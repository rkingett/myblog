<#
.ForWhenIGetOld
Creates a new Markdown file with YAML front matter for Eleventy projects,
using templates found in a 'templates' directory.

.DESCRIPTION
This script automates the creation of new content files for Eleventy.
It finds Markdown templates (.md) in a 'templates' folder relative to the script's location.

- If no templates are found, it exits with an error.
- If one template is found, it automatically uses it.
- If multiple templates are found, it prompts the user to choose one.

The script prompts the user for a post title.
It generates a Markdown file with YAML front matter including:
  - title: The user-provided title.
  - date: The current date and time in an ISO 8601 format compatible with Luxon's DateTime.fromISO.

The filename is the current date in YYYYMMDD format (e.g., 20231027.md).

Output Destination:
- If a specific template was chosen (multiple templates existed), the file is placed in 'content/<template_name>/'.
- If the single template was automatically chosen, the file is placed in 'content/Drafts/'.
- The 'content', 'content/Drafts', or 'content/<template_name>' directories are created if they don't exist.

Placeholders in the template file:
- {{TITLE}} : Replaced with the user-provided title.
- {{DATETIME_ISO}} : Replaced with the current date/time in ISO 8601 format.

.NOTES
Place this script in the root of your Eleventy project or adjust paths accordingly.
Assumes a standard project structure with 'templates' and 'content' directories
at the same level as the script (or where PowerShell is run from).
Requires PowerShell 3.0 or later for $PSScriptRoot.

.EXAMPLE
.\AdvancedNewPost.ps1
# Follow the prompts to select a template (if applicable) and enter a title.
#>

[CmdletBinding()]
param()

# --- Configuration ---
$templatesFolderName = "templates"
$contentFolderName = "content"
$draftsFolderName = "Drafts" # Used only when a single template is found

# --- Get Base Paths ---
# Use PSScriptRoot if the script is run directly, otherwise use current directory
if ($PSScriptRoot) {
    $projectRoot = $PSScriptRoot
} else {
    $projectRoot = Get-Location
    Write-Warning "PSScriptRoot not available. Using current directory '$projectRoot' as project root. Run the script directly (.\script.ps1) for best results."
}

$templatesDir = Join-Path -Path $projectRoot -ChildPath $templatesFolderName
$contentDir = Join-Path -Path $projectRoot -ChildPath $contentFolderName

# --- Get Current Date/Time ---
$currentDateTime = Get-Date
# ISO 8601 format with timezone offset, compatible with Luxon's DateTime.fromISO
# Example: 2023-10-27T15:30:00+01:00
$dateTimeIso = $currentDateTime.ToString("yyyy-MM-ddTHH:mm:sszzz")
# Filename format YYYYMMDD
$fileNameDate = $currentDateTime.ToString("yyyyMMdd")

# --- Find Templates ---
Write-Host "Scanning for templates in '$templatesDir'..."

if (-not (Test-Path -Path $templatesDir -PathType Container)) {
    Write-Error "Template directory not found: '$templatesDir'. Please create it and add template .md files."
    exit 1
}

# Look for Markdown files in the templates directory
$templateFiles = Get-ChildItem -Path $templatesDir -Filter *.md -File

# --- Handle Template Selection ---
$chosenTemplateFile = $null
$outputSubFolder = $null

switch ($templateFiles.Count) {
    0 {
        Write-Error "No template (.md) files found in '$templatesDir'."
        exit 1
    }
    1 {
        $chosenTemplateFile = $templateFiles[0]
        $outputSubFolder = $draftsFolderName
        Write-Host "Found one template: '$($chosenTemplateFile.Name)'. Using it automatically."
        Write-Host "Output will be placed in '$contentFolderName\$outputSubFolder'."
    }
    default {
        # More than one template
        Write-Host "Multiple templates found. Please choose one:"
        for ($i = 0; $i -lt $templateFiles.Count; $i++) {
            Write-Host ("[{0}] {1}" -f ($i + 1), $templateFiles[$i].Name)
        }

        [int]$choice = 0
        while ($choice -lt 1 -or $choice -gt $templateFiles.Count) {
            $inputChoice = Read-Host -Prompt "Enter the number of the template to use"
            if ($inputChoice -match '^\d+$') {
                $choice = [int]$inputChoice
                if ($choice -lt 1 -or $choice -gt $templateFiles.Count) {
                    Write-Warning "Invalid selection. Please enter a number between 1 and $($templateFiles.Count)."
                }
            } else {
                Write-Warning "Invalid input. Please enter a number."
            }
        }
        $chosenTemplateFile = $templateFiles[$choice - 1]
        # Output subfolder matches the template name without extension
        $outputSubFolder = $chosenTemplateFile.BaseName
        Write-Host "You selected: '$($chosenTemplateFile.Name)'."
        Write-Host "Output will be placed in '$contentFolderName\$outputSubFolder'."
    }
}

# --- Get Title Input ---
$postTitle = ""
while ([string]::IsNullOrWhiteSpace($postTitle)) {
    $postTitle = Read-Host -Prompt "Enter the title for the new post"
    if ([string]::IsNullOrWhiteSpace($postTitle)) {
        Write-Warning "Title cannot be empty."
    }
}

# --- Prepare Output ---
# Ensure the base content directory exists
if (-not (Test-Path -Path $contentDir -PathType Container)) {
    Write-Host "Creating content directory: '$contentDir'"
    New-Item -Path $contentDir -ItemType Directory -Force | Out-Null
}

# Define and ensure the specific output directory exists
$outputDir = Join-Path -Path $contentDir -ChildPath $outputSubFolder
if (-not (Test-Path -Path $outputDir -PathType Container)) {
    Write-Host "Creating output directory: '$outputDir'"
    New-Item -Path $outputDir -ItemType Directory -Force | Out-Null
}

# Construct the full output file path
$outputFileName = "$($fileNameDate).md"
$outputFilePath = Join-Path -Path $outputDir -ChildPath $outputFileName

# Check if file already exists (optional, but good practice)
if (Test-Path -Path $outputFilePath -PathType Leaf) {
    Write-Warning "File '$outputFilePath' already exists. Overwriting..."
    # Or uncomment the next two lines to prevent overwrite and exit
    # Write-Error "File '$outputFilePath' already exists. Aborting."
    # exit 1
}

# --- Process Template and Create File ---
Write-Host "Reading template '$($chosenTemplateFile.FullName)'..."
$templateContent = Get-Content -Path $chosenTemplateFile.FullName -Raw

Write-Host "Generating content for '$postTitle'..."
# Replace placeholders (case-sensitive)
$outputContent = $templateContent -replace '\{\{TITLE\}\}', $postTitle
$outputContent = $outputContent -replace '\{\{DATETIME_ISO\}\}', $dateTimeIso

Write-Host "Writing output file to '$outputFilePath'..."
try {
    # Use UTF8 encoding without BOM, common for web files
    # Requires PowerShell 5.1+ for -Encoding UTF8NoBOM with Set-Content
    # For older PS versions, you might need different encoding handling.
    if ($PSVersionTable.PSVersion.Major -ge 5 -and $PSVersionTable.PSVersion.Minor -ge 1) {
         Set-Content -Path $outputFilePath -Value $outputContent -Encoding UTF8NoBOM -Force
    } else {
         # Fallback for older PowerShell (might include BOM)
         Write-Warning "PowerShell version less than 5.1. Using default UTF8 encoding (may include BOM)."
         Set-Content -Path $outputFilePath -Value $outputContent -Encoding UTF8 -Force
    }
    Write-Host ("Successfully created file: '{0}'" -f $outputFilePath) -ForegroundColor Green
} catch {
    Write-Error "Failed to write output file: $($_.Exception.Message)"
    exit 1
}

Write-Host "Script finished."