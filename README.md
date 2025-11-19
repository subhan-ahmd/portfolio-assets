# 🎨 Portfolio Assets

> **Dynamic asset management for your Flutter portfolio** - Drop files, push code, and let automation do the rest!

[![Generate Asset Manifest](https://github.com/subhan-ahmd/portfolio-assets/actions/workflows/generate-manifest.yml/badge.svg)](https://github.com/subhan-ahmd/portfolio-assets/actions/workflows/generate-manifest.yml)

## ✨ What is this?

This repository serves as a **centralized asset storage** for my Flutter portfolio app. Instead of bundling heavy assets (screenshots, videos, PDFs, installers) into the app, they're hosted here and loaded dynamically via a generated manifest.

### 🚀 The Magic

1. **Drop assets** into organized folders
2. **Push to GitHub**
3. **GitHub Actions automatically generates** `manifest.json`
4. **Flutter app fetches** the manifest and loads assets on-demand

No manual JSON editing. No typos. Just pure automation. ✨

---

## 📁 Repository Structure

```
portfolio-assets/
├── projects/          # Project portfolio items
│   └── {slug}/       # e.g., quick_care, expense_tracker
│       ├── screenshots/   # .png, .jpg, .jpeg, .gif, .webp
│       ├── videos/        # .mp4, .mkv, .avi, .mov, .webm
│       ├── pdfs/          # .pdf
│       └── installers/    # .apk, .exe, .dmg, .msi
│
├── education/         # Education credentials
│   └── {slug}/       # e.g., kfueit
│       ├── screenshots/
│       ├── videos/
│       └── pdfs/
│
├── experience/        # Work experience & achievements
│   └── {slug}/       # e.g., orbilon
│       ├── screenshots/
│       ├── videos/
│       └── pdfs/
│
└── certifications/    # Professional certifications
    └── {slug}/       # e.g., udemy_flutter
        ├── screenshots/
        ├── videos/
        └── pdfs/
```

---

## 📋 Generated Manifest Format

The GitHub Action automatically generates `manifest.json` in this format:

```json
{
  "projects": {
    "quick_care": {
      "screenshots": ["1.png", "2.png", "3.jpg"],
      "videos": ["demo.mp4"],
      "pdfs": ["documentation.pdf"],
      "installers": ["app-release.apk"]
    },
    "expense_tracker": {
      "screenshots": ["1.png", "2.png"]
    }
  },
  "education": {
    "kfueit": {
      "pdfs": ["certificate.pdf"],
      "screenshots": ["transcript.png"]
    }
  },
  "experience": {
    "orbilon": {
      "screenshots": ["offer_letter.png"]
    }
  },
  "certifications": {
    "udemy_flutter": {
      "pdfs": ["certificate.pdf"]
    }
  }
}
```

---

## 🔧 How It Works

### Adding New Assets

1. **Create a slug directory** under the appropriate category:
   ```bash
   mkdir -p projects/xyz/screenshots
   ```

2. **Add your files** (they'll be sorted naturally):
   ```bash
   cp ~/Downloads/screenshot_1.png projects/xyz/screenshots/1.png
   cp ~/Downloads/screenshot_2.png projects/xyz/screenshots/2.png
   ```

3. **Commit and push**:
   ```bash
   git add .
   git commit -m "feat: add xyz project"
   git push
   ```

4. **Watch the magic happen!** 🎩✨
   - GitHub Actions runs automatically
   - `manifest.json` is generated
   - Changes are committed back to the repo

### Manual Generation (Local Testing)

You can also generate the manifest locally:

```bash
python3 generate_manifest.py
```

---

## 🎯 Usage in Flutter

In your Flutter app, fetch the manifest and use it to load assets dynamically:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class AssetService {
  static const String manifestUrl =
    'https://raw.githubusercontent.com/subhan-ahmd/portfolio-assets/main/manifest.json';

  static const String baseAssetUrl =
    'https://raw.githubusercontent.com/subhan-ahmd/portfolio-assets/main';

  Future<Map<String, dynamic>> getManifest() async {
    final response = await http.get(Uri.parse(manifestUrl));
    return json.decode(response.body);
  }

  String getAssetUrl(String category, String slug, String type, String filename) {
    return '$baseAssetUrl/$category/$slug/$type/$filename';
  }
}

// Example usage:
// final manifest = await AssetService().getManifest();
// final screenshots = manifest['projects']['quick_care']['screenshots'];
// final imageUrl = AssetService().getAssetUrl('projects', 'quick_care', 'screenshots', '1.png');
```

---

## 🤖 GitHub Actions Workflow

The workflow (`.github/workflows/generate-manifest.yml`) runs when:

- You push changes to `projects/**`, `education/**`, or `experience/**`
- You manually trigger it from the Actions tab

**Key features:**
- ✅ Automatically detects new/changed assets
- ✅ Generates manifest with proper JSON formatting
- ✅ Commits changes back to the repo (with `[skip ci]` to prevent infinite loops)
- ✅ Skips commit if manifest hasn't changed

---

## 📦 Supported File Types

| Asset Type | Extensions |
|-----------|-----------|
| **screenshots** | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp` |
| **videos** | `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm` |
| **pdfs** | `.pdf` |
| **installers** | `.apk`, `.exe`, `.dmg`, `.msi`, `.deb`, `.rpm` |

---

## 🛠️ Customization

### Adding New Categories

Edit `generate_manifest.py` and add your category to the `CATEGORIES` list:

```python
CATEGORIES = ['projects', 'education', 'experience', 'certifications']
```

### Adding New Asset Types

Add new types to the `ASSET_TYPES` dictionary:

```python
ASSET_TYPES = {
    'screenshots': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
    'videos': ['.mp4', '.mkv', '.avi', '.mov', '.webm'],
    'pdfs': ['.pdf'],
    'installers': ['.apk', '.exe', '.dmg', '.msi', '.deb', '.rpm']
}
```

---

## 🎓 Benefits

✅ **No app bloat** - Assets aren't bundled with the app
✅ **Easy updates** - Change assets without rebuilding the app
✅ **Version control** - All assets are tracked in Git
✅ **Automatic manifest** - No manual JSON editing
✅ **Type safety** - Flutter knows exactly what assets exist
✅ **Scalable** - Add unlimited projects without touching code

---

## 📝 License

This is a personal portfolio asset repository. All assets are proprietary unless stated otherwise.

---

## 🙏 Acknowledgments

Built with:
- 🐍 Python (manifest generation)
- ⚙️ GitHub Actions (automation)
- 🎨 Flutter (asset consumption)
- ❤️ Love for clean architecture

---

**Happy coding!** 🚀

*Remember: Don't commit sensitive files. Add them to `.gitignore` if needed.*
