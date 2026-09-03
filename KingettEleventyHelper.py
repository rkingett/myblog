import os
import sys
import re
import shutil
import subprocess
import datetime
import platform
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field

try:
    import yaml
except ImportError:
    print("PyYAML is required. Please install it: pip install PyYAML")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)

CONTENT_DIR = PROJECT_ROOT / "content"

EXCLUDED_DIRS = {
    "_site", ".git", ".github", ".settings", ".cache", "node_modules",
    "feed", "feeds", "assets", "css", "js", "images", "img", "fonts",
    "drafts"
}

@dataclass
class PostMeta:
    path: Path
    title: str = ""
    permalink: str = ""
    redirect_from: str = ""
    yaml_lines: List[str] = field(default_factory=list)
    content_lines: List[str] = field(default_factory=list)
    has_yaml: bool = False
    parsed_yaml: dict = field(default_factory=dict)


# --- Custom YAML Formatting ---

class FlowStyleList(list):
    """Custom list class to force YAML inline/flow style."""
    pass

class QuotedString(str):
    """Custom string class to force YAML double quotes."""
    pass

class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True

NoAliasDumper.add_representer(
    FlowStyleList, 
    lambda dumper, data: dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)
)
NoAliasDumper.add_representer(
    QuotedString, 
    lambda dumper, data: dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')
)


def get_drafts_dir() -> Path:
    lower_drafts = PROJECT_ROOT / "drafts"
    upper_drafts = PROJECT_ROOT / "Drafts"
    
    if lower_drafts.exists() and lower_drafts.is_dir():
        return lower_drafts
    
    if not upper_drafts.exists():
        upper_drafts.mkdir(parents=True, exist_ok=True)
        
    return upper_drafts


def initialize_environment() -> None:
    try:
        CONTENT_DIR.mkdir(parents=True, exist_ok=True)
        get_drafts_dir()
    except Exception as e:
        print(f"Failed to initialize environment: {e}")
        sys.exit(1)

def slugify(text: str) -> str:
    text = text.lower()
    text = text.replace("/", "-").replace("\\", "-")
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text).strip("-")
    return text

def make_permalink(text: str) -> str:
    # Ensure permalink always begins with /posts/<slug>/
    if not text:
        text = "untitled"
    # Strip leading/trailing slashes if provided and slugify the remainder
    candidate = text.strip("/")
    candidate = slugify(candidate)
    if not candidate:
        candidate = "untitled"
    return f"/posts/{candidate}/"

def is_permalink_valid(permalink: str) -> bool:
    if not permalink:
        return False
    # Allow absolute external URLs
    if permalink.startswith("http://") or permalink.startswith("https://"):
        return True
    # Require all internal permalinks to start with /posts/
    if not permalink.startswith("/posts/"):
        return False
    if not permalink.endswith("/"):
        return False
    if " " in permalink:
        return False
    if permalink != permalink.lower():
        return False
    # only allow lowercase letters, numbers, slashes and hyphens
    if re.search(r'[^a-z0-9/-]', permalink):
        return False
    return True

def open_editor(filepath: Path) -> None:
    try:
        if platform.system() == "Windows":
            os.startfile(filepath)
        elif platform.system() == "Darwin":
            subprocess.run(["open", str(filepath)], check=True)
        else:
            subprocess.run(["xdg-open", str(filepath)], check=True)
    except Exception as e:
        print(f"Failed to open file: {e}")

def create_post() -> None:
    print("\n--- CREATE POST ---")
    title = ""
    while not title:
        try:
            title = input("Enter title: ").strip()
        except EOFError:
            print("No input provided. Aborting.")
            return

    tags_input = input("Enter tags (comma-separated): ").strip()
    user_tags = [t.strip() for t in tags_input.split(",") if t.strip()]

    merged_tags = []
    for tag in user_tags:
        if tag and tag not in merged_tags:
            merged_tags.append(tag)

    is_redirect = input("Is this a redirect post? (y/N): ").strip().lower() == 'y'
    permalink = make_permalink(title)
    redirect_value = ""

    if is_redirect:
        redirect_input = input("Enter redirect_from (existing path or full URL): ").strip()
        if redirect_input:
            if redirect_input.startswith("http://") or redirect_input.startswith("https://"):
                redirect_value = redirect_input
            else:
                # treat as a site path/slug and normalize to /posts/<slug>/
                redirect_value = make_permalink(redirect_input)

    filename_base = slugify(title)
    if not filename_base:
        filename_base = "untitled"

    target_dir = get_drafts_dir()

    filename = f"{filename_base}.md"
    filepath = target_dir / filename

    counter = 2
    while filepath.exists():
        filename = f"{filename_base}-{counter}.md"
        filepath = target_dir / filename
        counter += 1

    current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

    frontmatter: Dict[str, Any] = {
        "title": QuotedString(title),
        "date": current_time,
        "tags": FlowStyleList(merged_tags),
        "permalink": QuotedString(permalink)
    }

    if is_redirect and redirect_value:
        frontmatter["redirect_from"] = QuotedString(redirect_value)

    try:
        yaml_str = yaml.dump(frontmatter, Dumper=NoAliasDumper, sort_keys=False, allow_unicode=True)
        # Properly delimit frontmatter and leave a blank line before content
        content = f"---\n{yaml_str}---\n\n"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\nCreated: {filepath}")
    except Exception as e:
        print(f"Failed to create file: {e}")
        return

    open_file = input("Open file? (Y/n): ").strip().lower() != 'n'
    if open_file:
        open_editor(filepath)

def read_post(filepath: Path) -> PostMeta:
    meta = PostMeta(path=filepath)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        if not lines or not lines[0].strip() == "---":
            meta.content_lines = lines
            return meta
            
        yaml_end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                yaml_end_idx = i
                break
        
        if yaml_end_idx != -1:
            meta.has_yaml = True
            meta.yaml_lines = lines[1:yaml_end_idx]
            meta.content_lines = lines[yaml_end_idx+1:]
            
            try:
                parsed = yaml.safe_load("".join(meta.yaml_lines))
                if isinstance(parsed, dict):
                    meta.parsed_yaml = parsed
                    meta.title = parsed.get("title") or ""
                    perm = parsed.get("permalink") or ""
                    meta.permalink = str(perm) if perm is not None else ""
                    red = parsed.get("redirect_from") or ""
                    meta.redirect_from = str(red) if red is not None else ""
            except Exception:
                pass
        else:
            meta.content_lines = lines
    except Exception:
        pass
    return meta

def scan_content() -> List[PostMeta]:
    posts = []
    try:
        for filepath in CONTENT_DIR.rglob("*.md"):
            is_excluded = False
            for parent in filepath.parents:
                if parent.name.lower() in EXCLUDED_DIRS:
                    is_excluded = True
                    break
            if not is_excluded:
                posts.append(read_post(filepath))
    except Exception as e:
        print(f"Error scanning content: {e}")
    return posts

def audit_permalinks() -> None:
    print("\n--- AUDIT PERMALINKS & REDIRECTS ---")
    posts = scan_content()
    
    missing_permalinks: List[Path] = []
    malformed_urls: List[Tuple[Path, str, str]] = []
    url_registry: Dict[str, List[Path]] = {}

    for p in posts:
        if not p.has_yaml:
            continue
        
        if not p.permalink:
            missing_permalinks.append(p.path)
        else:
            if not is_permalink_valid(p.permalink):
                malformed_urls.append((p.path, "permalink", p.permalink))
            else:
                url_registry.setdefault(p.permalink, []).append(p.path)
                
        if p.redirect_from:
            if not is_permalink_valid(p.redirect_from):
                malformed_urls.append((p.path, "redirect_from", p.redirect_from))
            else:
                url_registry.setdefault(p.redirect_from, []).append(p.path)

    conflicting_urls = {url: paths for url, paths in url_registry.items() if len(paths) > 1}
    
    report_file = PROJECT_ROOT / "audit_report.txt"
    try:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("=========================================\n")
            f.write(" ELEVENTY SITE AUDIT REPORT\n")
            f.write("=========================================\n")
            f.write(f"Generated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}\n")
            f.write(f"Total posts scanned: {len(posts)}\n\n")

            f.write("--- MISSING PERMALINKS ---\n")
            if missing_permalinks:
                for path in missing_permalinks:
                    f.write(f"- {path}\n")
            else:
                f.write("None found.\n")
            f.write("\n")

            f.write("--- MALFORMED URLS (Permalinks or Redirects) ---\n")
            if malformed_urls:
                for path, url_type, bad_url in malformed_urls:
                    f.write(f"- {path}\n  Invalid {url_type}: '{bad_url}'\n")
            else:
                f.write("None found.\n")
            f.write("\n")

            f.write("--- DUPLICATE / CONFLICTING URLS ---\n")
            if conflicting_urls:
                for url, paths in conflicting_urls.items():
                    f.write(f"- Conflict on URL: {url}\n")
                    for path in paths:
                        f.write(f"    - {path}\n")
            else:
                f.write("None found.\n")

        print(f"Audit complete! Comprehensive report saved to:\n{report_file}")
    except Exception as e:
        print(f"Failed to write audit report: {e}")

def serve_site() -> None:
    print("\n--- SERVE SITE ---")
    if not shutil.which("npx"):
        print("Error: 'npx' is not installed or not in PATH.")
        return
        
    try:
        result = subprocess.run(["npx", "--no-install", "@11ty/eleventy", "--version"], 
                                capture_output=True, text=True, input="n\n")
        if result.returncode != 0:
            print("Error: Eleventy does not appear to be installed locally or accessible via npx.")
            return
            
        print("Starting Eleventy server. Press Ctrl+C to stop.")
        subprocess.run(["npx", "@11ty/eleventy", "--serve"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Eleventy exited with error code: {e.returncode}")
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Unexpected error: {e}")

def main() -> None:
    initialize_environment()
    
    while True:
        print("\n" + "="*30)
        print(" EleventyHelperV9")
        print("="*30)
        print("1 Create Post")
        print("2 Audit Permalinks")
        print("3 Serve Site")
        print("4 Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == "1":
            create_post()
        elif choice == "2":
            audit_permalinks()
        elif choice == "3":
            serve_site()
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please select from the menu.")

if __name__ == "__main__":
    main()