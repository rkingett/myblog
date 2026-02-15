# filename: eleventy_helper.py
# description: A comprehensive helper script for managing an Eleventy static site.
# features: Create new posts/drafts with evergreen URLs, move drafts, serve locally, and deploy.
# dependencies: PyYAML (auto-installs), git, npx (Node.js), rclone.

import os
import sys
import subprocess
import datetime
import platform
import shutil
import time
import webbrowser
import re
from pathlib import Path
from typing import Optional, List, Tuple, Dict

# --- Pre-flight Check for PyYAML ---
try:
    import yaml
except ImportError:
    print("PyYAML library not found. It is required for this script.")
    try:
        print("Attempting to install PyYAML via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyYAML"])
        print("PyYAML installed successfully.")
        import yaml
    except (subprocess.CalledProcessError, ImportError) as e:
        print(f"Failed to install PyYAML automatically: {e}", file=sys.stderr)
        print("Please install it manually by running: pip install PyYAML", file=sys.stderr)
        sys.exit(1)


# --- Configuration ---
class Config:
    """All user-configurable settings for the script."""
    # --- Directory Names ---
    CONTENT_DIR_NAME = "content"
    DRAFTS_DIR_NAME = "drafts"
    ELEVENTY_OUTPUT_DIR = "_site"

    # --- Content Settings ---
    EXCLUDE_DIRS = {'feed', 'feeds', 'helper', 'helpers'}
    # Defines the URL structure. {slug} is replaced by the sanitized post title.
    # Example: "/posts/{slug}/" or "/{slug}.html"
    PERMALINK_STYLE = "/posts/{slug}/"

    # --- Deployment Settings ---
    DEPLOY_CLEAN_REMOTE = True
    # The name of your rclone remote (e.g., "my-s3-remote:"). Must end with a colon.
    RCLONE_REMOTE_NAME = "nfs:"
    FINAL_WEBSITE_URL = "https://sightlessscribbles.com"
    DEFAULT_COMMIT_MESSAGE = "Content: Add or update posts"


# --- YAML Formatting Helpers ---
class QuotedString(str): pass
class FlowStyleList(list): pass

def setup_yaml():
    """Adds custom representers to PyYAML for clean front matter output."""
    def quoted_string_representer(dumper, data):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')
    def flow_style_list_representer(dumper, data):
        return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)
    yaml.add_representer(QuotedString, quoted_string_representer, Dumper=yaml.Dumper)
    yaml.add_representer(FlowStyleList, flow_style_list_representer, Dumper=yaml.Dumper)


# --- Core Helper Functions ---

def slugify(text: str) -> str:
    """Converts a string into a URL-friendly 'slug'."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text).strip('-')
    return text

def run_command(command: List[str], cwd: Path, check: bool = True) -> bool:
    """Runs a command, providing enhanced error reporting on failure."""
    command_str = ' '.join(command)
    print(f"\n> Running command: {command_str}")
    try:
        use_shell = platform.system() == "Windows"
        process = subprocess.run(
            command if not use_shell else command_str,
            cwd=cwd, check=check, shell=use_shell, text=True, capture_output=True
        )
        if process.stdout: print(process.stdout)
        if process.stderr: print(process.stderr, file=sys.stderr)
        return process.returncode == 0
    except FileNotFoundError:
        print(f"Error: Command '{command[0]}' not found.", file=sys.stderr)
        print("Please ensure it is installed and in your system's PATH.", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed with exit code {e.returncode}.", file=sys.stderr)
        if e.stdout: print(f"--- STDOUT ---\n{e.stdout}", file=sys.stderr)
        if e.stderr: print(f"--- STDERR ---\n{e.stderr}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return False

def get_confirmation(prompt: str) -> bool:
    """Gets user confirmation (1 for Yes, 2 for No)."""
    while True:
        try:
            choice = input(f"{prompt} (1: Yes, 2: No): ").strip()
            if choice == '1': return True
            elif choice == '2': return False
            print("Invalid input. Please enter 1 for Yes or 2 for No.")
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return False

def get_numbered_choice(prompt: str, options: List[str]) -> Optional[Tuple[int, str]]:
    """Presents numbered options and gets a valid choice."""
    if not options:
        print("No options available.")
        return None
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
                    print("-" * 20)
                    continue
            print(f"Invalid choice. Please enter a number between 1 and {len(options)}.")
        except (ValueError, EOFError, KeyboardInterrupt):
            print("\nOperation cancelled.")
            return None

def get_valid_input(prompt: str, default: str = "") -> str:
    """Gets non-empty input from the user, with an optional default."""
    while True:
        if default:
            value = input(f"{prompt} [default: {default}]: ").strip()
            return value or default
        else:
            value = input(prompt).strip()
            if value: return value
            print("Input cannot be empty.")

def get_iso_datetime() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def find_project_root() -> Path:
    return Path.cwd()

def get_valid_subdirectories(parent_dir: Path, exclude_names: set) -> List[Path]:
    if not parent_dir or not parent_dir.is_dir(): return []
    return sorted([
        item for item in parent_dir.iterdir()
        if item.is_dir() and item.name.lower() not in exclude_names
    ], key=lambda p: p.name.lower())


# --- File Content Functions ---

def extract_yaml_front_matter(filepath: Path) -> Optional[Dict]:
    try:
        with open(filepath, 'r', encoding='utf-8') as f: lines = f.readlines()
        if not lines or not lines[0].strip() == "---": return None
        yaml_lines = []
        in_yaml = False
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if i == 0 and stripped_line == "---":
                in_yaml = True
                continue
            if in_yaml:
                if stripped_line == "---": break
                yaml_lines.append(line)
        if not yaml_lines: return None
        return yaml.safe_load("".join(yaml_lines))
    except Exception:
        return None

def get_title_from_md_file(filepath: Path) -> str:
    front_matter = extract_yaml_front_matter(filepath)
    if front_matter and isinstance(front_matter, dict) and 'title' in front_matter:
        return str(front_matter['title'])
    return filepath.name

def create_md_file(filepath: Path, title: str, tags_list: List[str], date_iso: str, permalink: str) -> bool:
    """Creates the markdown file with YAML front matter including a permalink."""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        front_matter = {
            'title': QuotedString(title),
            'date': date_iso,
            'tags': FlowStyleList(tags_list if tags_list else []),
            'permalink': permalink
        }
        yaml_string = yaml.dump(front_matter, Dumper=yaml.Dumper, sort_keys=False)
        content = f"---\n{yaml_string}---\n\n<!-- Your post content starts here -->\n"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully created file: {filepath}")
        return True
    except Exception as e:
        print(f"Error creating file {filepath}: {e}", file=sys.stderr)
        return False


# --- File System Interaction ---

def open_file_with_editor(filepath: Path):
    """Attempts to open a file with the default editor and waits for it to close if possible."""
    print(f"Attempting to open '{filepath}' in default editor...")
    try:
        if platform.system() == "Darwin":
            subprocess.run(['open', '-W', str(filepath)], check=True)
            print("Editor closed.")
        else:
            if platform.system() == "Windows": os.startfile(filepath)
            else: subprocess.run(['xdg-open', str(filepath)], check=True)
            print("File opened. Waiting requires manual confirmation.")
            input("--> Press Enter after you have saved and closed the file... ")
    except Exception as e:
        print(f"Could not open file with editor: {e}", file=sys.stderr)

def open_path(path_to_open: Path):
    """Opens a file or folder using the default system application."""
    print(f"Attempting to open: {path_to_open}")
    try:
        if platform.system() == "Windows": os.startfile(path_to_open)
        elif platform.system() == "Darwin": subprocess.run(['open', str(path_to_open)], check=True)
        else: subprocess.run(['xdg-open', str(path_to_open)], check=True)
    except Exception as e:
        print(f"Error opening {path_to_open}: {e}", file=sys.stderr)


# --- Main Choices ---

def choice_1_new_post_category(project_root: Path, content_dir: Path):
    """Handles Choice 1: Draft a new post in a category folder."""
    print("\n--- Draft a new post in a category folder ---")
    if not content_dir:
        print(f"Error: Content directory ('{Config.CONTENT_DIR_NAME}') not found.", file=sys.stderr)
        return

    target_dir = None
    while not target_dir:
        subdirs = get_valid_subdirectories(content_dir, Config.EXCLUDE_DIRS)
        dir_options = [d.name for d in subdirs] + ["Create a new category folder"]
        choice = get_numbered_choice("Select the category (output directory):", dir_options)
        if not choice: return
        _, chosen_option = choice

        if chosen_option == "Create a new category folder":
            new_dir_name = get_valid_input("Enter the name for the new category folder: ")
            if new_dir_name.lower() in Config.EXCLUDE_DIRS:
                print(f"Error: '{new_dir_name}' is a reserved directory name.", file=sys.stderr)
                continue
            if any(c in r'<>:"/\|?*' for c in new_dir_name):
                print("Invalid folder name. Avoid special characters.")
                continue
            target_dir = content_dir / new_dir_name
            if target_dir.exists():
                print(f"Folder '{new_dir_name}' already exists. Please select it from the list.")
                target_dir = None # Reset to re-prompt
                continue
            try:
                target_dir.mkdir(parents=True)
                print(f"Folder '{target_dir.name}' created successfully.")
            except Exception as e:
                print(f"Error creating folder: {e}", file=sys.stderr)
                target_dir = None # Reset to re-prompt
        else:
            target_dir = content_dir / chosen_option

    post_title = get_valid_input("Enter the post title: ")
    tags_input = get_valid_input("Enter tags, comma-separated: ")
    tags_list = [tag.strip() for tag in tags_input.split(',') if tag.strip()]

    slug = slugify(post_title) or "untitled-post"
    permalink = Config.PERMALINK_STYLE.format(slug=slug)
    
    base_filename = f"{slug}"
    filepath = target_dir / f"{base_filename}.md"
    counter = 1
    while filepath.exists():
        filepath = target_dir / f"{base_filename}-{counter}.md"
        counter += 1
    
    if not create_md_file(filepath, post_title, tags_list, get_iso_datetime(), permalink):
        return

    if get_confirmation("Do you want to open the new file in your editor?"):
        open_file_with_editor(filepath)

def choice_2_new_draft(project_root: Path, content_dir: Path):
    """Handles Choice 2: Make a new draft in the drafts folder."""
    print("\n--- Make a new draft in the drafts folder ---")
    drafts_dir = project_root / Config.DRAFTS_DIR_NAME
    drafts_dir.mkdir(exist_ok=True)

    post_title = get_valid_input("Enter the draft title: ")
    tags_input = get_valid_input("Enter tags, comma-separated: ")
    tags_list = [tag.strip() for tag in tags_input.split(',') if tag.strip()]

    slug = slugify(post_title) or "untitled-draft"
    permalink = Config.PERMALINK_STYLE.format(slug=slug)

    base_filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{slug}"
    filepath = drafts_dir / f"{base_filename}.md"
    counter = 1
    while filepath.exists():
        filepath = drafts_dir / f"{base_filename}-{counter}.md"
        counter += 1

    if not create_md_file(filepath, post_title, tags_list, get_iso_datetime(), permalink):
        return

    if get_confirmation("Do you want to open the new draft in your editor?"):
        open_file_with_editor(filepath)
        if get_confirmation("Do you want to move this draft to a category now?"):
            choice_3_move_drafts(project_root, content_dir, specific_file=filepath)
    else:
        open_path(drafts_dir)

def choice_3_move_drafts(project_root: Path, content_dir: Path, specific_file: Optional[Path] = None):
    """Handles Choice 3: Move drafts to post categories."""
    print("\n--- Move drafts to post categories ---")
    drafts_dir = project_root / Config.DRAFTS_DIR_NAME
    if not drafts_dir.is_dir():
        print(f"Drafts directory ('{Config.DRAFTS_DIR_NAME}') not found.", file=sys.stderr)
        return

    draft_files = [specific_file] if specific_file and specific_file.exists() else \
                  [f for f in drafts_dir.iterdir() if f.is_file() and f.suffix.lower() == '.md']

    if not draft_files:
        print("No markdown drafts found to move.")
        return

    if not content_dir or not content_dir.is_dir():
        print(f"Error: Content directory ('{Config.CONTENT_DIR_NAME}') not found.", file=sys.stderr)
        return

    dest_dirs = get_valid_subdirectories(content_dir, Config.EXCLUDE_DIRS)
    if not dest_dirs:
        print(f"No suitable destination folders found in '{content_dir.name}'.", file=sys.stderr)
        return

    dest_options = [d.name for d in dest_dirs]
    for draft_file in draft_files:
        post_title = get_title_from_md_file(draft_file)
        print("-" * 20)
        choice = get_numbered_choice(f"Select destination for draft: \"{post_title}\"", dest_options)
        if choice:
            _, chosen_dest_name = choice
            destination_dir = content_dir / chosen_dest_name
            destination_path = destination_dir / draft_file.name
            
            if destination_path.exists():
                print(f"Warning: A file named '{draft_file.name}' already exists in '{destination_dir.name}'.")
                if not get_confirmation("Do you want to overwrite it?"):
                    print(f"Skipping move for '{draft_file.name}'.")
                    continue
            
            try:
                print(f"Moving '{draft_file.name}' to '{destination_dir.name}'...")
                shutil.move(str(draft_file), str(destination_path))
                print("Move successful.")
            except Exception as e:
                print(f"Error moving file: {e}", file=sys.stderr)
        else:
            print(f"Skipping move for \"{post_title}\".")
            if len(draft_files) > 1 and not get_confirmation("Continue with next draft?"):
                break

def choice_4_serve_local(project_root: Path):
    """Handles Choice 4: Serve site locally for testing."""
    print("\n--- Serve site locally for testing ---")
    print("Press Ctrl+C in this terminal to stop the server.")
    try:
        run_command(["npx", "@11ty/eleventy", "--serve"], cwd=project_root, check=False)
    except KeyboardInterrupt:
        print("\nEleventy server stopped by user.")

def choice_5_build_and_deploy(project_root: Path):
    """Handles Choice 5: Build and Deploy Website."""
    print("\n" + "!" * 40)
    print("! WARNING: This will build and deploy the site.")
    print(f"! It will run git commands and rclone to modify the remote: {Config.RCLONE_REMOTE_NAME}")
    if Config.DEPLOY_CLEAN_REMOTE:
        print("! The remote will be completely wiped before uploading the new site.")
    print("!" * 40)

    if not get_confirmation("Are you sure you want to proceed with deployment?"):
        print("Deployment cancelled.")
        return

    local_output_dir = project_root / Config.ELEVENTY_OUTPUT_DIR
    if local_output_dir.exists():
        print(f"\n--- Cleaning local output directory: {local_output_dir} ---")
        try:
            shutil.rmtree(local_output_dir)
        except Exception as e:
            print(f"Error cleaning local directory: {e}", file=sys.stderr)
            if not get_confirmation("Continue anyway?"): return

    print("\n--- Building site with Eleventy ---")
    if not run_command(["npx", "@11ty/eleventy"], cwd=project_root):
        print("Eleventy build failed. Aborting deployment.", file=sys.stderr)
        return

    print("\n--- Committing and pushing source files with Git ---")
    commit_message = get_valid_input("Enter commit message", default=Config.DEFAULT_COMMIT_MESSAGE)
    if not run_command(["git", "add", "."], cwd=project_root): return
    run_command(["git", "commit", "-m", commit_message], cwd=project_root, check=False)
    if not run_command(["git", "push"], cwd=project_root): return

    print("\n--- Deploying site with rclone ---")
    rclone_remote_path = f"{Config.RCLONE_REMOTE_NAME.rstrip(':')}:"
    if Config.DEPLOY_CLEAN_REMOTE:
        print(f"Cleaning remote target: {rclone_remote_path}")
        if not run_command(["rclone", "delete", rclone_remote_path, "--rmdirs"], cwd=project_root):
            return
    
    print(f"Copying '{Config.ELEVENTY_OUTPUT_DIR}' to '{rclone_remote_path}'")
    if not run_command(["rclone", "copy", Config.ELEVENTY_OUTPUT_DIR, rclone_remote_path, "--progress"], cwd=project_root):
        return

    print("\n" + "="*25 + "\n  DEPLOYMENT COMPLETE! \n" + "="*25)
    if get_confirmation(f"Do you want to open {Config.FINAL_WEBSITE_URL} in your browser?"):
        try: webbrowser.open(Config.FINAL_WEBSITE_URL)
        except Exception as e: print(f"Could not open browser: {e}", file=sys.stderr)

    print("\nExiting script.")
    sys.exit(0)


# --- Main Execution ---
def main():
    """Main function to run the helper script."""
    required_commands = ['git', 'npx', 'rclone']
    missing_commands = [cmd for cmd in required_commands if not shutil.which(cmd)]
    if missing_commands:
        print("Error: The following required commands were not found in your system's PATH:", file=sys.stderr)
        for cmd in missing_commands: print(f"- {cmd}", file=sys.stderr)
        print("Please install them and ensure they are accessible before running this script.", file=sys.stderr)
        sys.exit(1)

    setup_yaml()
    project_root = find_project_root()
    print(f"Detected project root: {project_root}")

    while True:
        content_dir = project_root / Config.CONTENT_DIR_NAME
        print("\n" + "=" * 30 + "\n Eleventy Helper Script\n" + "=" * 30)
        main_choices = [
            "Draft a new post in a category", "Make a new draft",
            "Move drafts to categories", "Serve site locally for testing",
            "Build and Deploy Website", "Exit"
        ]
        for i, choice_text in enumerate(main_choices):
             print(f"{i + 1}. {choice_text}")

        try:
            main_choice_num = input("Enter your choice number: ").strip()
            if main_choice_num == '1': choice_1_new_post_category(project_root, content_dir)
            elif main_choice_num == '2': choice_2_new_draft(project_root, content_dir)
            elif main_choice_num == '3': choice_3_move_drafts(project_root, content_dir)
            elif main_choice_num == '4': choice_4_serve_local(project_root)
            elif main_choice_num == '5': choice_5_build_and_deploy(project_root)
            elif main_choice_num == '6':
                print("Exiting script.")
                break
            else:
                print("Invalid choice. Please enter a number from the list.")
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled. Exiting.")
            break

        print("\n...Returning to main menu...")
        time.sleep(1)

if __name__ == "__main__":
    main()