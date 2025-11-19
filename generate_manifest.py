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
    'installers': ['.apk', '.exe', '.dmg', '.msi', '.deb', '.rpm']
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


def generate_manifest() -> Dict:
    """
    Generate the complete manifest by scanning all categories and slugs.
    """
    manifest = {}
    repo_root = Path(__file__).parent

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

    return manifest


def main():
    """
    Main function to generate and save the manifest.
    """
    print("🔍 Scanning portfolio assets...")

    manifest = generate_manifest()

    # Count total assets
    total_assets = sum(
        len(files) if isinstance(files, list) else 1
        for category in manifest.values()
        for slug in category.values()
        for files in slug.values()
    )

    print(f"✅ Found {total_assets} assets across {sum(len(cat) for cat in manifest.values())} projects")

    # Save manifest
    manifest_path = Path(__file__).parent / 'manifest.json'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"📝 Manifest saved to {manifest_path}")
    print("\n📊 Summary:")
    for category, slugs in manifest.items():
        if slugs:
            print(f"  {category}: {len(slugs)} item(s)")


if __name__ == '__main__':
    main()
