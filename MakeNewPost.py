import os
import sys
import subprocess
import datetime
import importlib.util
import platform

# --- Configuration ---
CONTENT_DIR_NAME = "content"
EXCLUDED_DIRS = ["feed", "helper", "helpers"] # Directories inside CONTENT_DIR_NAME to ignore

# --- Function to check and install PyYAML ---
def check_and_install_yaml():
    """Checks if PyYAML is installed, installs it if not."""
    package_name = "PyYAML"
    spec = importlib.util.find_spec("yaml")
    if spec is None:
        print(f"'{package_name}' not found. Attempting to install...")
        try:
            # Using sys.executable ensures pip is run from the correct Python environment
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"'{package_name}' installed successfully.")
            # Need to re-check spec after installation for the current run
            globals()["yaml"] = importlib.import_module("yaml")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to install '{package_name}'. Please install it manually using 'pip install {package_name}'.")
            print(f"Error details: {e}")
            sys.exit(1) # Exit if installation fails
        except ImportError:
             print(f"ERROR: '{package_name}' installed but could not be imported. Please check your Python environment.")
             sys.exit(1)
    else:
        print(f"'{package_name}' is already installed.")
        # Import it if already installed
        globals()["yaml"] = importlib.import_module("yaml")

# --- Function to find and select output directory ---
def select_output_directory(base_content_dir):
    """Scans for directories, presents choices, handles new directory creation."""
    while True: # Loop for directory selection and confirmation
        possible_dirs = []
        try:
            for item in os.listdir(base_content_dir):
                item_path = os.path.join(base_content_dir, item)
                if os.path.isdir(item_path) and item.lower() not in EXCLUDED_DIRS:
                    possible_dirs.append(item)
        except FileNotFoundError:
            print(f"ERROR: Could not list directories in '{base_content_dir}'. It might not exist or permissions are denied.")
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred while scanning directories: {e}")
            sys.exit(1)

        print("\nAvailable output directories:")
        for i, dir_name in enumerate(possible_dirs):
            print(f"  {i + 1}: {dir_name}")
        new_dir_option_num = len(possible_dirs) + 1
        print(f"  {new_dir_option_num}: Create a new directory inside '{CONTENT_DIR_NAME}'")

        # --- Get user choice ---
        choice = input(f"Enter the number for the output directory (1-{new_dir_option_num}): ")

        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(possible_dirs):
                selected_dir_name = possible_dirs[choice_num - 1]
                selected_dir_path = os.path.join(base_content_dir, selected_dir_name)
                is_new_dir = False
            elif choice_num == new_dir_option_num:
                selected_dir_name = "NEW" # Placeholder
                selected_dir_path = None # Will be determined later
                is_new_dir = True
            else:
                print("Invalid choice number. Please try again.")
                continue

            # --- Confirm Choice ---
            if is_new_dir:
                confirm_prompt = f"You chose to create a new directory. Is this correct? (1=Yes, 2=No/Choose again): "
            else:
                 confirm_prompt = f"You selected directory '{selected_dir_name}'. Is this correct? (1=Yes, 2=No/Choose again): "

            confirm = input(confirm_prompt)
            if confirm == '1':
                 # --- Handle New Directory Creation ---
                if is_new_dir:
                    while True:
                        new_dir_name = input("Enter the name for the new directory: ").strip()
                        if not new_dir_name:
                            print("Directory name cannot be empty.")
                            continue
                        # Basic sanitization (replace spaces, avoid problematic chars - adjust as needed)
                        # new_dir_name = new_dir_name.replace(" ", "-").lower()
                        # For simplicity, we'll allow most names but check for existence
                        new_dir_path = os.path.join(base_content_dir, new_dir_name)

                        if os.path.exists(new_dir_path):
                            print(f"Directory '{new_dir_name}' already exists. Please choose a different name.")
                        else:
                            try:
                                os.makedirs(new_dir_path)
                                print(f"Successfully created directory: '{new_dir_path}'")
                                selected_dir_path = new_dir_path
                                break # Exit new directory name loop
                            except OSError as e:
                                print(f"ERROR: Could not create directory '{new_dir_path}'. Error: {e}")
                                # Go back to directory selection
                                selected_dir_path = None # Reset path
                                break # Exit new directory name loop, will restart outer loop
                            except Exception as e:
                                print(f"An unexpected error occurred creating directory: {e}")
                                sys.exit(1)
                    if selected_dir_path is None: # If directory creation failed, restart selection
                        continue

                return selected_dir_path # Return the final path (existing or newly created)

            elif confirm == '2':
                print("Okay, let's choose again.")
                continue # Go back to the start of the while loop
            else:
                print("Invalid confirmation input. Please enter 1 or 2.")
                # Ask for confirmation again for the *same* choice
                # To re-list directories, we need to 'continue' the outer loop
                continue

        except ValueError:
            print("Invalid input. Please enter a number.")
            continue # Go back to the start of the while loop

# --- Function to get user input for post details ---
def get_post_details():
    """Prompts user for title and tags."""
    while True:
        title = input("Enter the title for the post: ").strip()
        if title:
            break
        else:
            print("Title cannot be empty.")

    while True:
        tags_input = input("Enter tags, separated by commas (e.g., tech, blog, update): ").strip()
        if tags_input:
            # Split, strip whitespace from each tag, filter empty strings
            tags_list = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            if tags_list:
                 # Format for YAML list representation
                 tags_yaml_list = yaml.dump(tags_list, default_flow_style=True).strip()
                 # Alternative manual formatting:
                 # tags_yaml_list = "[" + ", ".join([f'"{tag}"' for tag in tags_list]) + "]"
                 break
            else:
                 print("Please enter at least one valid tag.")
        else:
            # Allow no tags if input is empty
            tags_yaml_list = "[]"
            break

    return title, tags_yaml_list

# --- Function to open file in default editor ---
def open_file_in_editor(filepath):
    """Opens the specified file in the system's default text editor."""
    try:
        if platform.system() == "Windows":
            # 'start' command is safer than os.startfile for command line context
            subprocess.run(['start', '', filepath], check=True, shell=True)
        elif platform.system() == "Darwin": # macOS
            subprocess.run(['open', filepath], check=True)
        else: # Linux and other Unix-like
            subprocess.run(['xdg-open', filepath], check=True)
        print(f"Attempting to open '{filepath}' in your default editor...")
    except FileNotFoundError as e:
         # This might happen if 'start', 'open', or 'xdg-open' isn't in the PATH
         print(f"ERROR: Could not find command to open file. Error: {e}")
         print(f"Please open the file manually: {filepath}")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Command to open file failed. Error: {e}")
        print(f"Please open the file manually: {filepath}")
    except Exception as e:
        print(f"An unexpected error occurred while trying to open the file: {e}")
        print(f"Please open the file manually: {filepath}")


# --- Main Script Execution ---
if __name__ == "__main__":
    print("--- Eleventy Post Generator ---")

    # 1. Check and install PyYAML
    check_and_install_yaml()
    # Now 'yaml' should be available in the global scope if successful

    # 2. Find the content directory
    current_dir = os.getcwd()
    content_dir_path = os.path.join(current_dir, CONTENT_DIR_NAME)

    if not os.path.isdir(content_dir_path):
        print(f"\nERROR: Content directory '{CONTENT_DIR_NAME}' not found in the current directory ('{current_dir}').")
        print("Please run this script from the root of your Eleventy project.")
        sys.exit(1)
    else:
        print(f"\nFound content directory: '{content_dir_path}'")

    # 3. Select Output Directory
    chosen_output_dir = select_output_directory(content_dir_path)
    if not chosen_output_dir: # Should not happen if logic is correct, but good failsafe
         print("ERROR: No output directory was selected or created.")
         sys.exit(1)

    print(f"\nSelected output location: {chosen_output_dir}")

    # 4. Get Post Details (Title, Tags)
    post_title, post_tags_yaml = get_post_details()

    # 5. Generate Date/Time and Filename
    # Use timezone-aware UTC time for ISO 8601 consistency
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    # Format for YAML front matter (Luxon compatible)
    iso_timestamp = now_utc.isoformat() # e.g., 2023-10-27T10:30:00.123456+00:00
    # Format for filename (YYYYMMDD)
    filename_date = now_utc.strftime("%Y%m%d")

    # 6. Construct File Content (YAML Front Matter + Markdown Body)
    yaml_front_matter = f"""---
title: "{post_title}"
date: "{iso_timestamp}"
tags: {post_tags_yaml}
---

""" # Extra newline after front matter

    markdown_content = yaml_front_matter + "\n# Start writing your content here\n"

    # 7. Determine Output File Path
    output_filename = f"{filename_date}.md"
    output_file_path = os.path.join(chosen_output_dir, output_filename)

    # 8. Write the file
    try:
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"\nSuccessfully created Markdown file: '{output_file_path}'")
    except IOError as e:
        print(f"\nERROR: Could not write to file '{output_file_path}'. Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred while writing the file: {e}")
        sys.exit(1)

    # 9. Open the file in the default editor
    open_file_in_editor(output_file_path)

    print("\n--- Script finished ---")