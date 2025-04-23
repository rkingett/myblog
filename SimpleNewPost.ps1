<#
.SYNOPSIS
Creates a new Markdown file with YAML front matter for Eleventy projects,
allowing the user to choose an output directory based on existing content folders
containing an 11tydata.js file, or create a new one.

.DESCRIPTION
This vast wall of text is for when I get older and I forgot why I made this thing. It automates the creation of new content files for Eleventy.
It scans the 'content' directory for subfolders containing an '11tydata.js' file.

- It presents these folders as choices for the output destination ("post type").
- It includes an option to create a new subfolder within 'content'.
- It prompts the user for a post title.
- It prompts the user for comma-separated tags.

It generates a Markdown file with YAML front matter including:
  - title: The user-provided title.
  - date: The current date and time in an ISO 8601 format compatible with Luxon's DateTime.fromISO.
  - tags: A YAML array of tags provided by the user.

The filename is the current date in YYYYMMDD format (e.g., 20231027.md).
The file is placed in the selected or newly created subfolder within 'content'.

Placeholders generated in the file:
- YAML front matter with title, date, tags.
- A placeholder text below the front matter.

.NOTES
Place this script in the root of your Eleventy project or adjust paths accordingly.
Assumes a standard project structure with a 'content' directory
at the same level as the script (or where PowerShell is run from).
Requires PowerShell 3.0 or later for $PSScriptRoot.

.EXAMPLE
.\New-EleventyContent.ps1
# Follow the prompts to select an output directory/type, enter a title, and enter tags.
#>

[CmdletBinding()]
param()

# --- Configuration ---
$contentFolderName = "content"

# --- Get Base Paths ---
# Use PSScriptRoot if the script is run directly, otherwise use current directory
if ($PSScriptRoot) {
    $projectRoot = $PSScriptRoot
} else {
    $projectRoot = Get-Location
    Write-Warning "PSScriptRoot not available. Using current directory '$projectRoot' as project root. Run the script directly (.\script.ps1) for best results."
}

$contentDir = Join-Path -Path $projectRoot -ChildPath $contentFolderName

# --- Get Current Date/Time ---
$currentDateTime = Get-Date
# ISO 8601 format with timezone offset, compatible with Luxon's DateTime.fromISO
# Example: 2023-10-27T15:30:00+01:00
$dateTimeIso = $currentDateTime.ToString("yyyy-MM-ddTHH:mm:sszzz")
# Filename format YYYYMMDD
$fileNameDate = $currentDateTime.ToString("yyyyMMdd")

# --- Find Potential Output Locations (Post Types) ---
Write-Host "Scanning for potential output directories in '$contentDir'..."

if (-not (Test-Path -Path $contentDir -PathType Container)) {
    Write-Error "Content directory not found: '$contentDir'. Please create it."
    exit 1
}

# Find subdirectories in 'content' that contain an '11tydata.js' file
$validTypeDirectories = Get-ChildItem -Path $contentDir -Directory | Where-Object {
    Test-Path -Path (Join-Path -Path $_.FullName -ChildPath '11tydata.js') -PathType Leaf
} | Sort-Object Name

# --- Handle Output Location Selection ---
$chosenDirectoryInfo = $null
$outputSubFolder = $null # The name of the subfolder (e.g., 'blog', 'notes')
$outputDir = $null     # The full path to the output directory

Write-Host "Please choose an output directory/type:"
$choiceIndex = 1
foreach ($dir in $validTypeDirectories) {
    Write-Host ("[{0}] {1}" -f $choiceIndex, $dir.Name)
    $choiceIndex++
}
$newFolderChoiceNumber = $choiceIndex
Write-Host ("[{0}] Create a new folder..." -f $newFolderChoiceNumber)

[int]$choice = 0
$maxChoice = $newFolderChoiceNumber
while ($choice -lt 1 -or $choice -gt $maxChoice) {
    $inputChoice = Read-Host -Prompt "Enter the number for your choice"
    if ($inputChoice -match '^\d+$') {
        $choice = [int]$inputChoice
        if ($choice -lt 1 -or $choice -gt $maxChoice) {
            Write-Warning "Invalid selection. Please enter a number between 1 and $maxChoice."
        }
    } else {
        Write-Warning "Invalid input. Please enter a number."
    }
}

# --- Determine and Prepare Output Directory ---
if ($choice -eq $newFolderChoiceNumber) {
    # Create a new folder
    $newFolderName = ""
    while ([string]::IsNullOrWhiteSpace($newFolderName) -or ($newFolderName -match '[\\/:"*?<>|]')) {
        $newFolderName = Read-Host -Prompt "Enter the name for the new folder (cannot contain invalid characters like \ / : * ? < > |)"
        if ([string]::IsNullOrWhiteSpace($newFolderName)) {
            Write-Warning "Folder name cannot be empty."
        } elseif ($newFolderName -match '[\\/:"*?<>|]') {
             Write-Warning "Folder name contains invalid characters."
        }
    }
    $outputSubFolder = $newFolderName.Trim()
    $outputDir = Join-Path -Path $contentDir -ChildPath $outputSubFolder
    Write-Host "Selected: Create new folder '$outputSubFolder'."

    if (-not (Test-Path -Path $outputDir -PathType Container)) {
        Write-Host "Creating new directory: '$outputDir'"
        try {
            New-Item -Path $outputDir -ItemType Directory -Force | Out-Null
        } catch {
            Write-Error "Failed to create directory '$outputDir': $($_.Exception.Message)"
            exit 1
        }
    } else {
         Write-Warning "Directory '$outputDir' already exists. Files will be added to it."
    }

} else {
    # Use an existing folder
    $chosenDirectoryInfo = $validTypeDirectories[$choice - 1]
    $outputSubFolder = $chosenDirectoryInfo.Name
    $outputDir = $chosenDirectoryInfo.FullName
    Write-Host "Selected directory: '$outputSubFolder'."
}

# --- Get Title Input ---
$postTitle = ""
while ([string]::IsNullOrWhiteSpace($postTitle)) {
    $postTitle = Read-Host -Prompt "Enter the title for the new post"
    if ([string]::IsNullOrWhiteSpace($postTitle)) {
        Write-Warning "Title cannot be empty."
    }
}
# Basic escaping for YAML - replace double quotes with escaped double quotes within the title
$yamlTitle = $postTitle.Replace('"', '""')

# --- Get Tags Input ---
$tagString = Read-Host -Prompt "Enter tags, separated by commas (e.g., blog, tech, tutorial)"
$tags = @() # Initialize an empty array for tags
if (-not [string]::IsNullOrWhiteSpace($tagString)) {
    $tags = $tagString.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
}

# Format tags for YAML array: ["tag1", "tag2", "tag three"]
$yamlTags = $tags | ForEach-Object { "`"$_`"" } # Enclose each tag in quotes
$yamlTagsString = $yamlTags -join ', '          # Join with comma and space

# --- Construct File Content ---
Write-Host "Generating content for '$postTitle'..."

# Build the YAML front matter and content
$outputContent = @"
---
title: "$yamlTitle"
date: "$dateTimeIso"
tags: [$yamlTagsString]
# Add other default front matter relevant to '$outputSubFolder' if needed
# layout: layouts/$outputSubFolder.njk # Example layout based on folder
---

Start writing your content here...
"@ # The '@ signifies the end of the here-string

# --- Generate Output File ---
$outputFileName = "$($fileNameDate).md"
$outputFilePath = Join-Path -Path $outputDir -ChildPath $outputFileName

# Check if file already exists
if (Test-Path -Path $outputFilePath -PathType Leaf) {
    Write-Warning "File '$outputFilePath' already exists. Overwriting..."
    # Or uncomment the next two lines to prevent overwrite and exit
    # Write-Error "File '$outputFilePath' already exists. Aborting."
    # exit 1
}

Write-Host "Writing output file to '$outputFilePath'..."
try {
    # Use UTF8 encoding without BOM, common for web files
    if ($PSVersionTable.PSVersion.Major -ge 5 -and $PSVersionTable.PSVersion.Minor -ge 1) {
         Set-Content -Path $outputFilePath -Value $outputContent -Encoding UTF8NoBOM -Force
    } else {
         Write-Warning "PowerShell version less than 5.1. Using default UTF8 encoding (may include BOM)."
         Set-Content -Path $outputFilePath -Value $outputContent -Encoding UTF8 -Force
    }
    Write-Host ("Successfully created file: '{0}'" -f $outputFilePath) -ForegroundColor Green
} catch {
    Write-Error "Failed to write output file: $($_.Exception.Message)"
    exit 1
}

Write-Host "Script finished."