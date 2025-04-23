#Requires -Version 5.1

<#
.SYNOPSIS
Creates a new Markdown file with YAML front matter for an Eleventy project.
.DESCRIPTION
This script scans the current project directory for a 'content' folder.
It lists the subdirectories within 'content' (excluding 'feed', 'helper', 'helpers')
as potential locations for the new file, plus an option to create a new directory.
The user selects a location, provides a title, and the script generates an .md file.
The filename is the current date (YYYYMMDD.md).
The YAML front matter includes the user-provided title and the current date/time
in an ISO 8601 format compatible with Luxon's DateTime.fromISO.
.NOTES
Author: Assistant
Date:   (Will be set during execution)
Assumes the script is run from the root of the Eleventy project or a location
where a './content' directory can be found.
#>

# --- Configuration ---
$contentFolderName = "content"
$excludedDirs = @("feed", "helper", "helpers") # Directories to exclude from choices

# --- Script Start ---
Write-Host "Starting Eleventy Post Creator..." -ForegroundColor Cyan

# 1. Find the Content Directory
$projectRoot = $PSScriptRoot # Use script's directory if run as .ps1
if (-not $projectRoot) {
    $projectRoot = $PWD # Use current working directory if run interactively
}
$contentDir = Join-Path -Path $projectRoot -ChildPath $contentFolderName

if (-not (Test-Path -Path $contentDir -PathType Container)) {
    Write-Error "Error: Could not find the '$contentFolderName' directory at '$contentDir'. Please run this script from your project root."
    Exit 1 # Exit script if content directory isn't found
}

Write-Host "Found content directory: $contentDir"

# 2. Scan for Subdirectories and Prepare Choices
Write-Host "Scanning for available content subdirectories..."
try {
    $subDirs = Get-ChildItem -Path $contentDir -Directory -Exclude $excludedDirs -ErrorAction Stop | Sort-Object Name
}
catch {
    Write-Warning "Could not list subdirectories in '$contentDir'. Error: $($_.Exception.Message)"
    $subDirs = @() # Ensure $subDirs is an empty array if Get-ChildItem fails
}

$options = @{}
$counter = 1

Write-Host "`nAvailable Post Locations:" -ForegroundColor Yellow
if ($subDirs.Count -gt 0) {
    foreach ($dir in $subDirs) {
        Write-Host "  $counter. $($dir.Name)"
        $options[$counter] = $dir # Store the directory object
        $counter++
    }
} else {
    Write-Host "  No existing subdirectories found (excluding specified ones)."
}

$newDirOptionNumber = $counter
Write-Host "  $newDirOptionNumber. Create New Directory"
$options[$newDirOptionNumber] = "CREATE_NEW" # Special value for new directory

# 3. Get User Choice for Directory
$chosenDirInfo = $null
$finalDirPath = $null
$chosenOptionName = ""

do {
    $validChoice = $false
    $confirmationChoice = $null
    $dirChoiceInput = Read-Host "`nEnter the number for the desired post location (1-$newDirOptionNumber)"

    if ($dirChoiceInput -match '^\d+$' -and $options.ContainsKey([int]$dirChoiceInput)) {
        $chosenDirNumber = [int]$dirChoiceInput
        $chosenDirInfo = $options[$chosenDirNumber]

        if ($chosenDirInfo -eq "CREATE_NEW") {
            $chosenOptionName = "Create New Directory"
        } else {
            # It's a directory object
            $chosenOptionName = $chosenDirInfo.Name
            $finalDirPath = $chosenDirInfo.FullName # Pre-set path for existing dir
        }

        # 4. Confirm Choice
        Write-Host "`nYou selected: '$chosenOptionName'" -ForegroundColor Green
        while ($confirmationChoice -notin @('1', '2')) {
            $confirmationChoice = Read-Host "Confirm selection? (1 = Yes, 2 = Choose Again)"
            if ($confirmationChoice -eq '1') {
                $validChoice = $true
            } elseif ($confirmationChoice -eq '2') {
                Write-Host "Okay, let's choose again."
                # Loop will restart directory selection
            } else {
                Write-Warning "Invalid input. Please enter 1 or 2."
            }
        }
    } else {
        Write-Warning "Invalid input. Please enter a number between 1 and $newDirOptionNumber."
    }

} while (-not $validChoice)

# 5. Handle "Create New Directory" if selected
if ($chosenDirInfo -eq "CREATE_NEW") {
    $newDirName = ""
    while ([string]::IsNullOrWhiteSpace($newDirName)) {
        $newDirName = Read-Host "Enter the name for the new directory inside '$contentFolderName'"
        # Basic validation for invalid characters (optional but recommended)
        if ($newDirName -match '[\\/:*?"<>|]') {
            Write-Warning "Directory name contains invalid characters. Please avoid \ / : * ? "" < > |"
            $newDirName = "" # Reset to loop
        }
        # You could add more validation here (e.g., check if it conflicts with excluded names)
    }

    $finalDirPath = Join-Path -Path $contentDir -ChildPath $newDirName
    Write-Host "Attempting to create directory: $finalDirPath"
    try {
        if (-not (Test-Path -Path $finalDirPath)) {
            $null = New-Item -Path $finalDirPath -ItemType Directory -ErrorAction Stop
            Write-Host "Successfully created directory '$newDirName'." -ForegroundColor Green
        } else {
            Write-Warning "Directory '$finalDirPath' already exists. Using existing directory."
            # Check if it's actually a directory, not a file
            if (-not (Test-Path -Path $finalDirPath -PathType Container)) {
                 Write-Error "Error: '$finalDirPath' exists but is not a directory. Cannot proceed."
                 Exit 1
            }
        }
    } catch {
        Write-Error "Failed to create directory '$finalDirPath'. Error: $($_.Exception.Message)"
        Exit 1
    }
}

# At this point, $finalDirPath should hold the valid full path to the target directory

# 6. Get Post Title
$postTitle = ""
while ([string]::IsNullOrWhiteSpace($postTitle)) {
    $postTitle = Read-Host "`nEnter the title for your post"
    if ([string]::IsNullOrWhiteSpace($postTitle)) {
        Write-Warning "Title cannot be empty."
    }
}

# 7. Generate Date/Time and Filename
$currentDateTime = Get-Date
$isoDateTime = $currentDateTime.ToUniversalTime().ToString("o") # 'o' format: yyyy-MM-ddTHH:mm:ss.fffffffZ (UTC is common for consistency)
# Alternative: Local time with offset: $currentDateTime.ToString("yyyy-MM-ddTHH:mm:ss.fffzzz") # e.g., 2023-10-27T15:30:00.123+01:00
$fileNameDatePart = $currentDateTime.ToString("yyyyMMdd")
$fileName = "$($fileNameDatePart).md"
$fullFilePath = Join-Path -Path $finalDirPath -ChildPath $fileName

Write-Host "Generated Filename: $fileName"
Write-Host "Generated ISO DateTime: $isoDateTime"

# 8. Check if file already exists
if (Test-Path -Path $fullFilePath) {
    Write-Error "Error: A file named '$fileName' already exists in '$finalDirPath'. Please create the post manually or try again later."
    Exit 1
}

# 9. Create YAML Front Matter and Content
# Using double quotes within the here-string allows variable expansion.
# Escape any literal $ signs if needed with backtick `$
$yamlFrontMatter = @"
---
title: "$($postTitle)"
date: "$($isoDateTime)"
---

"@ # Important: Ensure a blank line follows the closing '---'

$fileContent = $yamlFrontMatter + "`nWrite your content here..." # Add placeholder text

# 10. Write the File
Write-Host "Creating file at: $fullFilePath"
try {
    Set-Content -Path $fullFilePath -Value $fileContent -Encoding UTF8 -ErrorAction Stop
    Write-Host "`nSuccessfully created post!" -ForegroundColor Green
    Write-Host "File Path: $fullFilePath"
} catch {
    Write-Error "Failed to write file '$fullFilePath'. Error: $($_.Exception.Message)"
    Exit 1
}

Write-Host "`nScript finished." -ForegroundColor Cyan