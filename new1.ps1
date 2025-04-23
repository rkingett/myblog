#Requires -Version 5.1

<#
.SYNOPSIS
A PowerShell script to manage an Eleventy blog project, including creating posts,
managing drafts, testing, and deploying.

.DESCRIPTION
This script provides a menu-driven interface for common Eleventy workflow tasks:
1. Draft a new post in a specific content category folder.
2. Create a new draft in a dedicated 'drafts' folder.
3. Move drafts to content folders and publish the website.
4. Test the Eleventy site locally.
5. Build and deploy the site using Git and Rclone.
6. Build and deploy the site using Rclone only (no Git).

The script handles user input, confirmations, file creation with YAML front matter,
directory scanning, and execution of external commands like git, npx, and rclone.

.NOTES
- Assumes the script is run from the root directory of the Eleventy project.
- Requires Git, Node.js (for npx), Eleventy (@11ty/eleventy), and Rclone to be installed and configured.
- The 'rclone delete' and 'rclone sync' commands use specific paths ($home/documents/myblog/DistSite and nfs:).
  Modify the $rcloneLocalPath and $rcloneRemotePath variables if needed.
- The script attempts to open files in the default text editor using 'Start-Process -Wait'.
  This might not wait correctly for all editors. If issues arise, consider specifying an editor,
  e.g., 'Start-Process notepad.exe $FilePath -Wait'.
- Error handling for external commands is basic. Check console output for detailed errors.
#>

# --- Configuration ---
$ProjectRoot = Get-Location
$ContentDirectoryName = "content"
$DraftsDirectoryName = "drafts"
$ExcludedContentDirs = @("feed", "feeds", "helper", "helpers") # Lowercase for case-insensitive comparison

# Rclone paths (MODIFY IF NEEDED)
$rcloneLocalPath = Join-Path $HOME "documents/myblog/DistSite"
$rcloneRemoteName = "nfs:" # Your configured rclone remote name

# Deployment Website URL (MODIFY IF NEEDED)
$deployedSiteUrl = "https://sightlessblog.nfshost.com"

# --- Helper Functions ---

# Function to get user confirmation (1=Yes, 2=No)
function Get-UserConfirmation {
    param(
        [Parameter(Mandatory=$true)]
        [string]$PromptMessage
    )
    while ($true) {
        $input = Read-Host "$PromptMessage (1 = Yes, 2 = No)"
        if ($input -eq '1') { return $true }
        if ($input -eq '2') { return $false }
        Write-Warning "Invalid input. Please enter 1 for Yes or 2 for No."
    }
}

# Function to present numbered choices and get validated user input
function Get-UserChoice {
    param(
        [Parameter(Mandatory=$true)]
        [string]$PromptMessage,
        [Parameter(Mandatory=$true)]
        [array]$Options
    )
    Write-Host $PromptMessage
    for ($i = 0; $i -lt $Options.Count; $i++) {
        Write-Host ("{0}. {1}" -f ($i + 1), $Options[$i])
    }

    while ($true) {
        $input = Read-Host "Enter your choice (number)"
        if ($input -match '^\d+$' -and [int]$input -ge 1 -and [int]$input -le $Options.Count) {
            return [int]$input
        }
        Write-Warning "Invalid input. Please enter a number between 1 and $($Options.Count)."
    }
}

# Function to select a directory, with confirmation and optional creation
function Select-Directory {
    param(
        [Parameter(Mandatory=$true)]
        [string]$ParentDirectoryPath,
        [Parameter(Mandatory=$true)]
        [array]$ExcludedFolders,
        [Parameter(Mandatory=$false)]
        [switch]$AllowNew = $false,
        [Parameter(Mandatory=$true)]
        [string]$ChoicePrompt
    )

    $selectedDirectoryPath = $null
    do {
        $confirmationMet = $false
        $availableDirs = Get-ChildItem -Path $ParentDirectoryPath -Directory | Where-Object { $ExcludedFolders -notcontains $_.Name.ToLower() } | Select-Object -ExpandProperty Name
        $options = @($availableDirs)
        if ($AllowNew) {
            $options += "Create a new directory"
        }

        if ($options.Count -eq 0 -and !$AllowNew) {
            Write-Error "No valid subdirectories found in '$ParentDirectoryPath' (excluding specified folders)."
            return $null
        }
        if ($options.Count -eq 0 -and $AllowNew) {
             Write-Host "No existing valid subdirectories found. Only option is to create a new one."
             # Force selection of 'Create New' conceptually
             $choiceIndex = 1 # Only one option presented below
             $options = @("Create a new directory") # Reset options for clarity
        } else {
             $choiceIndex = Get-UserChoice -PromptMessage $ChoicePrompt -Options $options
        }


        $chosenOption = $options[$choiceIndex - 1]

        if ($chosenOption -eq "Create a new directory") {
            $newDirName = ""
            while ([string]::IsNullOrWhiteSpace($newDirName)) {
                $newDirName = Read-Host "Enter the name for the new directory"
                # Basic validation for invalid characters
                if ($newDirName -match '[\\/:*?"<>|]') {
                    Write-Warning "Directory name contains invalid characters. Please avoid \ / : * ? "" < > |"
                    $newDirName = "" # Reset to loop again
                }
            }
            $targetPath = Join-Path -Path $ParentDirectoryPath -ChildPath $newDirName
            if (Test-Path $targetPath) {
                 Write-Warning "Directory '$newDirName' already exists."
                 # Loop again to re-select or re-try creation name
                 continue
            }

            if (Get-UserConfirmation "Confirm creating directory '$newDirName' inside '$ParentDirectoryPath'?") {
                try {
                    $null = New-Item -Path $targetPath -ItemType Directory -ErrorAction Stop
                    Write-Host "Directory '$newDirName' created successfully." -ForegroundColor Green
                    $selectedDirectoryPath = $targetPath
                    $confirmationMet = $true
                } catch {
                    Write-Error "Failed to create directory '$newDirName'. Error: $($_.Exception.Message)"
                    # Loop again
                    continue
                }
            } else {
                # User chose No on confirmation, loop back to show choices
                continue
            }
        } else {
            # User chose an existing directory
            $targetPath = Join-Path -Path $ParentDirectoryPath -ChildPath $chosenOption
            if (Get-UserConfirmation "Confirm using directory '$chosenOption'?") {
                $selectedDirectoryPath = $targetPath
                $confirmationMet = $true
            } else {
                 # User chose No on confirmation, loop back to show choices
                 continue
            }
        }

    } until ($confirmationMet)

    return $selectedDirectoryPath
}

# Function to create the Markdown file content
function Create-MarkdownContent {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Title,
        [Parameter(Mandatory=$true)]
        [string]$IsoDateTime,
        [Parameter(Mandatory=$true)]
        [array]$Tags
    )

    # Format tags for YAML array: ["tag1", "tag2"]
    $yamlTags = "[]" # Default for no tags
    if ($Tags.Count -gt 0) {
        $quotedTags = $Tags | ForEach-Object { "`"$_`"" }
        $yamlTags = "[" + ($quotedTags -join ", ") + "]"
    }

    # YAML Front Matter using a Here-String
    $frontMatter = @"
---
title: "$Title"
date: "$IsoDateTime"
tags: $yamlTags
---

Write your post content here...
"@
    return $frontMatter
}

# Function to run standard deployment commands (Eleventy build, Git, Rclone)
function Invoke-DeployCommands {
    param(
        [Parameter(Mandatory=$true)]
        [string]$LocalSitePath,
        [Parameter(Mandatory=$true)]
        [string]$RemotePath,
        [Parameter(Mandatory=$true)]
        [string]$SiteUrl
    )
    Write-Host "Starting deployment process..."
    try {
        Write-Host "Ensuring ssh-agent service is running..."
        Start-Service ssh-agent -ErrorAction SilentlyContinue # Might not be needed or fail gracefully

        Write-Host "Cleaning local distribution directory: $LocalSitePath"
        rclone delete $LocalSitePath --rmdirs -v --ErrorAction Stop

        Write-Host "Cleaning remote directory: $RemotePath"
        rclone delete $RemotePath --rmdirs -v --ErrorAction Stop

        Write-Host "Building Eleventy site..."
        npx @11ty/eleventy --quiet --ErrorAction Stop # Stop if build fails

        Write-Host "Adding changes to Git..."
        git add . --ErrorAction Stop

        Write-Host "Committing changes..."
        # Use a default commit message or prompt user? Using default for now.
        $commitMessage = "Added posts and updated posts (automated script)"
        git commit -am $commitMessage --ErrorAction Stop

        Write-Host "Pushing changes to Git remote..."
        git push --ErrorAction Stop

        Write-Host "Deployment successful!" -ForegroundColor Green
        Write-Host "Opening deployed site: $SiteUrl"
        Start-Process $SiteUrl

    } catch {
        Write-Error "Deployment failed at step '$($_.InvocationInfo.MyCommand)': $($_.Exception.Message)"
        Write-Warning "Check the console output for details. Opening project folder for troubleshooting."
        Invoke-Item $ProjectRoot
        # Consider pausing here or exiting differently if needed
        Read-Host "Press Enter to return to the main menu..."
    }
}

# Function to run deployment commands without Git (Eleventy build, Rclone sync)
function Invoke-DeployCommandsNoGit {
    param(
        [Parameter(Mandatory=$true)]
        [string]$LocalSitePath,
        [Parameter(Mandatory=$true)]
        [string]$RemotePath,
        [Parameter(Mandatory=$true)]
        [string]$SiteUrl
    )
     Write-Host "Starting deployment process (No Git)..."
    try {
        Write-Host "Ensuring ssh-agent service is running..."
        Start-Service ssh-agent -ErrorAction SilentlyContinue

        Write-Host "Cleaning local distribution directory: $LocalSitePath"
        rclone delete $LocalSitePath --rmdirs -v --ErrorAction Stop

        Write-Host "Cleaning remote directory: $RemotePath"
        rclone delete $RemotePath --rmdirs -v --ErrorAction Stop

        Write-Host "Building Eleventy site..."
        npx @11ty/eleventy --quiet --ErrorAction Stop # Stop if build fails

        Write-Host "Syncing local site to remote..."
        # Ensure ssh-agent is running again if needed for rclone auth via ssh
        Start-Service ssh-agent -ErrorAction SilentlyContinue
        rclone sync $LocalSitePath $RemotePath -v --ErrorAction Stop

        Write-Host "Deployment successful!" -ForegroundColor Green
        Write-Host "Opening deployed site: $SiteUrl"
        Start-Process $SiteUrl

    } catch {
        Write-Error "Deployment failed at step '$($_.InvocationInfo.MyCommand)': $($_.Exception.Message)"
        Write-Warning "Check the console output for details. Opening project folder for troubleshooting."
        Invoke-Item $ProjectRoot
        # Consider pausing here or exiting differently if needed
        Read-Host "Press Enter to return to the main menu..."
    }
}


# --- Main Script Logic ---

# Check if running in the project root (basic check for content dir)
$ContentDirectoryPath = Join-Path -Path $ProjectRoot -ChildPath $ContentDirectoryName
if (-not (Test-Path $ContentDirectoryPath -PathType Container)) {
    Write-Warning "Could not find the '$ContentDirectoryName' directory in the current location ($ProjectRoot)."
    Write-Warning "Please run this script from the root of your Eleventy project."
    Read-Host "Press Enter to exit."
    exit
}

# Main menu loop
while ($true) {
    Clear-Host
    Write-Host "---------------------------------"
    Write-Host " Eleventy Project Manager Menu   "
    Write-Host "---------------------------------"
    $mainMenuOptions = @(
        "Draft a new post in a category folder."
        "Make a new draft in the drafts folder."
        "Move my drafts to post categories and then publish my website."
        "Test Eleventy locally."
        "Build and deploy via Github."
        "Build and deploy without Github."
        "Exit"
    )
    $mainChoice = Get-UserChoice -PromptMessage "Select an action:" -Options $mainMenuOptions

    # --- Process Main Menu Choice ---
    switch ($mainChoice) {
        # 1. Draft a new post in a category folder
        1 {
            Write-Host "`n--- Choice 1: Draft New Post in Category ---"

            # Select destination directory within content folder
            $chosenContentDir = Select-Directory -ParentDirectoryPath $ContentDirectoryPath -ExcludedFolders $ExcludedContentDirs -AllowNew -ChoicePrompt "Select the category (directory) for the new post:"
            if (-not $chosenContentDir) {
                Write-Warning "Directory selection cancelled or failed. Returning to main menu."
                Read-Host "Press Enter to continue..."
                continue # Go back to main menu
            }

            # Get Title
            $postTitle = ""
            while ([string]::IsNullOrWhiteSpace($postTitle)) {
                $postTitle = Read-Host "Enter the post title"
            }

            # Get Tags
            $tagsString = Read-Host "Enter tags, separated by commas (e.g., tech, blog, update)"
            $tagsArray = $tagsString.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }

            # Generate Date/Time and Filename
            $currentDateTime = Get-Date
            $isoDateTime = $currentDateTime.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ") # ISO 8601 UTC
            $fileNameDate = $currentDateTime.ToString("yyyyMMdd")
            $newFilePath = Join-Path -Path $chosenContentDir -ChildPath "$($fileNameDate).md"

            # Check if file exists
            if (Test-Path $newFilePath) {
                Write-Warning "A file named '$($fileNameDate).md' already exists in '$chosenContentDir'."
                if (-not (Get-UserConfirmation "Overwrite existing file?")) {
                     Write-Warning "Operation cancelled. Returning to main menu."
                     Read-Host "Press Enter to continue..."
                     continue
                }
            }

            # Create Content
            $markdownContent = Create-MarkdownContent -Title $postTitle -IsoDateTime $isoDateTime -Tags $tagsArray

            # Write File
            try {
                Set-Content -Path $newFilePath -Value $markdownContent -Encoding UTF8 -ErrorAction Stop
                Write-Host "Successfully created post: $newFilePath" -ForegroundColor Green
            } catch {
                Write-Error "Failed to create file '$newFilePath'. Error: $($_.Exception.Message)"
                Read-Host "Press Enter to return to the main menu..."
                continue
            }

            # Ask to open file
            if (Get-UserConfirmation "Do you want to open the new file '$($fileNameDate).md' now?") {
                Write-Host "Opening file... Please save and close the editor when finished to continue."
                try {
                    # Attempt to use Start-Process -Wait with the default handler
                    Start-Process $newFilePath -Wait -ErrorAction Stop
                    Write-Host "Editor closed."

                    # Ask to build/deploy
                    if (Get-UserConfirmation "Do you want to build and deploy the website now (via Git)?") {
                        Invoke-DeployCommands -LocalSitePath $rcloneLocalPath -RemotePath $rcloneRemoteName -SiteUrl $deployedSiteUrl
                    } else {
                        Write-Host "Skipping deployment. Returning to main menu."
                        Read-Host "Press Enter to continue..."
                    }

                } catch {
                    Write-Error "Could not open '$newFilePath' or wait for editor. Error: $($_.Exception.Message)"
                    Write-Warning "Please open the file manually if needed."
                    Read-Host "Press Enter to return to the main menu..."
                }
            } else {
                # Don't open file, open project folder and close script
                Write-Host "Opening project folder '$ProjectRoot'..."
                Invoke-Item $ProjectRoot
                Write-Host "Exiting script."
                exit # Exit PowerShell as requested
            }
        } # End Choice 1

        # 2. Make a new draft in the drafts folder
        2 {
            Write-Host "`n--- Choice 2: Make New Draft ---"
            $DraftsDirectoryPath = Join-Path -Path $ProjectRoot -ChildPath $DraftsDirectoryName

            # Ensure drafts directory exists
            if (-not (Test-Path $DraftsDirectoryPath -PathType Container)) {
                Write-Host "'$DraftsDirectoryName' directory not found. Creating it..."
                try {
                    $null = New-Item -Path $DraftsDirectoryPath -ItemType Directory -ErrorAction Stop
                    Write-Host "'$DraftsDirectoryName' directory created." -ForegroundColor Green
                } catch {
                    Write-Error "Failed to create '$DraftsDirectoryName' directory. Error: $($_.Exception.Message)"
                    Read-Host "Press Enter to return to the main menu..."
                    continue
                }
            }

            # Get Title
            $draftTitle = ""
            while ([string]::IsNullOrWhiteSpace($draftTitle)) {
                $draftTitle = Read-Host "Enter the draft title"
            }

            # Get Tags
            $draftTagsString = Read-Host "Enter tags, separated by commas (e.g., draft, idea, todo)"
            $draftTagsArray = $draftTagsString.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }

            # Generate Date/Time and Filename
            $currentDateTime = Get-Date
            $isoDateTime = $currentDateTime.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ") # ISO 8601 UTC
            $fileNameDate = $currentDateTime.ToString("yyyyMMdd")
            $newDraftFilePath = Join-Path -Path $DraftsDirectoryPath -ChildPath "$($fileNameDate).md"

             # Check if file exists
            if (Test-Path $newDraftFilePath) {
                Write-Warning "A file named '$($fileNameDate).md' already exists in '$DraftsDirectoryPath'."
                if (-not (Get-UserConfirmation "Overwrite existing file?")) {
                     Write-Warning "Operation cancelled. Returning to main menu."
                     Read-Host "Press Enter to continue..."
                     continue
                }
            }

            # Create Content
            $markdownContent = Create-MarkdownContent -Title $draftTitle -IsoDateTime $isoDateTime -Tags $draftTagsArray

            # Write File
            try {
                Set-Content -Path $newDraftFilePath -Value $markdownContent -Encoding UTF8 -ErrorAction Stop
                Write-Host "Successfully created draft: $newDraftFilePath" -ForegroundColor Green
            } catch {
                Write-Error "Failed to create file '$newDraftFilePath'. Error: $($_.Exception.Message)"
                Read-Host "Press Enter to return to the main menu..."
                continue
            }

            # Ask to open file
            if (Get-UserConfirmation "Do you want to open the new draft file '$($fileNameDate).md' now?") {
                 Write-Host "Opening file... Please save and close the editor when finished to continue."
                try {
                    Start-Process $newDraftFilePath -Wait -ErrorAction Stop
                    Write-Host "Editor closed."

                    # Ask to move file
                    if (Get-UserConfirmation "Do you want to move this draft to a content category folder now?") {
                        $moveToDir = Select-Directory -ParentDirectoryPath $ContentDirectoryPath -ExcludedFolders $ExcludedContentDirs -AllowNew:$false -ChoicePrompt "Select the destination category for the draft:"
                        if ($moveToDir) {
                            $destinationPath = Join-Path $moveToDir $newDraftFilePath.Split('\')[-1] # Keep original filename
                             # Check if destination file exists
                            if (Test-Path $destinationPath) {
                                Write-Warning "A file with the same name already exists in '$moveToDir'."
                                if (Get-UserConfirmation "Overwrite existing file at destination?") {
                                     try {
                                        Move-Item -Path $newDraftFilePath -Destination $destinationPath -Force -ErrorAction Stop
                                        Write-Host "Draft moved successfully to $destinationPath" -ForegroundColor Green
                                    } catch {
                                        Write-Error "Failed to move draft. Error: $($_.Exception.Message)"
                                    }
                                } else {
                                    Write-Warning "Move cancelled. Draft remains in '$DraftsDirectoryName'."
                                    Invoke-Item $DraftsDirectoryPath # Open drafts folder
                                }
                            } else {
                                # Destination does not exist, proceed with move
                                try {
                                    Move-Item -Path $newDraftFilePath -Destination $destinationPath -ErrorAction Stop
                                    Write-Host "Draft moved successfully to $destinationPath" -ForegroundColor Green
                                } catch {
                                    Write-Error "Failed to move draft. Error: $($_.Exception.Message)"
                                }
                            }
                        } else {
                            Write-Warning "Move cancelled because no destination was selected. Draft remains in '$DraftsDirectoryName'."
                            Invoke-Item $DraftsDirectoryPath # Open drafts folder
                        }
                    } else {
                        Write-Host "Draft will remain in the '$DraftsDirectoryName' folder."
                        Invoke-Item $DraftsDirectoryPath # Open drafts folder for manual moving
                    }

                } catch {
                    Write-Error "Could not open '$newDraftFilePath' or wait for editor. Error: $($_.Exception.Message)"
                    Write-Warning "Please open the file manually if needed. Draft remains in '$DraftsDirectoryName'."
                    Invoke-Item $DraftsDirectoryPath # Open drafts folder
                }

                # Ask to return to main menu or exit
                if (Get-UserConfirmation "Return to the main menu?") {
                    continue # Loop back to the start of the while loop
                } else {
                    Write-Host "Exiting script."
                    exit
                }

            } else {
                 # Don't open file, open project folder and close script
                Write-Host "Opening project folder '$ProjectRoot'..."
                Invoke-Item $ProjectRoot
                Write-Host "Exiting script."
                exit # Exit PowerShell as requested
            }
        } # End Choice 2

        # 3. Move drafts to post categories and publish
        3 {
            Write-Host "`n--- Choice 3: Move Drafts and Publish ---"
            $DraftsDirectoryPath = Join-Path -Path $ProjectRoot -ChildPath $DraftsDirectoryName

            if (-not (Test-Path $DraftsDirectoryPath -PathType Container)) {
                Write-Warning "Drafts directory '$DraftsDirectoryName' not found. Nothing to move."
                Read-Host "Press Enter to return to the main menu..."
                continue
            }

            $draftFiles = Get-ChildItem -Path $DraftsDirectoryPath -Filter "*.md" -File
            if ($draftFiles.Count -eq 0) {
                Write-Warning "No Markdown files found in the drafts directory."
                Read-Host "Press Enter to return to the main menu..."
                continue
            }

            Write-Host "Found $($draftFiles.Count) draft(s) to move."

            # Get available destination directories ONCE
            $availableDestDirs = Get-ChildItem -Path $ContentDirectoryPath -Directory | Where-Object { $ExcludedContentDirs -notcontains $_.Name.ToLower() }
            $destDirNames = $availableDestDirs | Select-Object -ExpandProperty Name

            if ($destDirNames.Count -eq 0) {
                 Write-Error "No valid destination directories found in '$ContentDirectoryName' (excluding specified folders)."
                 Write-Warning "Cannot move drafts. Please create category folders first."
                 Read-Host "Press Enter to return to the main menu..."
                 continue
            }

            $movePlan = @{} # Hashtable to store [DraftFilePath] = DestinationPath

            # Determine destinations for all drafts first
            $cancelAll = $false
            foreach ($draftFile in $draftFiles) {
                Write-Host "`nProcessing draft: $($draftFile.Name)"
                $chosenDestDirInfo = $null
                do {
                    $destChoiceIndex = Get-UserChoice -PromptMessage "Select destination category for '$($draftFile.Name)':" -Options $destDirNames
                    $chosenDestName = $destDirNames[$destChoiceIndex - 1]
                    $chosenDestDirInfo = $availableDestDirs | Where-Object {$_.Name -eq $chosenDestName} | Select-Object -First 1

                    if (Get-UserConfirmation "Confirm moving '$($draftFile.Name)' to '$($chosenDestName)'?") {
                        $movePlan[$draftFile.FullName] = $chosenDestDirInfo.FullName
                        break # Confirmation received, move to next draft
                    } else {
                        # Confirmation denied, ask to re-select for this file or cancel all
                        if (-not (Get-UserConfirmation "Choose a different destination for this file? (No = Cancel entire operation)")) {
                            $cancelAll = $true
                            break # Break inner loop
                        }
                        # If Yes, the outer do..while loop continues for this file
                    }
                } while ($true) # Loop until confirmed or cancelled all

                if ($cancelAll) { break } # Break outer foreach loop
            } # End foreach draftFile

            if ($cancelAll) {
                Write-Warning "Operation cancelled by user. No drafts were moved."
                Read-Host "Press Enter to return to the main menu..."
                continue
            }

            # Execute the move plan
            Write-Host "`nExecuting move plan..."
            $moveSuccess = $true
            foreach ($draftPath in $movePlan.Keys) {
                $destFolderPath = $movePlan[$draftPath]
                $draftFileName = Split-Path $draftPath -Leaf
                $finalDestPath = Join-Path $destFolderPath $draftFileName

                Write-Host "Moving '$draftFileName' to '$destFolderPath'..."
                try {
                     # Check for overwrite
                     if (Test-Path $finalDestPath) {
                         Write-Warning "File '$draftFileName' already exists in '$destFolderPath'."
                         if (Get-UserConfirmation "Overwrite?") {
                             Move-Item -Path $draftPath -Destination $finalDestPath -Force -ErrorAction Stop
                             Write-Host "Moved (overwrite)." -ForegroundColor Green
                         } else {
                             Write-Warning "Skipped moving '$draftFileName' due to existing file."
                             # Decide if this counts as a failure? For now, just warn.
                         }
                     } else {
                         Move-Item -Path $draftPath -Destination $finalDestPath -ErrorAction Stop
                         Write-Host "Moved successfully." -ForegroundColor Green
                     }
                } catch {
                    Write-Error "Failed to move '$draftFileName'. Error: $($_.Exception.Message)"
                    $moveSuccess = $false
                    # Optionally break here or continue trying others
                }
            }

            if ($moveSuccess) {
                Write-Host "`nAll selected drafts moved successfully." -ForegroundColor Green
                Write-Host "Proceeding with website build and deployment..."
                Invoke-DeployCommands -LocalSitePath $rcloneLocalPath -RemotePath $rcloneRemoteName -SiteUrl $deployedSiteUrl
            } else {
                Write-Warning "`nSome drafts failed to move. Deployment cancelled."
                Read-Host "Press Enter to return to the main menu..."
            }
        } # End Choice 3

        # 4. Test Eleventy locally
        4 {
            Write-Host "`n--- Choice 4: Test Eleventy Locally ---"
            Write-Host "Starting local development server..."
            Write-Host "Access at: http://localhost:8080/ (usually)"
            Write-Host "Press CTRL+C in the new window/tab where Eleventy runs to stop the server."
            try {
                # Start browser first, then the blocking server command
                Start-Process "http://localhost:8080/"
                npx @11ty/eleventy --serve # This command will block until stopped
                # Code here might not be reached until server is stopped
                Write-Host "Eleventy server stopped."
            } catch {
                 Write-Error "Failed to start Eleventy server. Error: $($_.Exception.Message)"
                 Write-Warning "Is Node.js/npm/npx installed and in PATH? Is Eleventy installed (`npm install @11ty/eleventy`)?"
            }
            Read-Host "Press Enter to return to the main menu..."
        } # End Choice 4

        # 5. Build and deploy via Github
        5 {
            Write-Host "`n--- Choice 5: Build and Deploy via Github ---"
            if (Get-UserConfirmation "Confirm build and deploy using Git?") {
                Invoke-DeployCommands -LocalSitePath $rcloneLocalPath -RemotePath $rcloneRemoteName -SiteUrl $deployedSiteUrl
            } else {
                Write-Host "Deployment cancelled."
                Read-Host "Press Enter to return to the main menu..."
            }
        } # End Choice 5

        # 6. Build and deploy without Github
        6 {
             Write-Host "`n--- Choice 6: Build and Deploy without Github ---"
             if (Get-UserConfirmation "Confirm build and deploy WITHOUT Git?") {
                Invoke-DeployCommandsNoGit -LocalSitePath $rcloneLocalPath -RemotePath $rcloneRemoteName -SiteUrl $deployedSiteUrl
             } else {
                Write-Host "Deployment cancelled."
                Read-Host "Press Enter to return to the main menu..."
            }
        } # End Choice 6

        # 7. Exit
        7 {
            Write-Host "Exiting script."
            exit # Exit the script
        } # End Choice 7

        Default {
            # Should not happen with Get-UserChoice validation, but good practice
            Write-Warning "Invalid selection. Please try again."
            Read-Host "Press Enter to continue..."
        }
    } # End Switch

    # Pause at the end of an action before showing the menu again (unless exited)
    # Some actions have their own pauses or exit points.

} # End While True (Main Loop)