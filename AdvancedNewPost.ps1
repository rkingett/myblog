#Requires -Version 5.1

<#
.SYNOPSIS
Creates a new Markdown file with YAML front matter for Eleventy projects.

.DESCRIPTION
This script scans the project for a 'content' directory (configurable).
It lists the subdirectories within 'content' (excluding 'feed', 'helper', 'helpers')
as potential locations for the new file. Users can select an existing directory
or choose to create a new one.
The script prompts for a title and tags, then generates an .md file named
with the current date (YYYYMMDD.md) in the chosen location.
The YAML front matter includes the title, current date/time in ISO 8601 format,
and the provided tags formatted as a YAML list.
Finally, it opens the newly created file in the default text editor.

.NOTES
Author: Me
Date:   (Get-Date).ToString('yyyy-MM-dd')
Ensure you run this script from within your Eleventy project directory or one of its subdirectories.
The script searches upwards for the content directory.
ISO 8601 format used: yyyy-MM-ddTHH:mm:ss.fffzzz (compatible with Luxon's DateTime.fromISO)
#>

# --- Configuration ---
$contentDirectoryName = "content" # The name of your main content directory (e.g., "src", "posts", "content")
$excludedDirs = @("feed", "helper", "helpers") # Directories inside $contentDirectoryName to exclude from choices

# --- Script Start ---
Clear-Host
Write-Host "Starting Eleventy Post Creator..." -ForegroundColor Cyan

# --- Find Project Root and Content Directory ---
$currentPath = $PWD.Path
$contentDirPath = $null

# Search upwards for the content directory
$searchPath = $currentPath
while ($searchPath -ne $null -and $searchPath -ne (Split-Path $searchPath -Parent)) {
    $potentialContentPath = Join-Path -Path $searchPath -ChildPath $contentDirectoryName
    if (Test-Path $potentialContentPath -PathType Container) {
        $contentDirPath = $potentialContentPath
        Write-Host "Found content directory at: $contentDirPath"
        break
    }
    $searchPath = Split-Path $searchPath -Parent
}

if (-not $contentDirPath) {
    Write-Error "Could not find a '$contentDirectoryName' directory searching up from '$currentPath'. Please run the script from within your project."
    Exit 1
}

# --- Directory Selection Loop ---
$chosenDirPath = $null
$chosenDirName = $null
$confirmed = $false

do {
    # --- Get Available Directories ---
    try {
        $availableDirs = Get-ChildItem -Path $contentDirPath -Directory -ErrorAction Stop | Where-Object { $_.Name -notin $excludedDirs }
    } catch {
        Write-Error "Error accessing directories within '$contentDirPath': $($_.Exception.Message)"
        Exit 1
    }

    # --- Display Choices ---
    Clear-Host
    Write-Host "Available Content Directories (inside '$contentDirectoryName'):" -ForegroundColor Yellow
    $i = 1
    $dirMap = @{} # Map choice number to directory object
    foreach ($dir in $availableDirs) {
        Write-Host "[$i] $($dir.Name)"
        $dirMap[$i] = $dir
        $i++
    }
    $newDirOption = $i
    Write-Host "[$newDirOption] ** Create New Directory **"

    # --- Get User Choice ---
    $choice = $null
    while ($choice -eq $null) {
        $inputChoice = Read-Host "Enter the number for the destination directory"
        if ($inputChoice -match '^\d+$') {
            $numericChoice = [int]$inputChoice
            if ($numericChoice -ge 1 -and $numericChoice -le $newDirOption) {
                $choice = $numericChoice
            } else {
                Write-Warning "Invalid choice. Please enter a number between 1 and $newDirOption."
            }
        } else {
            Write-Warning "Wrong key! Now enter a number."
        }
    }

    # --- Process Choice ---
    $createNewDir = $false
    if ($choice -eq $newDirOption) {
        # Create New Directory
        $newDirName = ""
        while (-not $newDirName.Trim()) {
             $newDirName = Read-Host "Enter the name for the new directory (inside '$contentDirectoryName')"
             if (-not $newDirName.Trim()) {
                 Write-Warning "Directory name cannot be empty."
             }
             # Basic validation for invalid characters (optional, can be more robust)
             if ($newDirName -match '[\\/:*?"<>|]') {
                 Write-Warning "Directory name contains invalid characters (\ / : * ? "" < > |)."
                 $newDirName = "" # Reset to re-prompt
             }
        }
        $chosenDirName = $newDirName.Trim()
        $chosenDirPath = Join-Path -Path $contentDirPath -ChildPath $chosenDirName
        $createNewDir = $true
        Write-Host "Will create new directory: $chosenDirPath"

    } else {
        # Existing Directory
        $chosenDirObject = $dirMap[$choice]
        $chosenDirName = $chosenDirObject.Name
        $chosenDirPath = $chosenDirObject.FullName
        Write-Host "You selected existing directory: $chosenDirName"
    }

    # --- Confirm Choice ---
    $confirmation = $null
    while ($confirmation -notin @('1', '2')) {
        $confirmation = Read-Host "Confirm selection '$chosenDirName'? [1] Yes [2] No (choose again)"
        if ($confirmation -eq '1') {
            $confirmed = $true
        } elseif ($confirmation -eq '2') {
            $confirmed = $false
            Write-Host "Okay, let's choose again."
            Start-Sleep -Seconds 1
        } else {
            Write-Warning "Invalid input. Please enter 1 for Yes or 2 for No."
        }
    }

} until ($confirmed)

# --- Get Post Details ---
Write-Host "`n--- Post Details ---" -ForegroundColor Yellow

# Get Title
$title = ""
while (-not $title.Trim()) {
    $title = Read-Host "Enter the post title"
    if (-not $title.Trim()) {
        Write-Warning "Title cannot be empty."
    }
}
$title = $title.Trim()

# Get Tags
$tagsInput = Read-Host "Enter tags, separated by commas (e.g., tech, blog, eleventy)"
$tagsArray = $tagsInput -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ } # Split, trim, remove empty

# Format tags for YAML list
$yamlTags = $tagsArray | ForEach-Object { "`"$_`"" } | Join-String -Separator ', ' # Enclose each tag in quotes and join

# --- Prepare File Content ---
$currentDateTime = Get-Date
$isoDateTime = $currentDateTime.ToString("o") # ISO 8601 format (e.g., 2023-10-27T15:30:00.1234567+01:00) - Luxon handles this
$fileNameDate = $currentDateTime.ToString("yyyyMMdd")
$fileName = "$($fileNameDate).md"

# Escape double quotes in title for YAML safety
$yamlTitle = $title.Replace('"', '\"')

# Define YAML Front Matter and basic content using a Here-String
$fileContent = @"
---
title: "$yamlTitle"
date: $isoDateTime
tags: [$yamlTags]
---

# $title

Start writing your content here...
"@

# --- Create Directory and File ---

# Create the directory if requested
if ($createNewDir) {
    if (-not (Test-Path $chosenDirPath -PathType Container)) {
        try {
            Write-Host "Creating directory: $chosenDirPath"
            New-Item -Path $chosenDirPath -ItemType Directory -Force -ErrorAction Stop | Out-Null
        } catch {
            Write-Error "Failed to create directory '$chosenDirPath': $($_.Exception.Message)"
            Exit 1
        }
    } else {
         Write-Host "Directory '$chosenDirPath' already exists. Using it." -ForegroundColor Yellow
    }
}

# Define the full file path
$filePath = Join-Path -Path $chosenDirPath -ChildPath $fileName

# Check if file already exists (optional, but good practice)
if (Test-Path $filePath) {
    Write-Warning "File '$filePath' already exists. Overwriting is not implemented in this script. Please rename or delete the existing file."
    # Or implement overwrite confirmation logic here
    # Read-Host "File exists. Overwrite? (y/n)" ... etc.
    Exit 1
}

# Create and write the file
try {
    Write-Host "Creating file: $filePath"
    Set-Content -Path $filePath -Value $fileContent -Encoding UTF8 -ErrorAction Stop
    Write-Host "Successfully created file!" -ForegroundColor Green
} catch {
    Write-Error "Failed to create file '$filePath': $($_.Exception.Message)"
    Exit 1
}

# --- Open File in Default Editor ---
Write-Host "Opening file in default editor..."
try {
    Invoke-Item $filePath
} catch {
    Write-Warning "Could not automatically open the file. Please open it manually: $filePath"
}

Write-Host "`nScript finished." -ForegroundColor Cyan