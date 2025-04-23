#Requires -Version 5.1
<#
.SYNOPSIS
Automates common Eleventy blog tasks like creating posts, moving drafts, and deploying.

.DESCRIPTION
Presents a menu of choices to the user:
1. Draft a new post in a specific content category folder.
2. Create a new draft in the 'drafts' folder.
3. Move existing drafts to content folders and publish.
4. Test the Eleventy site locally.
5. Build and deploy the site via GitHub.
6. Build and deploy the site without GitHub (direct sync).

The script handles finding content directories, creating files with YAML front matter,
user input for titles and tags, confirmation prompts, opening files, and running
build/deploy commands.

.NOTES
- Assumes the script is run from the root directory of the Eleventy project.
- Requires Node.js, npm/npx, Eleventy (@11ty/eleventy), Git, and rclone to be installed and configured.
- The deployment commands (rclone paths, git commands) might need adjustment based on your specific setup.
- Assumes your default text editor for .md files correctly handles the -Wait parameter for Start-Process.
- The script uses specific folder names like 'content', 'drafts', 'feed', 'feeds', 'helper', 'helpers'. Adjust if needed.
- Ensure the ssh-agent service can be started by the script runner.
#>

# --- Configuration ---
# Adjust these paths and names if your project structure is different
$ProjectRoot = (Get-Location).Path
$ContentFolderName = "content"
$DraftsFolderName = "drafts"
$ExcludedContentFolders = @("feed", "feeds", "helper", "helpers") # Folders to exclude from category choices
$RcloneDistPath = Join-Path $HOME "documents/myblog/DistSite" # Local path for rclone source/delete
$RcloneRemoteName = "nfs:" # Name of your rclone remote
$DeployGitCommitMessage = "Added posts and updated posts"
$DeploySiteUrl = "https://sightlessblog.nfshost.com" # URL to open after deployment

# --- Helper Functions ---

# Function to get user confirmation (1=Yes, 2=No)
function Get-UserConfirmation($PromptMessage) {
    while ($true) {
        Write-Host "$PromptMessage" -ForegroundColor Yellow
        Write-Host "1: Yes"
        Write-Host "2: No"
        $confirmation = Read-Host "Enter your choice (1 or 2)"
        if ($confirmation -eq '1') {
            return $true
        } elseif ($confirmation -eq '2') {
            return $false
        } else {
            Write-Warning "Invalid input. Please enter 1 for Yes or 2 for No."
        }
    }
}

# Function to present numbered choices and get validated input
function Get-NumberedChoice($PromptMessage, $Choices) {
    if (-not $Choices -or $Choices.Count -eq 0) {
        Write-Error "No choices provided to Get-NumberedChoice function."
        return $null
    }

    while ($true) {
        Write-Host $PromptMessage -ForegroundColor Cyan
        for ($i = 0; $i -lt $Choices.Count; $i++) {
            Write-Host "$($i + 1): $($Choices[$i])"
        }
        $userInput = Read-Host "Enter the number of your choice (1-$($Choices.Count))"

        if ($userInput -match '^\d+$' -and [int]$userInput -ge 1 -and [int]$userInput -le $Choices.Count) {
            return [int]$userInput # Return the selected number (1-based index)
        } else {
            Write-Warning "Invalid input. Please enter a number between 1 and $($Choices.Count)."
        }
    }
}

# Function to get content directories, excluding specified ones
function Get-ContentSubdirectories($ContentPath, $Exclusions) {
    if (-not (Test-Path -Path $ContentPath -PathType Container)) {
        Write-Warning "Content directory not found at '$ContentPath'."
        return @()
    }
    Get-ChildItem -Path $ContentPath -Directory | Where-Object { $_.Name -notin $Exclusions }
}

# Function to format tags into YAML list string
function Format-TagsToYaml($TagsInput) {
    if ([string]::IsNullOrWhiteSpace($TagsInput)) {
        return "[]" # Return empty YAML array if no tags provided
    }
    # Split by comma, trim whitespace from each tag, filter out empty strings, enclose in quotes
    $formattedTags = $TagsInput.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object { "`"$_`"" }
    return "[$($formattedTags -join ', ')]" # Join with comma+space and wrap in brackets
}

# Function to create the markdown file content
function Create-MarkdownContent($Title, $TagsYaml, $IsoDateTime) {
    $yamlFrontMatter = @"
---
title: "$Title"
date: "$IsoDateTime"
tags: $TagsYaml
---

Write your post content here...
"@
    return $yamlFrontMatter
}

# Function to run deployment steps
function Run-DeploymentSteps($UseGit) {
    Write-Host "Starting deployment process..." -ForegroundColor Green
    try {
        # Ensure ssh-agent is running (often needed for git push with SSH keys)
        Write-Host "Ensuring ssh-agent service is started..."
        Start-Service ssh-agent -ErrorAction SilentlyContinue # Continue if already running or fails slightly

        # Clean destinations
        Write-Host "Cleaning local distribution directory: $RcloneDistPath"
        rclone delete $RcloneDistPath --rmdirs -v --ErrorAction Stop
        Write-Host "Cleaning remote destination: $RcloneRemoteName"
        rclone delete $RcloneRemoteName --rmdirs -v --ErrorAction Stop

        # Build Eleventy site
        Write-Host "Building Eleventy site..."
        # Use Invoke-Expression to ensure npx runs correctly in the current shell context
        Invoke-Expression "npx @11ty/eleventy --quiet"
        if ($LASTEXITCODE -ne 0) {
            throw "Eleventy build failed. Exit code: $LASTEXITCODE"
        }
        Write-Host "Eleventy build successful." -ForegroundColor Green

        if ($UseGit) {
            # Git steps
            Write-Host "Adding changes to Git..."
            git add . -A # Use -A to stage deletions as well
            Write-Host "Committing changes..."
            git commit -am $DeployGitCommitMessage
            Write-Host "Pushing changes to remote repository..."
            git push
            Write-Host "Git push successful." -ForegroundColor Green

            # Optionally open the deployed site URL
            if (-not [string]::IsNullOrWhiteSpace($DeploySiteUrl)) {
                Write-Host "Opening deployed site: $DeploySiteUrl"
                Start-Process $DeploySiteUrl
            }
        } else {
            # Direct sync without Git involvement for deployment artifact
             Write-Host "Syncing built site to remote destination..."
             # Ensure ssh-agent is running again if needed for rclone backend
             Start-Service ssh-agent -ErrorAction SilentlyContinue
             rclone sync $RcloneDistPath $RcloneRemoteName -v --ErrorAction Stop
             Write-Host "Rclone sync successful." -ForegroundColor Green
        }

        Write-Host "Deployment process completed successfully." -ForegroundColor Green
        return $true # Indicate success
    } catch {
        Write-Error "Deployment failed: $($_.Exception.Message)"
        Write-Warning "Opening project folder for troubleshooting: $ProjectRoot"
        Invoke-Item $ProjectRoot
        return $false # Indicate failure
    }
}

# --- Main Script Logic ---

$ContentPath = Join-Path $ProjectRoot $ContentFolderName
$DraftsPath = Join-Path $ProjectRoot $DraftsFolderName

# Main Menu Loop
while ($true) {
    Clear-Host
    Write-Host "---------------------------------" -ForegroundColor Magenta
    Write-Host " Eleventy Blog Helper Script " -ForegroundColor Magenta
    Write-Host "---------------------------------" -ForegroundColor Magenta
    Write-Host "Select an action:"
    Write-Host "1: Draft a new post in a category folder"
    Write-Host "2: Make a new draft in the drafts folder"
    Write-Host "3: Move drafts to post categories and publish"
    Write-Host "4: Test Eleventy locally"
    Write-Host "5: Build and deploy via GitHub"
    Write-Host "6: Build and deploy without GitHub (direct sync)"
    Write-Host "7: Exit"

    $mainChoice = Read-Host "Enter your choice (1-7)"

    switch ($mainChoice) {
        # --- Choice 1: Draft a new post in a category folder ---
        '1' {
            Write-Host "`n--- Draft a new post in a category folder ---" -ForegroundColor Green

            # Select Output Directory
            $chosenDirectoryPath = $null
            while ($true) { # Loop for directory selection and confirmation
                $availableDirs = Get-ContentSubdirectories -ContentPath $ContentPath -Exclusions $ExcludedContentFolders
                $dirNames = $availableDirs | ForEach-Object { $_.Name }
                $choices = @($dirNames) + "Create a new directory" # Add create new option
                $choicePrompt = "`nChoose the category (directory) for the new post:"

                $dirChoiceIndex = Get-NumberedChoice -PromptMessage $choicePrompt -Choices $choices
                $chosenItem = $choices[$dirChoiceIndex - 1]

                if ($chosenItem -eq "Create a new directory") {
                    # Create new directory
                    $newDirName = ""
                    while ([string]::IsNullOrWhiteSpace($newDirName) -or $newDirName -match '[\\/:\*\?"<>\|]' -or (Test-Path (Join-Path $ContentPath $newDirName))) {
                         $newDirName = Read-Host "Enter the name for the new directory (cannot contain invalid characters or already exist)"
                         if ([string]::IsNullOrWhiteSpace($newDirName)) { Write-Warning "Directory name cannot be empty."; continue }
                         if ($newDirName -match '[\\/:\*\?"<>\|]') { Write-Warning "Directory name contains invalid characters."; continue }
                         if (Test-Path (Join-Path $ContentPath $newDirName)) { Write-Warning "Directory '$newDirName' already exists."; continue }
                    }
                    try {
                        $chosenDirectoryPath = New-Item -Path $ContentPath -Name $newDirName -ItemType Directory -Force -ErrorAction Stop
                        Write-Host "Created directory: $($chosenDirectoryPath.FullName)" -ForegroundColor Green
                    } catch {
                        Write-Error "Failed to create directory '$newDirName'. Error: $($_.Exception.Message)"
                        # Go back to directory selection
                        continue
                    }
                } else {
                    # Existing directory chosen
                    $chosenDirectoryPath = $availableDirs[$dirChoiceIndex - 1].FullName
                }

                Write-Host "`nYou have selected: '$($chosenDirectoryPath | Split-Path -Leaf)'"
                if (Get-UserConfirmation -PromptMessage "Confirm this directory choice?") {
                    break # Exit the directory selection loop
                }
                # If No (returns false), the loop continues and choices are shown again
            } # End directory selection loop

            # Get Post Details
            $postTitle = Read-Host "Enter the post title"
            while ([string]::IsNullOrWhiteSpace($postTitle)) {
                 Write-Warning "Title cannot be empty."
                 $postTitle = Read-Host "Enter the post title"
            }
            $tagsInput = Read-Host "Enter tags, separated by commas (e.g., tech, blog, eleventy)"
            $tagsYaml = Format-TagsToYaml $tagsInput

            # Generate Date/Time and Filename
            $currentDateTime = Get-Date
            $isoDateTime = $currentDateTime.ToUniversalTime().ToString("o") # ISO 8601 Round-trip format (UTC)
            $fileNameDatePart = $currentDateTime.ToString("yyyyMMdd")
            $newFileName = "$($fileNameDatePart).md"
            $newFilePath = Join-Path $chosenDirectoryPath $newFileName

             # Handle potential filename collision (optional but good practice)
             $counter = 1
             while (Test-Path $newFilePath) {
                 $newFileName = "$($fileNameDatePart)_$($counter).md"
                 $newFilePath = Join-Path $chosenDirectoryPath $newFileName
                 $counter++
             }

            # Create File Content
            $fileContent = Create-MarkdownContent -Title $postTitle -TagsYaml $tagsYaml -IsoDateTime $isoDateTime

            # Write the file
            try {
                Set-Content -Path $newFilePath -Value $fileContent -Encoding UTF8 -ErrorAction Stop
                Write-Host "`nSuccessfully created post:" -ForegroundColor Green
                Write-Host $newFilePath
            } catch {
                Write-Error "Failed to create file '$newFilePath'. Error: $($_.Exception.Message)"
                Read-Host "Press Enter to return to the main menu."
                continue # Go back to main menu
            }

            # Ask to open the file
            if (Get-UserConfirmation -PromptMessage "`nDo you want to open the new file '$newFileName' in your default editor?") {
                Write-Host "Opening file... Please save and close the editor when you are finished editing."
                try {
                    # Use -Wait to pause the script until the editor is closed
                    Start-Process -FilePath $newFilePath -Wait -ErrorAction Stop
                    Write-Host "Editor closed."

                    # Ask to Build and Deploy
                    if (Get-UserConfirmation -PromptMessage "`nDo you want to build and deploy the website now (using GitHub workflow)?") {
                       Run-DeploymentSteps -UseGit $true
                    } else {
                        Write-Host "Okay, skipping deployment. You can deploy later using option 5."
                    }
                } catch {
                    Write-Error "Failed to open file '$newFilePath' or wait for editor. Error: $($_.Exception.Message)"
                    Write-Warning "Please manually edit the file if needed."
                    # Still ask about deployment
                    if (Get-UserConfirmation -PromptMessage "`nDo you want to build and deploy the website now (using GitHub workflow), assuming you've finished editing?") {
                       Run-DeploymentSteps -UseGit $true
                    } else {
                        Write-Host "Okay, skipping deployment."
                    }
                }
            } else {
                # Didn't open the file
                Write-Host "Okay, file not opened. Opening the project folder."
                Invoke-Item $ProjectRoot
                Write-Host "Exiting script."
                exit # Exit PowerShell as requested
            }
            Read-Host "`nPress Enter to return to the main menu."
        } # End Choice 1

        # --- Choice 2: Make a new draft in the drafts folder ---
        '2' {
             Write-Host "`n--- Make a new draft in the drafts folder ---" -ForegroundColor Green

            # Ensure Drafts Directory Exists
            if (-not (Test-Path -Path $DraftsPath -PathType Container)) {
                Write-Host "Drafts directory '$DraftsFolderName' not found. Creating it..."
                try {
                    New-Item -Path $ProjectRoot -Name $DraftsFolderName -ItemType Directory -Force -ErrorAction Stop | Out-Null
                    Write-Host "Drafts directory created successfully." -ForegroundColor Green
                } catch {
                    Write-Error "Failed to create drafts directory '$DraftsPath'. Error: $($_.Exception.Message)"
                    Read-Host "Press Enter to return to the main menu."
                    continue # Go back to main menu
                }
            }

            # Get Post Details (same as Choice 1)
            $postTitle = Read-Host "Enter the draft title"
             while ([string]::IsNullOrWhiteSpace($postTitle)) {
                 Write-Warning "Title cannot be empty."
                 $postTitle = Read-Host "Enter the draft title"
            }
            $tagsInput = Read-Host "Enter tags, separated by commas (e.g., draft, idea, todo)"
            $tagsYaml = Format-TagsToYaml $tagsInput

            # Generate Date/Time and Filename (same as Choice 1)
            $currentDateTime = Get-Date
            $isoDateTime = $currentDateTime.ToUniversalTime().ToString("o") # ISO 8601 Round-trip format (UTC)
            $fileNameDatePart = $currentDateTime.ToString("yyyyMMdd")
            $newFileName = "$($fileNameDatePart)_draft.md" # Add _draft suffix for clarity
            $newFilePath = Join-Path $DraftsPath $newFileName

             # Handle potential filename collision
             $counter = 1
             while (Test-Path $newFilePath) {
                 $newFileName = "$($fileNameDatePart)_draft_$($counter).md"
                 $newFilePath = Join-Path $DraftsPath $newFileName
                 $counter++
             }

            # Create File Content
            $fileContent = Create-MarkdownContent -Title $postTitle -TagsYaml $tagsYaml -IsoDateTime $isoDateTime

            # Write the file
            try {
                Set-Content -Path $newFilePath -Value $fileContent -Encoding UTF8 -ErrorAction Stop
                Write-Host "`nSuccessfully created draft:" -ForegroundColor Green
                Write-Host $newFilePath
            } catch {
                Write-Error "Failed to create file '$newFilePath'. Error: $($_.Exception.Message)"
                Read-Host "Press Enter to return to the main menu."
                continue # Go back to main menu
            }

             # Ask to open the file
            if (Get-UserConfirmation -PromptMessage "`nDo you want to open the new draft '$newFileName' in your default editor?") {
                Write-Host "Opening file... Please save and close the editor when you are finished editing."
                try {
                    # Use -Wait to pause the script until the editor is closed
                    Start-Process -FilePath $newFilePath -Wait -ErrorAction Stop
                    Write-Host "Editor closed."

                     # Ask to Move the file
                     if (Get-UserConfirmation -PromptMessage "`nDo you want to move this draft to a content folder now?") {
                         # Select Destination Directory
                         $moveDestinationPath = $null
                         while ($true) { # Loop for directory selection and confirmation
                             $availableDirs = Get-ContentSubdirectories -ContentPath $ContentPath -Exclusions $ExcludedContentFolders
                             if ($availableDirs.Count -eq 0) {
                                 Write-Warning "No suitable content directories found to move the draft to."
                                 $moveDestinationPath = $null # Ensure it's null if no dirs
                                 break # Exit selection loop
                             }
                             $dirNames = $availableDirs | ForEach-Object { $_.Name }
                             # Do NOT add "Create New" here, just moving to existing
                             $choicePrompt = "`nChoose the destination category (directory) for the draft:"

                             $dirChoiceIndex = Get-NumberedChoice -PromptMessage $choicePrompt -Choices $dirNames
                             $chosenDirInfo = $availableDirs[$dirChoiceIndex - 1]

                             Write-Host "`nYou have selected: '$($chosenDirInfo.Name)'"
                             if (Get-UserConfirmation -PromptMessage "Confirm this destination directory?") {
                                 $moveDestinationPath = $chosenDirInfo.FullName
                                 break # Exit the directory selection loop
                             }
                             # If No (returns false), the loop continues and choices are shown again
                         } # End destination directory selection loop

                         # Execute the move if a destination was chosen
                         if ($moveDestinationPath) {
                             $finalFilePath = Join-Path $moveDestinationPath $newFileName
                              # Handle potential filename collision in destination
                             $counter = 1
                             while (Test-Path $finalFilePath) {
                                 $baseName = [System.IO.Path]::GetFileNameWithoutExtension($newFileName)
                                 $extension = [System.IO.Path]::GetExtension($newFileName)
                                 $finalFilePath = Join-Path $moveDestinationPath "$($baseName)_$($counter)$($extension)"
                                 $counter++
                             }

                             try {
                                 Move-Item -Path $newFilePath -Destination $finalFilePath -Force -ErrorAction Stop
                                 Write-Host "Successfully moved '$newFileName' to '$($moveDestinationPath | Split-Path -Leaf)'" -ForegroundColor Green
                                 $newFilePath = $finalFilePath # Update path for consistency
                             } catch {
                                 Write-Error "Failed to move file. Error: $($_.Exception.Message)"
                                 Write-Warning "The draft remains in the '$DraftsFolderName' folder."
                             }
                         } else {
                              Write-Host "Move cancelled or no destination available."
                         }
                     } else {
                         # User chose not to move the file
                         Write-Host "Okay, the draft remains in the '$DraftsFolderName' folder."
                         Write-Host "Opening the drafts folder for manual moving if needed."
                         Invoke-Item $DraftsPath
                     }

                } catch {
                    Write-Error "Failed to open file '$newFilePath' or wait for editor. Error: $($_.Exception.Message)"
                    Write-Warning "Please manually edit the file if needed. The draft remains in '$DraftsFolderName'."
                    # Skip move prompt if editor failed
                    Write-Host "Opening the drafts folder."
                    Invoke-Item $DraftsPath
                }

                # Ask about main menu or exit
                if (Get-UserConfirmation -PromptMessage "`nReturn to the main menu?") {
                    continue # Go to start of the while loop
                } else {
                    Write-Host "Exiting script."
                    exit
                }

            } else {
                # Didn't open the file
                Write-Host "Okay, file not opened. Opening the project folder."
                Invoke-Item $ProjectRoot
                Write-Host "Exiting script."
                exit # Exit PowerShell as requested
            }
        } # End Choice 2

        # --- Choice 3: Move drafts to post categories and publish ---
        '3' {
            Write-Host "`n--- Move drafts to post categories and publish ---" -ForegroundColor Green

            # Check if Drafts folder exists and has files
             if (-not (Test-Path -Path $DraftsPath -PathType Container)) {
                Write-Warning "Drafts directory '$DraftsFolderName' not found. Nothing to move."
                Read-Host "Press Enter to return to the main menu."
                continue
            }
            $draftFiles = Get-ChildItem -Path $DraftsPath -Filter *.md -File
             if ($draftFiles.Count -eq 0) {
                 Write-Warning "No markdown files found in the drafts folder '$DraftsFolderName'."
                 Read-Host "Press Enter to return to the main menu."
                 continue
             }

             Write-Host "Found $($draftFiles.Count) draft(s) to process."

             # Get available destination directories
             $availableDirs = Get-ContentSubdirectories -ContentPath $ContentPath -Exclusions $ExcludedContentFolders
             if ($availableDirs.Count -eq 0) {
                 Write-Warning "No suitable content directories found to move drafts into."
                 Write-Warning "Please create category folders inside '$ContentFolderName' first."
                 Read-Host "Press Enter to return to the main menu."
                 continue
             }
             $dirNames = $availableDirs | ForEach-Object { $_.Name }
             $choicePrompt = "Choose the destination category (directory):"

             # Plan the moves
             $movePlan = @() # Array to store planned moves {SourcePath, DestinationPath, OriginalFileName}

             foreach ($draftFile in $draftFiles) {
                 Write-Host "`nProcessing draft: $($draftFile.Name)" -ForegroundColor Yellow

                 $destinationDirInfo = $null
                 while ($true) { # Loop for directory selection and confirmation for this file
                     $dirChoiceIndex = Get-NumberedChoice -PromptMessage $choicePrompt -Choices $dirNames
                     $chosenDirInfo = $availableDirs[$dirChoiceIndex - 1]

                     Write-Host "`nYou have selected destination: '$($chosenDirInfo.Name)' for file '$($draftFile.Name)'"
                     if (Get-UserConfirmation -PromptMessage "Confirm this destination?") {
                         $destinationDirInfo = $chosenDirInfo
                         break # Confirmed for this file
                     }
                     # If No, loop again to re-select for this file
                 }

                 # Add to move plan
                 $movePlan += [PSCustomObject]@{
                     SourcePath       = $draftFile.FullName
                     DestinationPath  = $destinationDirInfo.FullName
                     OriginalFileName = $draftFile.Name
                 }
             } # End foreach draft file

             # Optional: Confirm all planned moves
             Write-Host "`n--- Move Plan ---" -ForegroundColor Cyan
             $movePlan | ForEach-Object {
                 Write-Host "$($_.OriginalFileName) => $(Split-Path $_.DestinationPath -Leaf)"
             }
             if (-not (Get-UserConfirmation -PromptMessage "`nProceed with moving these files?")) {
                 Write-Host "Move operation cancelled."
                 Read-Host "Press Enter to return to the main menu."
                 continue
             }

             # Execute the moves
             Write-Host "`nMoving files..."
             $moveSuccess = $true
             foreach ($move in $movePlan) {
                 $targetFilePath = Join-Path $move.DestinationPath $move.OriginalFileName
                 # Handle potential filename collision in destination
                 $counter = 1
                 while (Test-Path $targetFilePath) {
                     $baseName = [System.IO.Path]::GetFileNameWithoutExtension($move.OriginalFileName)
                     $extension = [System.IO.Path]::GetExtension($move.OriginalFileName)
                     $targetFilePath = Join-Path $move.DestinationPath "$($baseName)_$($counter)$($extension)"
                     $counter++
                 }

                 try {
                     Move-Item -Path $move.SourcePath -Destination $targetFilePath -Force -ErrorAction Stop
                     Write-Host "Moved '$($move.OriginalFileName)' to '$(Split-Path $move.DestinationPath -Leaf)'" -ForegroundColor Green
                 } catch {
                     Write-Error "Failed to move '$($move.OriginalFileName)'. Error: $($_.Exception.Message)"
                     $moveSuccess = $false
                     # Decide whether to continue with other files or stop? Let's continue.
                 }
             }

             if (-not $moveSuccess) {
                 Write-Warning "Some files failed to move. Please check the errors above."
                 # Don't automatically deploy if moves failed
                 Read-Host "Press Enter to return to the main menu."
                 continue
             }

             Write-Host "`nAll selected drafts moved successfully." -ForegroundColor Green

             # Proceed to Deploy
             Write-Host "`nProceeding to build and deploy the website (using GitHub workflow)..."
             Run-DeploymentSteps -UseGit $true

             Read-Host "Press Enter to return to the main menu."

        } # End Choice 3

        # --- Choice 4: Test Eleventy locally ---
        '4' {
            Write-Host "`n--- Test Eleventy locally ---" -ForegroundColor Green
            Write-Host "Starting local development server..."
            Write-Host "Access the site at http://localhost:8080/ (usually)"
            Write-Host "Press CTRL+C in the terminal window where Eleventy is running to stop the server."
            try {
                # Open the browser first
                Start-Process "http://localhost:8080/" -ErrorAction SilentlyContinue
                # Then run the serve command, which will block this script until stopped
                Invoke-Expression "npx @11ty/eleventy --serve"
                 # Code here will run only after npx command is stopped (Ctrl+C)
                 Write-Host "`nEleventy serve process stopped."
            } catch {
                 Write-Error "Failed to start Eleventy serve process. Is Node.js/npm/Eleventy installed and in PATH?"
                 Write-Error $_.Exception.Message
            }
            Read-Host "Press Enter to return to the main menu."
        } # End Choice 4

        # --- Choice 5: Build and deploy via GitHub ---
        '5' {
            Write-Host "`n--- Build and deploy via GitHub ---" -ForegroundColor Green
            if (Get-UserConfirmation -PromptMessage "Are you sure you want to build and deploy using the GitHub workflow?") {
                Run-DeploymentSteps -UseGit $true
            } else {
                Write-Host "Deployment cancelled."
            }
            Read-Host "Press Enter to return to the main menu."
        } # End Choice 5

        # --- Choice 6: Build and deploy without GitHub ---
        '6' {
             Write-Host "`n--- Build and deploy without GitHub (direct sync) ---" -ForegroundColor Green
             if (Get-UserConfirmation -PromptMessage "Are you sure you want to build and deploy using direct rclone sync (no git push)?") {
                 Run-DeploymentSteps -UseGit $false
             } else {
                 Write-Host "Deployment cancelled."
             }
             Read-Host "Press Enter to return to the main menu."
        } # End Choice 6

        # --- Choice 7: Exit ---
        '7' {
            Write-Host "Exiting script. Goodbye!"
            break # Exit the main while loop
        }

        # --- Default: Invalid Choice ---
        default {
            Write-Warning "Invalid choice. Please select a number from 1 to 7."
            Read-Host "Press Enter to continue."
        }
    } # End Switch
} # End While Loop

# --- Script End ---