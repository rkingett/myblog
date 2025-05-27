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

# --- Global placeholder for yaml module and its components ---
yaml_module = None # Renamed to avoid conflict with 'yaml' variable name if used locally
DoubleQuotedScalarString_type = None # Renamed for clarity

# --- Helper Functions ---

def check_pyyaml_installed():
    """
    Checks if PyYAML and its necessary submodules are accessible.
    Sets global 'yaml_module' and 'DoubleQuotedScalarString_type' if successful.
    If not, informs the user to install it manually.
    """
    global yaml_module, DoubleQuotedScalarString_type
    try:
        import yaml as yml_temp
        from yaml.scalarstring import DoubleQuotedScalarString as dq_temp
        
        yaml_module = yml_temp
        DoubleQuotedScalarString_type = dq_temp
        # print("PyYAML is installed and accessible.") # Keep commented unless debugging
        return True
    except ImportError:
        print("-" * 60)
        print("ERROR: PyYAML (Python YAML library) is not found or not fully accessible.")
        print("This script requires PyYAML to function correctly.")
        print("Please install it manually in your Python environment.")
        print("You can typically do this by running:")
        print(f"  {sys.executable} -m pip install PyYAML")
        print("-" * 60)
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
        return None, None 

    while True:
        print(prompt)
        for i, option in enumerate(options):
            print(f"{i + 1}. {option}")

        try:
            choice = input("Enter your choice number: ").strip()
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(options):
                chosen_option = options[choice_index]
                if get_confirmation(f"You selected: '{chosen_option}'. Confirm?"):
                    return choice_index, chosen_option
                else:
                    print("-" * 20) 
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
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def find_project_root():
    """Assumes the script is run from the project root."""
    return Path.cwd()

def find_directory(base_path, dir_name):
    """Finds a directory by name within the base path."""
    target_dir = base_path / dir_name
    if target_dir.is_dir():
        return target_dir
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
    if yaml_module is None or DoubleQuotedScalarString_type is None: 
        print("Error: PyYAML module not loaded correctly. Cannot create MD file.")
        print("Please ensure PyYAML is installed in your Python environment.")
        return False
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure title is quoted
        quoted_title = DoubleQuotedScalarString_type(title)
        
        front_matter = {
            'title': quoted_title,
            'date': date_iso,
            'tags': tags_list # PyYAML will handle list representation
        }
        
        # To achieve tags: ["tag1", "tag2"] (flow style for the list specifically)
        # while keeping the overall structure block style, we can define a custom representer
        # or set default_flow_style=None and rely on PyYAML's behavior for simple lists.
        # Forcing flow style for the entire YAML block with default_flow_style=True:
        # yaml_string = yaml_module.dump(front_matter, default_flow_style=True, sort_keys=False, allow_unicode=True)
        # This would make it: {title: "My Title", date: "...", tags: ["tag1", "tag2"]}
        #
        # To get block style for the main map but flow style for the tags list:
        # This is the most common desired output for front matter:
        # title: "My Title"
        # date: ...
        # tags:
        #   - tag1
        #   - tag2
        # This is achieved with default_flow_style=False (or None)
        #
        # If the request is strictly for `tags: ["tag1", "tag2"]` on one line within a block-style map:
        
        class FlowListRepresenter(yaml_module.SafeRepresenter):
            def represent_list(self, data):
                return super().represent_list(data, flow_style=True)

        yaml_string = yaml_module.dump(
            front_matter, 
            Representer=FlowListRepresenter, 
            default_flow_style=False, # Main structure block style
            sort_keys=False, 
            allow_unicode=True
        )

        content = f"---\n{yaml_string}---\n\n<!-- Your post content starts here -->\n"
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
            os.startfile(path_str)
        elif platform.system() == "Darwin": 
            subprocess.run(['open', path_str], check=True)
        else: 
            subprocess.run(['xdg-open', path_str], check=True)
        time.sleep(1) 
        return True
    except FileNotFoundError:
         print(f"Error: Path not found - {path_str}")
         return False
    except Exception as e:
        print(f"Error opening {path_str}: {e}")
        return False

def attempt_open_and_wait(filepath):
    """Attempts to open a file with the default editor and waits."""
    filepath_str = str(filepath)
    print(f"Attempting to open '{filepath_str}' in default editor...")
    editor_opened = False
    try:
        if platform.system() == "Windows":
            os.startfile(filepath_str)
            editor_opened = True
            print("File opened. Waiting requires manual confirmation (press Enter)...")
            input("Press Enter after you have saved and closed the file...")
        elif platform.system() == "Darwin": 
            subprocess.run(['open', '-W', filepath_str], check=True)
            editor_opened = True
            print("Editor closed.")
        else: 
            subprocess.run(['xdg-open', filepath_str], check=True)
            editor_opened = True
            print("File opened. Waiting requires manual confirmation (press Enter)...")
            input("Press Enter after you have saved and closed the file...")
    except FileNotFoundError:
         print(f"Error: File not found - {filepath_str}")
    except subprocess.CalledProcessError as e:
        print(f"Error opening file with waiting: {e}")
        print("Falling back to simple open...")
        editor_opened = open_file_or_folder(filepath)
    except Exception as e:
        print(f"An unexpected error occurred while opening editor: {e}")
        print("Attempting simple open...")
        editor_opened = open_file_or_folder(filepath)

    if editor_opened and platform.system() != "Darwin": 
         time.sleep(1)
    return editor_opened

def choice_1_new_post_category(project_root, content_dir):
    """Handles Choice 1: Draft a new post in a category folder."""
    print("\n--- Draft a new post in a category folder ---")
    if not content_dir:
        content_dir_path = project_root / CONTENT_DIR_NAME
        try:
            print(f"Content directory ('{CONTENT_DIR_NAME}') not found. Attempting to create it...")
            content_dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Content directory '{CONTENT_DIR_NAME}' created at {content_dir_path}")
            content_dir = content_dir_path
        except Exception as e:
            print(f"Error: Content directory ('{CONTENT_DIR_NAME}') not found and could not be created in {project_root}: {e}")
            return

    while True: 
        subdirs = get_valid_subdirectories(content_dir, EXCLUDE_DIRS)
        dir_options = [d.name for d in subdirs]
        dir_options.append("Create a new category folder")
        choice_index, chosen_option = get_numbered_choice("Select the category (output directory):", dir_options)

        if choice_index is None:
             print("Operation cancelled.")
             return

        target_dir = None
        if chosen_option == "Create a new category folder":
            while True:
                new_dir_name = get_valid_input("Enter the name for the new category folder: ")
                if new_dir_name.lower() in EXCLUDE_DIRS:
                     print(f"Folder name '{new_dir_name}' matches a reserved name. Please choose a different name.")
                     continue
                if not new_dir_name or any(c in r'<>:"/\|?*' for c in new_dir_name): 
                    print("Invalid folder name. Avoid special characters: <>:\"/\\|?* and ensure it's not empty.")
                    continue
                target_dir = content_dir / new_dir_name
                try:
                    target_dir.mkdir(parents=True, exist_ok=False)
                    print(f"Folder '{target_dir.name}' created successfully.")
                    break
                except FileExistsError:
                    print(f"Folder '{target_dir.name}' already exists. Please choose a different name or select the existing folder.")
                    target_dir = None 
                    break 
                except Exception as e:
                    print(f"Error creating folder: {e}")
                    target_dir = None 
                    break
            if target_dir is None: 
                 continue
        else:
            target_dir = subdirs[choice_index]
        if target_dir: 
            break

    post_title = get_valid_input("Enter the post title: ") 
    tags_input = get_valid_input("Enter tags, separated by commas (e.g., tech, blog, javascript): ")
    tags_list = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
    current_time_iso = get_iso_datetime()
    file_date_str = datetime.datetime.now().strftime("%Y%m%d")
    filename = f"{file_date_str}.md"
    filepath = target_dir / filename
    counter = 1
    while filepath.exists():
        filename = f"{file_date_str}_{counter}.md"
        filepath = target_dir / filename
        counter += 1

    if not create_md_file(filepath, post_title, tags_list, current_time_iso):
        return

    if get_confirmation("Do you want to open the new file in your editor?"):
        attempt_open_and_wait(filepath) 
        print("Opening project folder...")
        open_file_or_folder(project_root)
    else:
        print("Opening project folder...")
        open_file_or_folder(project_root)
        print("Exiting script.")
        sys.exit()

def choice_2_new_draft(project_root):
    """Handles Choice 2: Make a new draft in the drafts folder."""
    print("\n--- Make a new draft in the drafts folder ---")
    drafts_dir = project_root / DRAFTS_DIR_NAME
    try:
        drafts_dir.mkdir(parents=True, exist_ok=True)
        print(f"Ensured drafts directory exists: {drafts_dir}")
    except Exception as e:
        print(f"Error creating/accessing drafts directory '{drafts_dir}': {e}")
        return

    post_title = get_valid_input("Enter the draft title: ") 
    tags_input = get_valid_input("Enter tags, separated by commas (e.g., idea, wip): ")
    tags_list = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
    current_time_iso = get_iso_datetime()
    file_date_str = datetime.datetime.now().strftime("%Y%m%d")
    filename = f"{file_date_str}.md"
    filepath = drafts_dir / filename
    counter = 1
    while filepath.exists():
        filename = f"{file_date_str}_{counter}.md"
        filepath = drafts_dir / filename
        counter += 1

    if not create_md_file(filepath, post_title, tags_list, current_time_iso):
        return

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
        print("Opening project folder...")
        open_file_or_folder(project_root)
        print("Exiting script.")
        sys.exit()

    if move_file_after_edit:
        content_dir = find_directory(project_root, CONTENT_DIR_NAME)
        if not content_dir: 
            content_dir_path = project_root / CONTENT_DIR_NAME
            print(f"Content directory ('{CONTENT_DIR_NAME}') not found for move. Attempting to create it...")
            try:
                content_dir_path.mkdir(parents=True, exist_ok=True)
                print(f"Content directory '{CONTENT_DIR_NAME}' created at {content_dir_path}")
                content_dir = content_dir_path
            except Exception as e:
                print(f"Error: Content directory ('{CONTENT_DIR_NAME}') not found and could not be created: {e}")
                print("Opening drafts folder for manual moving...")
                open_file_or_folder(drafts_dir)
        
        if content_dir: 
            while True: 
                subdirs = get_valid_subdirectories(content_dir, EXCLUDE_DIRS)
                if not subdirs:
                     print(f"No suitable category folders found in '{content_dir.name}'.")
                     print("Opening drafts folder for manual moving...")
                     open_file_or_folder(drafts_dir)
                     break 
                dir_options = [d.name for d in subdirs]
                choice_index, chosen_option = get_numbered_choice(f"Select destination category for '{filepath.name}':", dir_options)
                if choice_index is not None:
                    destination_dir = subdirs[choice_index]
                    destination_path = destination_dir / filepath.name
                    if destination_path.exists():
                        if not get_confirmation(f"File '{destination_path.name}' already exists in '{destination_dir.name}'. Overwrite?"):
                            print("Move cancelled to avoid overwrite.")
                            if not get_confirmation("Try choosing a different destination?"):
                                print("Skipping move. Opening drafts folder...")
                                open_file_or_folder(drafts_dir)
                                break 
                            else:
                                continue         
                    try:
                        print(f"Moving '{filepath.name}' to '{destination_dir.name}'...")
                        shutil.move(str(filepath), str(destination_path))
                        print("Move successful.")
                        break 
                    except Exception as e:
                        print(f"Error moving file: {e}")
                        if not get_confirmation("Move failed. Try choosing a destination again?"):
                             print("Skipping move. Opening drafts folder...")
                             open_file_or_folder(drafts_dir)
                             break 
                else: 
                    print("Move cancelled. Opening drafts folder...")
                    open_file_or_folder(drafts_dir)
                    break 
    elif editor_opened_successfully: 
        print("Opening drafts folder for manual moving...")
        open_file_or_folder(drafts_dir)

    if editor_opened_successfully: 
        if get_confirmation("Go back to the main menu? (No will exit)"):
            return 
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

    draft_files = [f for f in drafts_dir.iterdir() if f.is_file() and f.suffix.lower() == '.md']
    if not draft_files:
        print(f"No markdown files found in the drafts directory ('{drafts_dir.name}').")
        return

    if not content_dir:
        content_dir_path = project_root / CONTENT_DIR_NAME
        print(f"Content directory ('{CONTENT_DIR_NAME}') not found. Attempting to create it...")
        try:
            content_dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Content directory '{CONTENT_DIR_NAME}' created at {content_dir_path}")
            content_dir = content_dir_path
        except Exception as e:
            print(f"Error: Content directory ('{CONTENT_DIR_NAME}') not found and could not be created: {e}")
            print("Cannot proceed to move drafts without a content directory.")
            return
            
    dest_dirs = get_valid_subdirectories(content_dir, EXCLUDE_DIRS)
    if not dest_dirs:
        print(f"No suitable destination folders found in '{content_dir.name}'. Cannot move drafts.")
        print(f"You might need to create category folders inside '{content_dir.name}' first (e.g., using Option 1).")
        return
    dest_options_base = [d.name for d in dest_dirs]
    moves_to_perform = {} 

    if len(draft_files) == 1:
        draft_file = draft_files[0]
        print(f"Found 1 draft file: {draft_file.name}")
        choice_index, chosen_option = get_numbered_choice(f"Select destination category for '{draft_file.name}':", dest_options_base)
        if choice_index is not None:
            moves_to_perform[draft_file] = dest_dirs[choice_index]
        else:
            print("Move cancelled.")
            return 
    else: 
        print(f"Found {len(draft_files)} draft files.")
        for draft_file in draft_files:
            print("-" * 20)
            current_dest_options = dest_options_base + ["Skip this file"]
            choice_index, chosen_option = get_numbered_choice(f"Select destination category for '{draft_file.name}':", current_dest_options)
            if chosen_option == "Skip this file":
                print(f"Skipping move for '{draft_file.name}'.")
                continue 
            elif choice_index is not None: 
                moves_to_perform[draft_file] = dest_dirs[choice_index]
            else: 
                print(f"Skipping move for '{draft_file.name}'.")
                if not get_confirmation("Do you want to continue assigning destinations for other files? (No cancels all remaining moves)"):
                    print("Move operation cancelled.")
                    return 

    if not moves_to_perform:
        print("No moves were scheduled.")
        return

    print("\n--- Performing Moves ---")
    success_count, fail_count, skipped_overwrite = 0, 0, 0
    for source_path, dest_dir_path in moves_to_perform.items():
        dest_file_path = dest_dir_path / source_path.name
        try:
            if dest_file_path.exists():
                if get_confirmation(f"WARNING: File '{source_path.name}' already exists in '{dest_dir_path.name}'. Overwrite?"):
                    print(f"Moving and overwriting '{source_path.name}' -> '{dest_dir_path.name}/'")
                    shutil.move(str(source_path), str(dest_file_path))
                    success_count += 1
                else:
                    print(f"  SKIPPED (overwrite denied) moving '{source_path.name}' to '{dest_dir_path.name}/'")
                    skipped_overwrite += 1
            else:
                print(f"Moving '{source_path.name}' -> '{dest_dir_path.name}/'")
                shutil.move(str(source_path), str(dest_file_path))
                success_count += 1
        except Exception as e:
            print(f"  ERROR moving '{source_path.name}': {e}")
            fail_count += 1
    print("-" * 20)
    print(f"Move complete. Success: {success_count}, Failed: {fail_count}, Skipped (overwrite denied): {skipped_overwrite}.")
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
        process = subprocess.run(command, cwd=project_root, shell=True)
        print(f"\nEleventy process finished with exit code: {process.returncode}")
    except FileNotFoundError:
        print("\nError: 'npx' command not found. Ensure Node.js and npm/npx are in PATH.")
    except KeyboardInterrupt: 
        print("\nPython script interrupted. Eleventy process might still be running.")
    except Exception as e:
        print(f"\nAn error occurred while running Eleventy: {e}")
    print("Exiting script.")
    sys.exit()

# --- Main Script ---
if __name__ == "__main__":
    if not check_pyyaml_installed():
        sys.exit(1) 

    project_root = find_project_root()
    print(f"Detected project root: {project_root}")

    while True:
        content_dir = find_directory(project_root, CONTENT_DIR_NAME) 
        print("\n" + "=" * 30 + "\n Eleventy Helper Script\n" + "=" * 30)
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
            if main_choice_num == '1': choice_1_new_post_category(project_root, content_dir)
            elif main_choice_num == '2': choice_2_new_draft(project_root)
            elif main_choice_num == '3': choice_3_move_drafts(project_root, content_dir) 
            elif main_choice_num == '4': choice_4_build_deploy(project_root) 
            elif main_choice_num == '5':
                print("Exiting script.")
                break 
            else: print("Invalid choice. Please enter a number from the list.")
        except ValueError: print("Invalid input. Please enter a number.")
        except EOFError:
            print("\nOperation cancelled. Exiting.")
            break
        except KeyboardInterrupt:
             print("\nOperation interrupted by user. Exiting.")
             break

        if main_choice_num not in ['3', '4', '5']: 
            print("\nReturning to main menu...")
            # time.sleep(1) # Optional
