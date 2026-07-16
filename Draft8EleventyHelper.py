script = r'''#!/usr/bin/env python3
"""
Eleventy Helper V9
Rebuilt version with:
- Nested category support
- Draft creation
- Post creation
- Draft moving
- Category memory
- Redirect support
- Tag normalization
- Permalink collision detection
- Local Eleventy serving
- Editor launching
- Backup/archive support
"""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'PyYAML'])
    import yaml

PROJECT_ROOT = Path(__file__).resolve().parent
os.chdir(PROJECT_ROOT)

CONTENT_DIR = PROJECT_ROOT / 'content'
DRAFTS_DIR = PROJECT_ROOT / 'drafts'
ARCHIVE_DIR = DRAFTS_DIR / 'archive'
SETTINGS_DIR = PROJECT_ROOT / '.settings'
SETTINGS_FILE = SETTINGS_DIR / 'settings.json'

EXCLUDED = {
    '_site','.git','.github','node_modules','feed','feeds',
    'assets','css','js','images','img','fonts','.settings','.cache'
}


def ensure_dirs():
    for d in [CONTENT_DIR, DRAFTS_DIR, ARCHIVE_DIR, SETTINGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def load_settings():
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {'last_category': ''}


def save_settings(data):
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding='utf-8')


def slugify(text):
    text = text.strip().lower().replace('/', ' ')
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def iso_date():
    return datetime.now(timezone.utc).isoformat()


def yes_no(prompt):
    while True:
        v = input(f'{prompt} (1=yes,2=no): ').strip()
        if v == '1':
            return True
        if v == '2':
            return False


def open_editor(path):
    try:
        if sys.platform.startswith('win'):
            os.startfile(str(path))
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(path)])
        else:
            subprocess.run(['xdg-open', str(path)])
        input('Press Enter after saving and closing the file...')
    except Exception as e:
        print(e)


def categories():
    results = []
    if not CONTENT_DIR.exists():
        return results
    for root, dirs, files in os.walk(CONTENT_DIR):
        dirs[:] = [d for d in dirs if d.lower() not in EXCLUDED]
        rel = Path(root).relative_to(CONTENT_DIR)
        if str(rel) != '.':
            results.append(rel.as_posix())
    return sorted(results)


def choose_category():
    cats = categories()
    settings = load_settings()

    print('\nCategories')
    if settings.get('last_category'):
        print(f'Last used: {settings["last_category"]}')

    for i,c in enumerate(cats,1):
        print(f'{i}. {c}')

    print('N. Create New Category')

    while True:
        choice = input('Choice: ').strip()
        if choice.lower() == 'n':
            name = input('New category path (nested allowed): ').strip().replace('\\','/')
            path = CONTENT_DIR / name
            path.mkdir(parents=True, exist_ok=True)
            settings['last_category'] = name
            save_settings(settings)
            return path
        try:
            idx = int(choice)-1
            if 0 <= idx < len(cats):
                settings['last_category'] = cats[idx]
                save_settings(settings)
                return CONTENT_DIR / cats[idx]
        except ValueError:
            pass


def normalize_tags(text):
    seen = set()
    out = []
    for t in text.split(','):
        t = slugify(t.replace('-', ' '))
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def permalink_exists(permalink):
    for md in list(CONTENT_DIR.rglob('*.md')) + list(DRAFTS_DIR.rglob('*.md')):
        try:
            txt = md.read_text(encoding='utf-8')
            if permalink in txt:
                return True
        except Exception:
            pass
    return False


def unique_file(directory, slug):
    path = directory / f'{slug}.md'
    n = 2
    while path.exists():
        path = directory / f'{slug}-{n}.md'
        n += 1
    return path


def create_item(directory):
    title = input('Title: ').strip()
    if not title:
        return

    tags = normalize_tags(input('Tags (comma-separated): '))

    slug = slugify(title)

    if yes_no('Is this a redirect?'):
        target = input('Enter URL without slashes: ').strip()
        permalink_slug = slugify(target)
    else:
        permalink_slug = slug

    permalink = f'/{permalink_slug}/'

    if permalink_exists(permalink):
        print('Warning: permalink already exists.')

    filepath = unique_file(directory, slug)

    front = {
        'title': title,
        'date': iso_date(),
        'tags': tags,
        'permalink': permalink
    }

    yml = yaml.safe_dump(front, sort_keys=False, allow_unicode=True)

    filepath.write_text(f'---\n{yml}---\n\n', encoding='utf-8')

    print(f'Created: {filepath}')

    if yes_no('Open file now?'):
        open_editor(filepath)


def create_post():
    create_item(choose_category())


def create_draft():
    create_item(DRAFTS_DIR)


def move_draft():
    drafts = sorted([p for p in DRAFTS_DIR.glob('*.md')])
    if not drafts:
        print('No drafts found.')
        return

    for i,d in enumerate(drafts,1):
        print(f'{i}. {d.name}')

    while True:
        try:
            draft = drafts[int(input('Draft: '))-1]
            break
        except Exception:
            pass

    backup = ARCHIVE_DIR / draft.name
    shutil.copy2(draft, backup)

    dest_dir = choose_category()
    dest = dest_dir / draft.name

    if dest.exists():
        print('Destination already exists.')
        return

    shutil.move(str(draft), str(dest))
    print(f'Moved: {dest}')

    if yes_no('Open moved file?'):
        open_editor(dest)


def serve_site():
    try:
        subprocess.run(['npx','@11ty/eleventy','--version'], check=True)
        subprocess.run(['npx','@11ty/eleventy','--serve'])
    except Exception as e:
        print(f'Eleventy failed: {e}')


def menu():
    while True:
        print('\nEleventy Helper V9')
        print('1. Create Post')
        print('2. Create Draft')
        print('3. Move Draft')
        print('4. Serve Site')
        print('5. Exit')

        c = input('Choice: ').strip()

        if c == '1':
            create_post()
        elif c == '2':
            create_draft()
        elif c == '3':
            move_draft()
        elif c == '4':
            serve_site()
        elif c == '5':
            break


if __name__ == '__main__':
    ensure_dirs()
    menu()
'''

path='/mnt/data/EleventyHelperV9.py'
with open(path,'w',encoding='utf-8') as f:
    f.write(script)
print(path)
