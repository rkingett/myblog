import os
import sys
import subprocess
import datetime
import platform
import shutil
import time
from pathlib import Path
# PyYAML will be imported conditionally later, and then properly in __main__
# import yaml # Keep this for static analysis if preferred, but logic handles it

# --- Configuration ---
CONTENT_DIR_NAME = "content"
DRAFTS_DIR_NAME = "drafts"
EXCLUDE_DIRS = {'feed', 'feeds', 'helper', 'helpers'} # Directories to exclude from choices

# --- Helper Functions ---

def check_and_install_pyyaml():
    """Checks if PyYAML is installed and installs it if not."""
    try:
        import yaml # Attempt to import
        print("PyYAML is already installed.")
        return True
    except ImportError:
        print("PyYAML not found. Attempting to install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "--version"])
            subprocess.check_call([sys.executable, "-m", "pip", "install", "PyYAML"])
            print("PyYAML installed successfully.")
            # Make yaml available globally for this session if installed here
            # The __main__ block will re-import it properly.
            global yaml
            import yaml
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error installing PyYAML: {e}")
            print("It failed installing so install PyYAML manually using: pip install PyYAML")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during installation: {e}")
            print("It failed installing automatically so install PyYAML manually using: pip install PyYAML")
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

# New helper function to extract YAML front matter from a file
def extract_yaml_front_matter(filepath: Path):
    """Reads a file and extracts YAML front matter if present."""
    try:
        # This local import is fine as yaml module will be loaded by __main__
        import yaml
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if not lines or not lines[0].strip() == "---":
            # print(f"Debug: No YAML front matter start in {filepath}")
            return None

        yaml_lines = []
        in_yaml = False
        # Start from the first line, check for "---"
        for i, line_content in enumerate(lines):
            stripped_line = line_content.strip()
            if i == 0 and stripped_line == "---":
                in_yaml = True
                continue
            if in_yaml:
                if stripped_line == "---": # End of YAML block
                    break
                yaml_lines.append(line_content)
            elif i > 0 : # If first line was not ---, then no frontmatter
                return None


        if not yaml_lines:
            # print(f"Debug: Empty YAML block in {filepath}")
            return None

        yaml_content = "".join(yaml_lines)
        front_matter_data = yaml.safe_load(yaml_content)
        return front_matter_data
    except FileNotFoundError:
        # print(f"Debug: File not found {filepath}")
        return None
    except Exception as e:
        # print(f"Debug: Error parsing YAML from {filepath}: {e}")
        return None

# New helper function to get title from markdown file
def get_title_from_md_file(filepath: Path):
    """Extracts the title from a markdown file's YAML front matter."""
    front_matter = extract_yaml_front_matter(filepath)
    if front_matter and isinstance(front_matter, dict) and 'title' in front_matter:
        # Ensure the title is returned as a string, even if it was a number or other type in YAML
        return str(front_matter['title'])
    return filepath.name # Fallback to filename

def create_md_file(filepath, title, tags_list, date_iso):
    """Creates the markdown file with YAML front matter."""
    # This local import is fine as yaml module will be loaded by __main__
    # and custom representers registered there.
    import yaml

    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Use QuotedString for title and FlowStyleList for tags
        # These classes (QuotedString, FlowStyleList) are defined and registered in __main__
        front_matter = {
            'title': QuotedString(title), # MODIFIED: Use QuotedString wrapper
            'date': date_iso,
            # MODIFIED: Use FlowStyleList wrapper, ensure it's an empty list if tags_list is None or empty
            'tags': FlowStyleList(tags_list if tags_list else [])
        }
        # MODIFIED: Use yaml.Dumper and default_flow_style=False
        # Custom representers will handle specific formatting for title and tags.
        yaml_string = yaml.dump(front_matter, Dumper=yaml.Dumper, default_flow_style=False, sort_keys=False)

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


# --- Main Choices ---

def choice_1_new_post_category(project_root, content_dir):
    """Handles Choice 1: Draft a new post in a category folder."""
    print("\n--- Draft a new post in a category folder ---")
    if not content_dir:
        print(f"Error: Content directory ('{CONTENT_DIR_NAME}') not found in {project_root}")
        return

    while True:
        subdirs = get_valid_subdirectories(content_dir, EXCLUDE_DIRS)
        dir_options = [d.name for d in subdirs]
        dir_options.append("Create a new category folder")

        choice_index, chosen_option = get_numbered_choice(
            "Select the category (output directory):", dir_options
        )

        if choice_index is None:
             print("Operation cancelled.")
             return

        target_dir = None
        if chosen_option == "Create a new category folder":
            while True:
                new_dir_name = get_valid_input("Enter the name for the new category folder: ")
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
        print("Failed to create post file.")
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
        print("Failed to create draft file.")
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
            print(f"Error: Content directory ('{CONTENT_DIR_NAME}') not found. Cannot move file.")
            print("Opening drafts folder for manual moving...")
            open_file_or_folder(drafts_dir)
        else:
            while True:
                subdirs = get_valid_subdirectories(content_dir, EXCLUDE_DIRS)
                if not subdirs:
                     print(f"No suitable category folders found in '{content_dir.name}'.")
                     print("Opening drafts folder for manual moving...")
                     open_file_or_folder(drafts_dir)
                     break

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
        print(f"Error: Content directory ('{CONTENT_DIR_NAME}') not found. Cannot select destinations.")
        return

    dest_dirs = get_valid_subdirectories(content_dir, EXCLUDE_DIRS)
    if not dest_dirs:
        print(f"No suitable destination folders found in '{content_dir.name}'. Cannot move drafts.")
        return
    dest_options = [d.name for d in dest_dirs]

    moves_to_perform = {}

    # MODIFIED: Iterate through draft files, get their titles, and prompt user
    print(f"Found {len(draft_files)} draft file(s).")
    for draft_file_path in draft_files:
        post_title = get_title_from_md_file(draft_file_path) # Get title, fallback to filename
        
        print("-" * 20)
        # Use post_title (which might be filename if title extraction failed) in prompt
        choice_index, chosen_dest_name = get_numbered_choice(
            f"Select destination category for draft: \"{post_title}\" (file: {draft_file_path.name}):",
            dest_options
        )

        if choice_index is not None:
            destination_dir = dest_dirs[choice_index]
            moves_to_perform[draft_file_path] = destination_dir
        else:
            print(f"Skipping move for draft: \"{post_title}\".")
            if not get_confirmation("Do you want to continue assigning destinations for other files? (No cancels all remaining moves)"):
                print("Move operation cancelled.")
                return

    if not moves_to_perform:
        print("No moves were scheduled.")
        return

    print("\n--- Performing Moves ---")
    success_count = 0
    fail_count = 0
    for source_path, dest_dir_path in moves_to_perform.items():
        dest_file_path = dest_dir_path / source_path.name
        try:
            post_title_display = get_title_from_md_file(source_path) # For display
            print(f"Moving \"{post_title_display}\" ('{source_path.name}') -> '{dest_dir_path.name}/'")
            shutil.move(str(source_path), str(dest_file_path))
            success_count += 1
        except Exception as e:
            print(f"  ERROR moving '{source_path.name}': {e}")
            fail_count += 1

    print("-" * 20)
    print(f"Move complete. Success: {success_count}, Failed: {fail_count}.")
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
        print("\nError: 'npx' command not found.")
        print("Please ensure Node.js and npm/npx are installed and in your system's PATH.")
    except Exception as e:
        print(f"\nAn error occurred while running Eleventy: {e}")
    except KeyboardInterrupt:
        print("\nEleventy process interrupted by user (Ctrl+C detected in Python script).")

    print("Exiting script.")
    sys.exit()


# --- Main Script ---
if __name__ == "__main__":
    # Step 1: Ensure PyYAML is installed
    if not check_and_install_pyyaml():
        sys.exit(1)

    # Step 2: Now that PyYAML is installed (or was already), import it for use.
    import yaml

    # Step 3: Define custom types and add representers to the imported 'yaml' module.
    # These classes need to be available for create_md_file.
    # If create_md_file is called, it will use these definitions.

    class QuotedString(str):
        """A string subclass that PyYAML will represent with double quotes."""
        pass

    def quoted_string_representer(dumper, data):
        """PyYAML representer for QuotedString."""
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

    yaml.add_representer(QuotedString, quoted_string_representer, Dumper=yaml.Dumper)
    yaml.add_representer(QuotedString, quoted_string_representer, Dumper=yaml.SafeDumper)


    class FlowStyleList(list):
        """A list subclass that PyYAML will represent in flow style (e.g., [item1, item2])."""
        pass

    def flow_style_list_representer(dumper, data):
        """PyYAML representer for FlowStyleList."""
        return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)

    yaml.add_representer(FlowStyleList, flow_style_list_representer, Dumper=yaml.Dumper)
    yaml.add_representer(FlowStyleList, flow_style_list_representer, Dumper=yaml.SafeDumper)
    
    # Make QuotedString and FlowStyleList globally available if create_md_file needs them
    # This is a bit of a workaround for them being defined inside if __name__ == "__main__"
    # but used by create_md_file which is top-level.
    # A cleaner way would be to pass dumper configurations or have these classes defined top-level.
    # For now, functions like create_md_file import yaml locally, and the representers are registered
    # on the module itself, so it should work.
    # To be absolutely sure, we can assign them to globals for create_md_file to see.
    # This is generally not ideal but works for a single script file.
    globals()['QuotedString'] = QuotedString
    globals()['FlowStyleList'] = FlowStyleList


    project_root = find_project_root()
    print(f"Detected project root: {project_root}")

    while True:
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
            elif main_choice_num == '2':
                choice_2_new_draft(project_root)
            elif main_choice_num == '3':
                choice_3_move_drafts(project_root, content_dir)
            elif main_choice_num == '4':
                choice_4_build_deploy(project_root)
            elif main_choice_num == '5':
                print("Exiting script.")
                break
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

        if main_choice_num != '5':
            print("\nReturning to main menu...")
            # time.sleep(1) # Optional