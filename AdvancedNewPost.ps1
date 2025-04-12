# Get the current date and time
$now = Get-Date
$date_time = $now.ToString("yyyyMMddHHmm")

# Get the list of template files
$template_folder = "templates"
$template_files = Get-ChildItem -Path $template_folder -File | Select-Object -ExpandProperty Name

# If there is only one template file, use it without prompting
if ($template_files.Count -eq 1) {
    $template_file = $template_files
    $output_folder = "drafts"
    $output_file = "$date_time.md"
    $output_path = Join-Path -Path $output_folder -ChildPath $output_file
    
    # Create the output folder if it does not exist
    if (!(Test-Path -Path $output_folder)) {
        New-Item -Path $output_folder -ItemType Directory
    }
} else {
    # If there are multiple template files, prompt the user to choose one
    Write-Host "Available templates:"
    for ($i = 0; $i -lt $template_files.Count; $i++) {
        Write-Host ($i + 1) ". " $template_files[$i]
    }
    
    # Get the user's choice
    while ($true) {
        $choice = Read-Host "Enter the number of your chosen template"
        if ($choice -match "^\d+$" -and 1 -le [int]$choice -and [int]$choice -le $template_files.Count) {
            $template_file = $template_files[[int]$choice - 1]
            break
        } else {
            Write-Host "Invalid choice. Please try again."
        }
    }
    
    # Get the output folder name from the template file name
    $output_folder = $template_file -replace "\.[^\.]+$"
    $output_file = "$date_time.md"
    $output_path = Join-Path -Path "content" -ChildPath $output_folder -AdditionalChildPath $output_file
    
    # Create the output folder if it does not exist
    $output_folder_path = Join-Path -Path "content" -ChildPath $output_folder
    if (!(Test-Path -Path $output_folder_path)) {
        New-Item -Path $output_folder_path -ItemType Directory
    }
}

# Get the title from the user
$title = Read-Host "Enter the title"

# Read the template file and replace the placeholders
$template_content = Get-Content -Path (Join-Path -Path $template_folder -ChildPath $template_file) -Raw
$template_content = $template_content -replace "{{DATE}}", $now.ToString("yyyy-MM-dd")
$template_content = $template_content -replace "{{TITLE}}", $title

# Write the content to the output file
$template_content | Out-File -FilePath $output_path -Encoding utf8

# Ask the user if they want to open the newly created file
while ($true) {
    $open_file = Read-Host "Do you want to open the newly created file? (Y/N)"
    if ($open_file -eq "Y") {
        # Open the file using the default editor
        Invoke-Item -Path $output_path
        break
    } elseif ($open_file -eq "N") {
        break
    } else {
        Write-Host "Invalid choice. Please try again."
    }
}
