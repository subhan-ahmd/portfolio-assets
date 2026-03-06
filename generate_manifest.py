#!/usr/bin/env python3
"""
Portfolio Assets Manifest Generator
Automatically scans the repository and generates a manifest.json file
"""

import os
import json
from pathlib import Path
from typing import Dict, List

# Define the main categories and their supported asset types
CATEGORIES = ['projects', 'education', 'experience', 'certifications']
ASSET_TYPES = {
    'screenshots': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
    'videos': ['.mp4', '.mkv', '.avi', '.mov', '.webm'],
    'pdfs': ['.pdf'],
    'installers': ['.apk', '.exe', '.dmg', '.msi', '.deb', '.rpm'],
    'docs': ['.md']
}
LOGO_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.svg', '.webp']


def get_files_in_directory(directory: Path, extensions: List[str]) -> List[str]:
    """
    Get all files in a directory that match the given extensions.
    Returns filenames sorted naturally.
    """
    if not directory.exists():
        return []

    files = []
    for file in directory.iterdir():
        if file.is_file() and file.suffix.lower() in extensions:
            files.append(file.name)

    # Sort files naturally (1.png, 2.png, ... 10.png)
    return sorted(files, key=lambda x: (
        int(''.join(filter(str.isdigit, x.split('.')[0]))) if any(c.isdigit() for c in x.split('.')[0]) else 0,
        x
    ))


def scan_slug_directory(slug_path: Path) -> Dict:
    """
    Scan a slug directory and return all assets organized by type.
    """
    assets = {}

    # Check for logo file in the slug root directory
    for file in slug_path.iterdir():
        if file.is_file() and file.stem.lower() == 'logo' and file.suffix.lower() in LOGO_EXTENSIONS:
            assets['logo'] = file.name
            break

    # Scan subdirectories for other asset types
    for asset_type, extensions in ASSET_TYPES.items():
        asset_dir = slug_path / asset_type
        files = get_files_in_directory(asset_dir, extensions)
        if files:  # Only include asset types that have files
            assets[asset_type] = files

    return assets


def get_profile_image(repo_root: Path) -> str | None:
    """
    Check for profile image in the root directory.
    Returns the filename if found, None otherwise.
    """
    for ext in LOGO_EXTENSIONS:
        profile_file = repo_root / f"profile{ext}"
        if profile_file.exists():
            return profile_file.name
    return None


def generate_manifest() -> Dict:
    """
    Generate the complete manifest by scanning all categories and slugs.
    """
    manifest = {}
    repo_root = Path(__file__).parent

    # Check for profile image
    profile_image = get_profile_image(repo_root)
    if profile_image:
        manifest['profile'] = profile_image

    # CV section: generic + flavoured variants
    cv_data = {}
    cv_dir = repo_root / "cv"
    cv_latest_dir = cv_dir / "latest"
    data_dir = repo_root / "data"
    flavours = []
    flavours_file = data_dir / "cv_flavours.json"
    if flavours_file.exists():
        with open(flavours_file, "r", encoding="utf-8") as f:
            flavours = json.load(f)

    # Generic CV
    generic_stable = cv_latest_dir / "cv.pdf"
    # Match timestamped generic: "Name - CV - DDMMYY-HHMM.pdf" (no label in between)
    generic_timestamped = sorted(
        p for p in cv_dir.glob("*- CV - *.pdf")
        if not any(p.name.count(" - CV - ") == 1 and f" - {fl['label']} - " in p.name for fl in flavours)
    ) if cv_dir.exists() else []
    if generic_stable.exists() or generic_timestamped:
        entry = {}
        if generic_stable.exists():
            entry["latest"] = generic_stable.name
        if generic_timestamped:
            entry["timestamped"] = generic_timestamped[-1].name
        cv_data["generic"] = entry

    # Flavoured CVs
    for fl in flavours:
        slug = fl["slug"]
        label = fl["label"]
        stable = cv_latest_dir / f"cv-{slug}.pdf"
        timestamped = sorted(cv_dir.glob(f"*- CV - {label} - *.pdf")) if cv_dir.exists() else []
        if stable.exists() or timestamped:
            entry = {}
            if stable.exists():
                entry["latest"] = stable.name
            if timestamped:
                entry["timestamped"] = timestamped[-1].name
            cv_data[slug] = entry

    if cv_data:
        manifest['cv'] = cv_data

    for category in CATEGORIES:
        category_path = repo_root / category

        if not category_path.exists():
            manifest[category] = {}
            continue

        category_data = {}

        # Iterate through each slug directory in the category
        for slug_dir in category_path.iterdir():
            if slug_dir.is_dir() and not slug_dir.name.startswith('.'):
                slug_assets = scan_slug_directory(slug_dir)
                if slug_assets:  # Only include slugs that have assets
                    category_data[slug_dir.name] = slug_assets

        manifest[category] = category_data

    # Skill icons (flat directory of icon files)
    skills_dir = repo_root / "skills"
    if skills_dir.exists():
        skills_icons = {}
        for file in sorted(skills_dir.iterdir()):
            if file.is_file() and file.suffix.lower() in LOGO_EXTENSIONS and not file.name.startswith('.'):
                skills_icons[file.stem] = file.name
        manifest["skills"] = skills_icons
    else:
        manifest["skills"] = {}

    return manifest


def main():
    """
    Main function to generate and save the manifest.
    """
    print("🔍 Scanning portfolio assets...")

    manifest = generate_manifest()

    # Count total assets
    total_assets = 0
    if 'profile' in manifest:
        total_assets += 1
    # Count skill icons (flat slug → filename dict)
    if 'skills' in manifest:
        total_assets += len(manifest['skills'])
    # Count category assets (nested slug → asset_type → files dict)
    for key, category in manifest.items():
        if key in ('profile', 'skills') or not isinstance(category, dict):
            continue
        for slug in category.values():
            for files in slug.values():
                total_assets += len(files) if isinstance(files, list) else 1

    project_count = sum(
        len(cat) for key, cat in manifest.items()
        if isinstance(cat, dict) and key not in ('skills', 'cv')
    )
    print(f"✅ Found {total_assets} assets across {project_count} projects")

    # Save manifest
    manifest_path = Path(__file__).parent / 'manifest.json'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"📝 Manifest saved to {manifest_path}")
    print("\n📊 Summary:")
    if 'profile' in manifest:
        print(f"  profile: {manifest['profile']}")
    if 'cv' in manifest:
        for cv_slug, cv_entry in manifest['cv'].items():
            latest = cv_entry.get('latest', '')
            print(f"  cv/{cv_slug}: {latest}")
    if 'skills' in manifest and manifest['skills']:
        print(f"  skills: {len(manifest['skills'])} icon(s)")
    for category, slugs in manifest.items():
        if category not in ('profile', 'skills', 'cv') and slugs:
            print(f"  {category}: {len(slugs)} item(s)")


if __name__ == '__main__':
    main()
