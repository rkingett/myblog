# Set the path to the Eleventy project directory
$projectDirectory = "$home/documents/myblog"

# Set the path to the template file
$templateFolder = "templates"
$templateFile = "template.md"
$templateFilePath = Join-Path -Path $projectDirectory -ChildPath (Join-Path -Path $templateFolder -ChildPath $templateFile)

# Set the path to the drafts folder
$draftsFolder = "drafts"
$draftsFolderPath = Join-Path -Path $projectDirectory -ChildPath $draftsFolder

# Check if the drafts folder exists, if not create it
if (!(Test-Path -Path $draftsFolderPath)) {
    New-Item -Path $draftsFolderPath -ItemType Directory
}

# Ask the user for the title of the post
$title = Read-Host "Please enter the title of your Eleventy post"

# Get the current date
$currentDate = Get-Date
$dateFormatted = $currentDate.ToString("yyyyMMdd")
$dateForYaml = $currentDate.ToString("yyyy-MM-dd")

# Read the content of the template file
$content = Get-Content -Path $templateFilePath -Raw

# Replace the placeholders with the user input and current date
$content = $content -replace "{{TITLE}}", $title
$content = $content -replace "{{DATE}}", $dateForYaml

# Define the path to the destination file based on the current date
$destinationFile = Join-Path -Path $draftsFolderPath -ChildPath ($dateFormatted + ".md")

# Write the modified content to the destination file
$content | Out-File -FilePath $destinationFile -Encoding utf8

Write-Host "File created successfully: $destinationFile"
