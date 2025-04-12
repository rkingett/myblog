import os
import datetime
import subprocess

# Get the current date and time
now = datetime.datetime.now()
date_time = now.strftime("%Y%m%d%H%M")

# Get the list of template files
template_folder = "templates"
template_files = [f for f in os.listdir(template_folder) if os.path.isfile(os.path.join(template_folder, f))]

# If there is only one template file, use it without prompting
if len(template_files) == 1:
    template_file = template_files[0]
    output_folder = "drafts"
    output_file = f"{date_time}.md"
    output_path = os.path.join(output_folder, output_file)
    
    # Create the output folder if it does not exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
else:
    # If there are multiple template files, prompt the user to choose one
    print("Available templates:")
    for i, template_file in enumerate(template_files):
        print(f"{i+1}. {template_file}")
    
    # Get the user's choice
    while True:
        choice = input("Enter the number of your chosen template: ")
        if choice.isdigit() and 1 <= int(choice) <= len(template_files):
            template_file = template_files[int(choice) - 1]
            break
        else:
            print("Invalid choice. Please try again.")
    
    # Get the output folder name from the template file name
    output_folder = os.path.splitext(template_file)[0]
    output_file = f"{date_time}.md"
    output_path = os.path.join("content", output_folder, output_file)
    
    # Create the output folder if it does not exist
    if not os.path.exists(os.path.join("content", output_folder)):
        os.makedirs(os.path.join("content", output_folder))

# Get the title from the user
title = input("Enter the title: ")

# Read the template file and replace the placeholders
with open(os.path.join(template_folder, template_file), "r") as f:
    template_content = f.read()

template_content = template_content.replace("{{DATE}}", now.strftime("%Y-%m-%d"))
template_content = template_content.replace("{{TITLE}}", title)

# Write the content to the output file
with open(output_path, "w") as f:
    f.write(template_content)

# Ask the user if they want to open the newly created file
while True:
    open_file = input("Do you want to open the newly created file? (Y/N): ")
    if open_file.upper() == "Y":
        # Open the file using the default editor
        if os.name == 'nt':  # Windows
            os.startfile(output_path)
        else:  # Unix-based systems
            subprocess.call(['open', output_path])
        break
    elif open_file.upper() == "N":
        break
    else:
        print("Invalid choice. Please try again.")
