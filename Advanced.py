import os
import sys
import subprocess
import datetime
import platform
import shutil
import time
from pathlib import Path

# --- Configuration ---
CONTENT_DIR_NAME = "content"
DRAFTS_DIR_NAME = "drafts"
EXCLUDE_DIRS = {'feed', 'feeds', 'helper', 'helpers'} # Directories to exclude from choices

# --- Helper Functions ---

def check_and_install_pyyaml():
    """Checks if PyYAML is installed and installs it if not."""
    try:
        import yaml
        print("PyYAML is already installed.")
        return True
    except ImportError:
        print("PyYAML not found. Attempting to install...")
        try:
            # Ensure pip is available
            subprocess.check_call([sys.executable, "-m", "pip", "--version"])
            # Install PyYAML
            subprocess.check_call([sys.executable, "-m", "pip", "install", "PyYAML"])
            print("PyYAML installed successfully.")
            # Need to import it now after installation
            global yaml
            import yaml
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error installing PyYAML: {e}")
            print("Please install PyYAML manually using: pip install PyYAML")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during installation: {e}")
            print("Please install PyYAML manually using: pip install PyYAML")
            return False

def get_confirmation(prompt):
    """Gets user confirmation (1 for Yes, 2 for No)."""
    while True:
        try:
            choice = input(f"{prompt} (1: Yes, 2: No): ").strip()
            if choice == '1':
                return True
            elif choice == '2':
                return False
            else:
                print("Invalid input. Please enter 1 for Yes or 2 for No.")
        except EOFError:
            print("\nOperation cancelled.")
            return False

def get_numbered_choice(prompt, options):
    """Presents numbered options and gets a valid choice."""
    if not options:
        print("No options available.")
        return None, None # Return None for choice index and value

    while True:
        print(prompt)
        for i, option in enumerate(options):
            print(f"{i + 1}. {option}")

        try:
            choice = input("Enter your choice number: ").strip()
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(options):
                chosen_option = options[choice_index]
                # Confirmation step
                if get_confirmation(f"You selected: '{chosen_option}'. Confirm?"):
                    return choice_index, chosen_option
                else:
                    # If confirmation fails, loop will restart and show options again
                    print("-" * 20) # Separator
                    continue
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(options)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except EOFError:
            print("\nOperation cancelled.")
            return None, None

def get_valid_input(prompt):
    """Gets non-empty input from the user."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        else:
            print("Input cannot be empty.")

def get_iso_datetime():
    """Returns the current datetime in ISO 8601 format suitable for Luxon."""
    # Using a format that is common and easily parsed by Luxon
    # Example: 2023-10-27T10:30:00.123+00:00 or 2023-10-27T10:30:00Z
    # datetime.isoformat() produces a suitable format.
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def find_project_root():
    """Assumes the script is run from the project root."""
    # Simple assumption: current working directory is the project root.
    # More robust methods could look for marker files like package.json, .git, etc.
    return Path.cwd()

def find_directory(base_path, dir_name):
    """Finds a directory by name within the base path."""
    target_dir = base_path / dir_name
    if target_dir.is_dir():
        return target_dir
    # Maybe search one level deeper? The prompt implies it's directly there.
    # Let's stick to the direct path for now.
    return None

def get_valid_subdirectories(parent_dir, exclude_names):
    """Gets a list of valid subdirectories, excluding specified names."""
    valid_dirs = []
    if not parent_dir or not parent_dir.is_dir():
        return valid_dirs
    for item in parent_dir.iterdir():
        if item.is_dir() and item.name.lower() not in exclude_names:
            valid_dirs.append(item)
    return valid_dirs

def create_md_file(filepath, title, tags_list, date_iso):
    """Creates the markdown file with YAML front matter."""
    try:
        # Ensure the directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Construct YAML front matter
        front_matter = {
            'title': title,
            'date': date_iso,
            'tags': tags_list
        }
        yaml_string = yaml.dump(front_matter, default_flow_style=None, sort_keys=False)

        # Construct file content
        content = f"---\n{yaml_string}---\n\n<!-- Your post content starts here -->\n"

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully created file: {filepath}")
        return True
    except Exception as e:
        print(f"Error creating file {filepath}: {e}")
        return False

def open_file_or_folder(path_to_open):
    """Opens a file or folder using the default system application."""
    try:
        path_str = str(path_to_open)
        print(f"Attempting to open: {path_str}")
        if platform.system() == "Windows":
            # os.startfile doesn't block (wait)
            os.startfile(path_str)
        elif platform.system() == "Darwin": # macOS
            subprocess.run(['open', path_str], check=True)
        else: # Linux and other Unix-like systems
            subprocess.run(['xdg-open', path_str], check=True)
        # Short delay to allow the file explorer/editor to potentially launch
        time.sleep(1)
        return True
    except FileNotFoundError:
         print(f"Error: Path not found - {path_str}")
         return False
    except Exception as e:
        print(f"Error opening {path_str}: {e}")
        return False

def attempt_open_and_wait(filepath):
    """
    Attempts to open a file with the default editor and waits.
    This is platform-dependent and might not reliably wait for all editors.
    Falls back to simple open if specific waiting mechanism fails.
    Returns True if opening was attempted, False otherwise.
    """
    filepath_str = str(filepath)
    print(f"Attempting to open '{filepath_str}' in default editor...")
    editor_opened = False
    try:
        if platform.system() == "Windows":
            # 'start /wait' might work for some console apps or executables,
            # but often doesn't wait for GUI editors like Notepad, VS Code etc.
            # We use os.startfile as a more general approach, accepting it won't wait.
            os.startfile(filepath_str)
            editor_opened = True
            print("File opened. Waiting requires manual confirmation (press Enter)...")
            input("Press Enter after you have saved and closed the file...")
        elif platform.system() == "Darwin": # macOS
            # 'open -W' waits for the application to quit
            subprocess.run(['open', '-W', filepath_str], check=True)
            editor_opened = True
            print("Editor closed.")
        else: # Linux
            # Finding the default editor and making xdg-open wait is complex.
            # We'll use xdg-open and rely on manual confirmation.
            subprocess.run(['xdg-open', filepath_str], check=True)
            editor_opened = True
            print("File opened. Waiting requires manual confirmation (press Enter)...")
            input("Press Enter after you have saved and closed the file...")

    except FileNotFoundError:
         print(f"Error: File not found - {filepath_str}")
    except subprocess.CalledProcessError as e:
        print(f"Error opening file with waiting: {e}")
        # Fallback to simple open without wait
        print("Falling back to simple open...")
        editor_opened = open_file_or_folder(filepath)
    except Exception as e:
        print(f"An unexpected error occurred while opening editor: {e}")
        # Fallback?
        print("Attempting simple open...")
        editor_opened = open_file_or_folder(filepath)

    if editor_opened and platform.system() != "Darwin":
         # Add a small delay for systems where we used manual prompt
         time.sleep(1)

    return editor_opened


# --- Main Choices ---

def choice_1_new_post_category(project_root, content_dir):
    """Handles Choice 1: Draft a new post in a category folder."""
    print("\n--- Draft a new post in a category folder ---")
    if not content_dir:
        print(f"Error: Content directory ('{CONTENT_DIR_NAME}') not found in {project_root}")
        return

    while True: # Loop for directory selection
        subdirs = get_valid_subdirectories(content_dir, EXCLUDE_DIRS)
        dir_options = [d.name for d in subdirs]
        dir_options.append("Create a new category folder")

        choice_index, chosen_option = get_numbered_choice(
            "Select the category (output directory):", dir_options
        )

        if choice_index is None: # User cancelled during selection
             print("Operation cancelled.")
             return # Back to main menu

        target_dir = None
        if chosen_option == "Create a new category folder":
            while True:
                new_dir_name = get_valid_input("Enter the name for the new category folder: ")
                # Basic validation for folder name (optional, can be enhanced)
                if EXCLUDE_DIRS.intersection(set(new_dir_name.lower().split())) :
                     print(f"Folder name '{new_dir_name}' is not allowed.")
                     continue
                if not new_dir_name or any(c in r'<>:"/\|?*' for c in new_dir_name):
                    print("Invalid folder name. Avoid special characters: <>:\"/\\|?*")
                    continue
                target_dir = content_dir / new_dir_name
                try:
                    target_dir.mkdir(parents=True, exist_ok=False)
                    print(f"Folder '{target_dir.name}' created successfully.")
                    break
                except FileExistsError:
                    print(f"Folder '{target_dir.name}' already exists. Please choose a different name or select the existing folder.")
                    # Let them choose again from the list
                    target_dir = None # Reset target_dir
                    break # Break inner loop to re-display directory choices
                except Exception as e:
                    print(f"Error creating folder: {e}")
                    # Let them choose again from the list
                    target_dir = None # Reset target_dir
                    break # Break inner loop to re-display directory choices
            if target_dir is None:
                 continue # Re-prompt directory selection

        else:
            target_dir = subdirs[choice_index] # Get the Path object

        # If we have a valid target_dir (either selected or newly created), break the selection loop
        if target_dir:
            break
        # else: loop continues if 'Create new' failed and needed retry

    # --- Get Post Details ---
    post_title = get_valid_input("Enter the post title: ")
    tags_input = get_valid_input("Enter tags, separated by commas (e.g., tech, blog, javascript): ")
    tags_list = [tag.strip() for tag in tags_input.split(',') if tag.strip()]

    # --- Prepare File ---
    current_time_iso = get_iso_datetime()
    # Filename: YYYYMMDD.md
    file_date_str = datetime.datetime.now().strftime("%Y%m%d")
    filename = f"{file_date_str}.md"
    filepath = target_dir / filename
    counter = 1
    while filepath.exists(): # Avoid overwriting
        filename = f"{file_date_str}_{counter}.md"
        filepath = target_dir / filename
        counter += 1


    # --- Create File ---
    if not create_md_file(filepath, post_title, tags_list, current_time_iso):
        print("Failed to create post file.")
        return # Back to main menu

    # --- Post Creation Actions ---
    if get_confirmation("Do you want to open the new file in your editor?"):
        editor_opened = attempt_open_and_wait(filepath)
        # Regardless of whether waiting worked perfectly, open project folder afterwards
        print("Opening project folder...")
        open_file_or_folder(project_root)
    else:
        # Don't open editor, just open project folder and exit script
        print("Opening project folder...")
        open_file_or_folder(project_root)
        # The prompt implies the script exits here for Choice 1 if 'no' is selected
        print("Exiting script.")
        sys.exit() # Exit script


def choice_2_new_draft(project_root):
    """Handles Choice 2: Make a new draft in the drafts folder."""
    print("\n--- Make a new draft in the drafts folder ---")
    drafts_dir = project_root / DRAFTS_DIR_NAME

    try:
        drafts_dir.mkdir(parents=True, exist_ok=True)
        print(f"Ensured drafts directory exists: {drafts_dir}")
    except Exception as e:
        print(f"Error creating/accessing drafts directory '{drafts_dir}': {e}")
        return # Back to main menu

    # --- Get Post Details ---
    post_title = get_valid_input("Enter the draft title: ")
    tags_input = get_valid_input("Enter tags, separated by commas (e.g., idea, wip): ")
    tags_list = [tag.strip() for tag in tags_input.split(',') if tag.strip()]

    # --- Prepare File ---
    current_time_iso = get_iso_datetime()
    file_date_str = datetime.datetime.now().strftime("%Y%m%d")
    filename = f"{file_date_str}.md"
    filepath = drafts_dir / filename
    counter = 1
    while filepath.exists(): # Avoid overwriting
        filename = f"{file_date_str}_{counter}.md"
        filepath = drafts_dir / filename
        counter += 1

    # --- Create File ---
    if not create_md_file(filepath, post_title, tags_list, current_time_iso):
        print("Failed to create draft file.")
        return # Back to main menu

    # --- Post Creation Actions ---
    move_file_after_edit = False
    editor_opened_successfully = False

    if get_confirmation("Do you want to open the new draft in your editor?"):
        editor_opened_successfully = attempt_open_and_wait(filepath)
        if editor_opened_successfully:
             if get_confirmation("Do you want to move this draft to a category now?"):
                 move_file_after_edit = True
        else:
            print("Editor failed to open or wait. Skipping move prompt.")

    else:
        # If user chooses not to open editor
        print("Opening project folder...")
        open_file_or_folder(project_root)
        print("Exiting script.")
        sys.exit() # Exit script as per prompt


    # --- Handle Moving ---
    if move_file_after_edit:
        content_dir = find_directory(project_root, CONTENT_DIR_NAME)
        if not content_dir:
            print(f"Error: Content directory ('{CONTENT_DIR_NAME}') not found. Cannot move file.")
            print("Opening drafts folder for manual moving...")
            open_file_or_folder(drafts_dir)
        else:
            while True: # Loop for move destination selection
                subdirs = get_valid_subdirectories(content_dir, EXCLUDE_DIRS)
                if not subdirs:
                     print(f"No suitable category folders found in '{content_dir.name}'.")
                     print("Opening drafts folder for manual moving...")
                     open_file_or_folder(drafts_dir)
                     break # Break move destination loop

                dir_options = [d.name for d in subdirs]
                choice_index, chosen_option = get_numbered_choice(
                    f"Select the destination category for '{filepath.name}':", dir_options
                )

                if choice_index is not None:
                    destination_dir = subdirs[choice_index]
                    destination_path = destination_dir / filepath.name
                    try:
                        print(f"Moving '{filepath.name}' to '{destination_dir.name}'...")
                        shutil.move(str(filepath), str(destination_path))
                        print("Move successful.")
                        break # Break move destination loop
                    except Exception as e:
                        print(f"Error moving file: {e}")
                        # Ask if they want to try again or skip moving
                        if not get_confirmation("Move failed. Try choosing a destination again?"):
                             print("Skipping move. Opening drafts folder...")
                             open_file_or_folder(drafts_dir)
                             break # Break move destination loop
                        # else: continue loop to select destination again
                else: # User cancelled selection
                    print("Move cancelled. Opening drafts folder...")
                    open_file_or_folder(drafts_dir)
                    break # Break move destination loop
    elif editor_opened_successfully: # Editor was opened, but user chose NOT to move
        print("Opening drafts folder for manual moving...")
        open_file_or_folder(drafts_dir)

    # --- Final Prompt (Only reached if editor was opened) ---
    if get_confirmation("Go back to the main menu? (No will exit)"):
        return # Go back to main loop
    else:
        print("Opening project folder...")
        open_file_or_folder(project_root)
        print("Exiting script.")
        sys.exit()


def choice_3_move_drafts(project_root, content_dir):
    """Handles Choice 3: Move drafts to post categories."""
    print("\n--- Move drafts to post categories ---")
    drafts_dir = project_root / DRAFTS_DIR_NAME

    if not drafts_dir.is_dir():
        print(f"Drafts directory ('{DRAFTS_DIR_NAME}') not found. Nothing to move.")
        return

    draft_files = [f for f in drafts_dir.iterdir() if f.is_file()] # Simple check, could filter by .md
    if not draft_files:
        print(f"No files found in the drafts directory ('{drafts_dir.name}').")
        return

    if not content_dir:
        print(f"Error: Content directory ('{CONTENT_DIR_NAME}') not found. Cannot select destinations.")
        return

    # Get valid destinations once
    dest_dirs = get_valid_subdirectories(content_dir, EXCLUDE_DIRS)
    if not dest_dirs:
        print(f"No suitable destination folders found in '{content_dir.name}'. Cannot move drafts.")
        return
    dest_options = [d.name for d in dest_dirs]

    moves_to_perform = {} # Store {source_path: destination_dir_path}

    if len(draft_files) == 1:
        draft_file = draft_files[0]
        print(f"Found 1 draft file: {draft_file.name}")
        choice_index, chosen_option = get_numbered_choice(
            f"Select destination category for '{draft_file.name}':", dest_options
        )
        if choice_index is not None:
            destination_dir = dest_dirs[choice_index]
            moves_to_perform[draft_file] = destination_dir
        else:
            print("Move cancelled.")
            return # Back to main menu
    else:
        print(f"Found {len(draft_files)} draft files.")
        for draft_file in draft_files:
            print("-" * 20)
            choice_index, chosen_option = get_numbered_choice(
                f"Select destination category for '{draft_file.name}':", dest_options
            )
            if choice_index is not None:
                destination_dir = dest_dirs[choice_index]
                moves_to_perform[draft_file] = destination_dir
            else:
                print(f"Skipping move for '{draft_file.name}'.")
                # Ask if they want to cancel all moves?
                if not get_confirmation("Do you want to continue assigning destinations for other files? (No cancels all remaining moves)"):
                    print("Move operation cancelled.")
                    return # Back to main menu

    # --- Perform the moves ---
    if not moves_to_perform:
        print("No moves were scheduled.")
        return

    print("\n--- Performing Moves ---")
    success_count = 0
    fail_count = 0
    for source_path, dest_dir_path in moves_to_perform.items():
        dest_file_path = dest_dir_path / source_path.name
        try:
            print(f"Moving '{source_path.name}' -> '{dest_dir_path.name}/'")
            shutil.move(str(source_path), str(dest_file_path))
            success_count += 1
        except Exception as e:
            print(f"  ERROR moving '{source_path.name}': {e}")
            fail_count += 1

    print("-" * 20)
    print(f"Move complete. Success: {success_count}, Failed: {fail_count}.")
    # Script exits after moving as per prompt
    print("Exiting script.")
    sys.exit()

def choice_4_build_deploy(project_root):
    """Handles Choice 4: Test Build and deploy website."""
    print("\n--- Test Build and Deploy Website ---")
    command = "npx @11ty/eleventy --serve"
    print(f"Running command: {command}")
    print("Working directory:", project_root)
    print("Press Ctrl+C in the Eleventy terminal window to stop serving.")

    try:
        # Run the command. subprocess.run waits for completion by default.
        # Use shell=True cautiously, especially if inputs were involved in the command.
        # It might be needed for 'npx' resolution on some systems (like Windows).
        process = subprocess.run(command, cwd=project_root, shell=True)
        print(f"\nEleventy process finished with exit code: {process.returncode}")

    except FileNotFoundError:
        print("\nError: 'npx' command not found.")
        print("Please ensure Node.js and npm/npx are installed and in your system's PATH.")
    except Exception as e:
        print(f"\nAn error occurred while running Eleventy: {e}")
    except KeyboardInterrupt:
        print("\nEleventy process interrupted by user (Ctrl+C detected in Python script).")

    # The script should exit after the command finishes or is interrupted.
    print("Exiting script.")
    sys.exit()


# --- Main Script ---
if __name__ == "__main__":
    if not check_and_install_pyyaml():
        sys.exit(1) # Exit if PyYAML installation failed

    # Now that PyYAML is guaranteed to be installed (or script exited), import it safely
    import yaml

    project_root = find_project_root()
    print(f"Detected project root: {project_root}")

    while True:
        # Find content dir fresh each time in case it's created by Choice 1
        content_dir = find_directory(project_root, CONTENT_DIR_NAME)

        print("\n" + "=" * 30)
        print(" Eleventy Helper Script")
        print("=" * 30)
        main_choices = [
            "Draft a new post in a category folder",
            "Make a new draft in the drafts folder",
            "Move my drafts to post categories",
            "Test Build and serve website",
            "Exit"
        ]
        print("Select an action:")
        for i, choice_text in enumerate(main_choices):
             print(f"{i + 1}. {choice_text}")

        try:
            main_choice_num = input("Enter your choice number: ").strip()

            if main_choice_num == '1':
                choice_1_new_post_category(project_root, content_dir)
                # Choice 1 either exits or returns here implicitly if user didn't exit
            elif main_choice_num == '2':
                choice_2_new_draft(project_root)
                # Choice 2 either exits or returns here to loop/exit based on user prompt
            elif main_choice_num == '3':
                choice_3_move_drafts(project_root, content_dir)
                # Choice 3 always exits
            elif main_choice_num == '4':
                choice_4_build_deploy(project_root)
                # Choice 4 always exits
            elif main_choice_num == '5':
                print("Exiting script.")
                break # Exit the main loop
            else:
                print("Invalid choice. Please enter a number from the list.")

        except ValueError:
            print("Invalid input. Please enter a number.")
        except EOFError:
            print("\nOperation cancelled. Exiting.")
            break
        except KeyboardInterrupt:
             print("\nOperation interrupted by user. Exiting.")
             break

        # Add a small pause before showing the menu again unless exiting
        if main_choice_num != '5':
            print("\nReturning to main menu...")
            # time.sleep(1) # Optional short pause