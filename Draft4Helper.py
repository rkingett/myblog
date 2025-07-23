import os
import sys
import subprocess
import datetime
import platform
import shutil
import time
from pathlib import Path

# --- Configuration ---
# --- EDIT THESE VALUES TO MATCH YOUR SETUP ---
CONTENT_DIR_NAME = "content"
DRAFTS_DIR_NAME = "drafts"
DIST_DIR_NAME = "DistSite"  # Default Eleventy output folder. Change if Mine is different (e.g., "dist").
RCLONE_REMOTE_NAME = "nfs:"  # The name of your rclone remote (e.g., "live_server:").
GIT_COMMIT_MESSAGE = "Updated site pages and posts"
SITE_URL = "https://sightlessscribbles.com" # URL to open after deployment
# --- END OF CONFIGURATION ---

EXCLUDE_DIRS = {'feed', 'feeds', 'helper', 'helpers'}  # Directories to exclude from choices

# --- Helper Functions ---

def check_and_install_pyyaml():
    """Checks if PyYAML is installed and installs it if not."""
    try:
        import yaml
        return True
    except ImportError:
        print("PyYAML not found. Attempting to install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "PyYAML"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("PyYAML installed successfully.")
            global yaml
            import yaml
            return True
        except (subprocess.CalledProcessError, Exception) as e:
            print(f"Error: Failed to install PyYAML automatically: {e}")
            print("Please install it manually by running: pip install PyYAML")
            return False

def run_command(command, cwd, error_message):
    """Runs a command in a specified directory and handles errors."""
    try:
        print(f"Running: {' '.join(command)}")
        subprocess.run(command, cwd=cwd, check=True, shell=platform.system() == "Windows")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error: {error_message}")
        print(f"Details: {e}")
        return False

def get_confirmation(prompt):
    """Gets user confirmation (1 for Yes, 2 for No)."""
    while True:
        choice = input(f"{prompt} (1: Yes, 2: No): ").strip()
        if choice == '1':
            return True
        elif choice == '2':
            return False
        print("Invalid input. Please enter 1 for Yes or 2 for No.")

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
            choice_index = int(input("Enter your choice number: ").strip()) - 1
            if 0 <= choice_index < len(options):
                chosen_option = options[choice_index]
                if get_confirmation(f"You selected: '{chosen_option}'. Confirm?"):
                    return choice_index, chosen_option
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(options)}.")
        except (ValueError, EOFError):
            print("Invalid input. Please enter a number.")
            return None, None

def get_valid_input(prompt):
    """Gets non-empty input from the user."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Input cannot be empty.")

def get_iso_datetime():
    """Returns the current datetime in ISO 8601 format."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def find_project_root():
    """Assumes the script is run from the project root."""
    return Path.cwd()

def get_valid_subdirectories(parent_dir):
    """Gets a list of valid subdirectories, excluding specified names."""
    if not parent_dir or not parent_dir.is_dir():
        return []
    return [item for item in parent_dir.iterdir() if item.is_dir() and item.name.lower() not in EXCLUDE_DIRS]

def extract_yaml_front_matter(filepath: Path):
    """Reads a file and extracts YAML front matter if present."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        if not lines or not lines[0].strip() == "---":
            return None
        yaml_lines = []
        in_yaml = False
        for i, line_content in enumerate(lines):
            stripped_line = line_content.strip()
            if i == 0 and stripped_line == "---":
                in_yaml = True
                continue
            if in_yaml:
                if stripped_line == "---":
                    break
                yaml_lines.append(line_content)
        if not yaml_lines:
            return None
        return yaml.safe_load("".join(yaml_lines))
    except Exception:
        return None

def get_title_from_md_file(filepath: Path):
    """Extracts the title from a markdown file's YAML front matter."""
    front_matter = extract_yaml_front_matter(filepath)
    if front_matter and isinstance(front_matter, dict) and 'title' in front_matter:
        return str(front_matter['title'])
    return filepath.name

def create_md_file(filepath, title, tags_list, date_iso):
    """Creates the markdown file with YAML front matter."""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        front_matter = {
            'title': QuotedString(title),
            'date': date_iso,
            'tags': FlowStyleList(tags_list if tags_list else [])
        }
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
    except Exception as e:
        print(f"Error opening {path_str}: {e}")

# --- Main Choices ---

def choice_1_new_post_category(project_root):
    """Handles Choice 1: Draft a new post in a category folder."""
    print("\n--- Draft a new post in a category folder ---")
    content_dir = project_root / CONTENT_DIR_NAME
    if not content_dir.is_dir():
        print(f"Error: Content directory ('{CONTENT_DIR_NAME}') not found.")
        return

    subdirs = get_valid_subdirectories(content_dir)
    dir_options = [d.name for d in subdirs] + ["Create a new category folder"]
    _, chosen_option = get_numbered_choice("Select the category:", dir_options)
    if not chosen_option:
        return

    target_dir = None
    if chosen_option == "Create a new category folder":
        new_dir_name = get_valid_input("Enter the name for the new category folder: ")
        if any(c in r'<>:"/\|?*' for c in new_dir_name):
            print("Invalid folder name.")
            return
        target_dir = content_dir / new_dir_name
        target_dir.mkdir(parents=True, exist_ok=True)
    else:
        target_dir = content_dir / chosen_option

    post_title = get_valid_input("Enter the post title: ")
    tags_input = get_valid_input("Enter tags, separated by commas: ")
    tags_list = [tag.strip() for tag in tags_input.split(',') if tag.strip()]

    filename = f"{datetime.datetime.now().strftime('%Y%m%d')}.md"
    filepath = target_dir / filename
    counter = 1
    while filepath.exists():
        filename = f"{datetime.datetime.now().strftime('%Y%m%d')}_{counter}.md"
        filepath = target_dir / filename
        counter += 1

    if create_md_file(filepath, post_title, tags_list, get_iso_datetime()):
        if get_confirmation("Do you want to open the new file?"):
            open_file_or_folder(filepath)

def choice_2_move_drafts(project_root):
    """Handles Choice 2: Move drafts to post categories."""
    print("\n--- Move drafts to post categories ---")
    drafts_dir = project_root / DRAFTS_DIR_NAME
    content_dir = project_root / CONTENT_DIR_NAME

    if not drafts_dir.is_dir():
        print(f"Drafts directory ('{DRAFTS_DIR_NAME}') not found.")
        return
    draft_files = [f for f in drafts_dir.iterdir() if f.is_file() and f.suffix.lower() == '.md']
    if not draft_files:
        print("No markdown drafts found.")
        return
    dest_dirs = get_valid_subdirectories(content_dir)
    if not dest_dirs:
        print(f"No destination folders found in '{CONTENT_DIR_NAME}'.")
        return

    dest_options = [d.name for d in dest_dirs]
    for draft_file in draft_files:
        post_title = get_title_from_md_file(draft_file)
        prompt = f"Select destination for draft: \"{post_title}\" (file: {draft_file.name}):"
        choice_index, _ = get_numbered_choice(prompt, dest_options)
        if choice_index is not None:
            destination_dir = dest_dirs[choice_index]
            try:
                print(f"Moving '{draft_file.name}' to '{destination_dir.name}'...")
                shutil.move(str(draft_file), str(destination_dir / draft_file.name))
                print("Move successful.")
            except Exception as e:
                print(f"Error moving file: {e}")
        else:
            print(f"Skipping move for '{post_title}'.")

def choice_3_test_build(project_root):
    """Handles Choice 3: Test Build and serve website locally."""
    print("\n--- Test Build and Serve Locally ---")
    print("Press Ctrl+C in the terminal to stop the server.")
    if not run_command(["npx", "@11ty/eleventy", "--serve"], project_root, "Failed to start Eleventy server."):
        print("Please ensure Node.js and npx are installed and in your system's PATH.")

def choice_4_build_and_deploy(project_root):
    """Handles Choice 4: Build and Deploy to Live Server."""
    print("\n" + "="*40)
    print("  🚀 STARTING BUILD AND DEPLOYMENT 🚀")
    print("="*40)
    if not get_confirmation("This will delete remote content and push to Git. Are you sure?"):
        print("Deployment cancelled.")
        return

    dist_path = project_root / DIST_DIR_NAME
    rclone_remote_path = f"{RCLONE_REMOTE_NAME.rstrip(':')}:"

    # --- Step 1: Clean local and remote directories ---
    print("\n--- Step 1: Cleaning Directories ---")
    if dist_path.exists():
        print(f"Deleting local build directory: {dist_path}")
        shutil.rmtree(dist_path)
    if not run_command(["rclone", "delete", rclone_remote_path, "--rmdirs"], project_root, f"Failed to delete remote directory '{rclone_remote_path}'."):
        return

    # --- Step 2: Build the site ---
    print("\n--- Step 2: Building with Eleventy ---")
    if not run_command(["npx", "@11ty/eleventy", "--quiet"], project_root, "Eleventy build failed."):
        return

    # --- Step 3: Git Version Control ---
    print("\n--- Step 3: Committing to Git ---")
    if not run_command(["git", "add", "."], project_root, "Failed to stage files with 'git add'."):
        return
    if not run_command(["git", "commit", "-m", GIT_COMMIT_MESSAGE], project_root, "Failed to commit changes. Nothing to commit or git error."):
        # This might fail if there are no changes, which is okay. We can continue.
        print("Warning: 'git commit' failed. This is okay if there were no new changes to commit.")
    if not run_command(["git", "push"], project_root, "Failed to push to remote Git repository."):
        return

    # --- Step 4: Deploy to Remote Server ---
    print("\n--- Step 4: Deploying to Remote Server ---")
    if not run_command(["rclone", "copy", str(dist_path), rclone_remote_path, "--progress"], project_root, "Failed to copy files with rclone."):
        return

    # --- Step 5: Finalization ---
    print("\n" + "="*40)
    print("  ✅ DEPLOYMENT COMPLETE! ✅")
    print("="*40)
    if get_confirmation(f"Do you want to open {SITE_URL} in your browser?"):
        open_file_or_folder(SITE_URL)

    print("\nExiting script.")
    sys.exit()


# --- Main Script ---
if __name__ == "__main__":
    if not check_and_install_pyyaml():
        sys.exit(1)
    import yaml

    # Define custom YAML types for formatting
    class QuotedString(str): pass
    def quoted_string_representer(dumper, data):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')
    yaml.add_representer(QuotedString, quoted_string_representer, Dumper=yaml.Dumper)

    class FlowStyleList(list): pass
    def flow_style_list_representer(dumper, data):
        return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)
    yaml.add_representer(FlowStyleList, flow_style_list_representer, Dumper=yaml.Dumper)

    globals()['QuotedString'] = QuotedString
    globals()['FlowStyleList'] = FlowStyleList

    project_root = find_project_root()
    print(f"Detected project root: {project_root}")

    while True:
        print("\n" + "=" * 30)
        print(" Eleventy Helper Script")
        print("=" * 30)
        main_choices = [
            "Draft a new post in a category",
            "Move drafts to post categories",
            "Test build and serve locally",
            "Build and Deploy to Live Server",
            "Exit"
        ]
        print("Select an action:")
        for i, choice_text in enumerate(main_choices):
             print(f"{i + 1}. {choice_text}")

        try:
            main_choice_num = input("Enter your choice number: ").strip()
            if main_choice_num == '1':
                choice_1_new_post_category(project_root)
            elif main_choice_num == '2':
                choice_2_move_drafts(project_root)
            elif main_choice_num == '3':
                choice_3_test_build(project_root)
            elif main_choice_num == '4':
                choice_4_build_and_deploy(project_root)
            elif main_choice_num == '5':
                print("Exiting script.")
                break
            else:
                print("Invalid choice. Please enter a number from the list.")
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled. Exiting.")
            break
