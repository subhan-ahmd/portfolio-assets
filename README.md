# Portfolio Assets

> Headless CMS powering [subhan-ahmd.github.io](https://subhan-ahmd.github.io) — JSON data, media assets, skill icons, and automated CV generation, all served via GitHub raw URLs at zero hosting cost.

[![Generate CV PDF](https://github.com/subhan-ahmd/portfolio-assets/actions/workflows/generate-cv.yml/badge.svg)](https://github.com/subhan-ahmd/portfolio-assets/actions/workflows/generate-cv.yml)
[![Generate Asset Manifest](https://github.com/subhan-ahmd/portfolio-assets/actions/workflows/generate-manifest.yml/badge.svg)](https://github.com/subhan-ahmd/portfolio-assets/actions/workflows/generate-manifest.yml)

## How It Works

This repo is one half of a two-repo architecture:

1. **This repo (portfolio-assets)** — Data, assets, and automation
2. **[Portfolio app](https://github.com/subhan-ahmd/subhan-ahmd.github.io)** — Flutter Web SPA that consumes it

The app fetches `manifest.json` and all data files at runtime from `raw.githubusercontent.com`. No bundling, no backend, no hosting costs.

### The Pipeline

```
Edit JSON data or drop assets
        |
   git push to main
        |
   +----+----+
   |         |
   v         v
Generate   Generate
CV PDF     Manifest
   |         |
   +----+----+
        |
   Auto-commit back to repo
        |
   Portfolio app fetches latest on load
```

## Repository Structure

```
portfolio-assets/
|-- data/                    # JSON data (the "database")
|   |-- profile.json         # Name, position, bio, availableForWork flag
|   |-- experiences.json     # Work history with descriptions
|   |-- projects.json        # Project entries with tech stacks
|   |-- education.json       # Degrees, scores, duration
|   |-- skills.json          # Categorized skill lists
|   |-- languages.json       # Spoken languages
|   |-- contacts.json        # Email, phone
|   +-- socials.json         # LinkedIn, GitHub, portfolio links
|
|-- projects/{slug}/         # Project assets
|   |-- logo.png
|   |-- screenshots/         # .png, .jpg, .jpeg, .gif, .webp
|   |-- videos/              # .mp4, .mkv, .avi, .mov, .webm
|   |-- pdfs/                # .pdf
|   +-- installers/          # .apk, .exe, .dmg, .msi
|
|-- experience/{slug}/       # Experience assets (logos, etc.)
|-- education/{slug}/        # Education assets
|-- certifications/{slug}/   # Certification assets
|-- skills/                  # Skill icons (SVG/PNG, keyed by stem)
|
|-- profile.jpeg             # Profile photo
|-- cv.pdf                   # Always-latest CV (stable permalink)
|-- Subhan Ahmed - CV - *.pdf  # Timestamped CV snapshots
|-- manifest.json            # Auto-generated asset index
|
|-- generate_cv.py           # CV PDF generator (ReportLab)
|-- generate_manifest.py     # Asset manifest generator
|-- fonts/                   # Montserrat font files for CV
|-- requirements.txt         # Python dependencies
+-- .github/workflows/       # CI/CD pipelines
```

## CV Generation

The CV is generated programmatically from the JSON data files using Python + ReportLab.

**Features:**
- Montserrat font, A4 layout, professional formatting
- Sections: header, summary, work experience, projects, education, skills, languages
- Sorted by `id` descending (latest first)
- `showInCv` / `showInPortfolio` visibility flags on every data item for independent content control
- Clickable footer with source repo link and "Get latest here" permanent download link
- Outputs both a timestamped PDF and a stable `cv.pdf` copy

**Permanent CV link:**
```
https://raw.githubusercontent.com/subhan-ahmd/portfolio-assets/main/cv.pdf
```

**Run locally:**
```bash
pip install -r requirements.txt
python generate_cv.py
```

## Manifest Generation

`generate_manifest.py` scans the repo and produces `manifest.json`:

```json
{
  "profile": "profile.jpeg",
  "cv": "Subhan Ahmed - CV - 240226-1332.pdf",
  "cvLatest": "cv.pdf",
  "projects": {
    "quick_care": {
      "logo": "logo.png",
      "screenshots": ["quick_care_1.png", "quick_care_2.png"],
      "videos": ["1.mp4"],
      "installers": ["app-release.apk"]
    }
  },
  "experience": {
    "orbilon": { "logo": "logo.png" }
  },
  "skills": {
    "flutter": "flutter.svg",
    "firebase": "firebase.svg"
  }
}
```

**Run locally:**
```bash
python generate_manifest.py
```

## Visibility Flags

Every item in `experiences.json`, `projects.json`, `education.json`, `contacts.json`, and `socials.json` has:

```json
{
  "showInCv": true,
  "showInPortfolio": true
}
```

This allows independent control over what appears in the CV vs the portfolio website. The CV generator filters by `showInCv`, the portfolio app filters by `showInPortfolio`.

Education has additional granular flags: `showScoreInCv`, `showScoreInPortfolio`, `showDurationInCv`, `showDurationInPortfolio`.

## CI/CD Workflows

### Generate CV PDF
**Triggers:** Push to `data/**`, `generate_cv.py`, or `requirements.txt`

Generates the CV, commits both the timestamped and stable `cv.pdf`, then triggers the manifest workflow.

### Generate Asset Manifest
**Triggers:** Push to asset directories, `generate_manifest.py`, or on CV workflow completion

Regenerates `manifest.json` and commits if changed.

Both workflows use `[skip ci]` to prevent infinite loops and `--rebase -X theirs` for conflict resolution.

## Adding Content

### New project assets
```bash
mkdir -p projects/my_app/screenshots
cp ~/screenshots/*.png projects/my_app/screenshots/
git add . && git commit -m "feat: add my_app assets" && git push
```

### New data entry
Edit the relevant JSON file in `data/`, push, and the CV regenerates automatically.

## Supported File Types

| Asset Type      | Extensions                                |
|-----------------|-------------------------------------------|
| **Logo**        | `.png`, `.jpg`, `.jpeg`, `.svg`, `.webp`  |
| **Screenshots** | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`  |
| **Videos**      | `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`   |
| **PDFs**        | `.pdf`                                    |
| **Installers**  | `.apk`, `.exe`, `.dmg`, `.msi`, `.deb`, `.rpm` |
| **Skill Icons** | `.png`, `.jpg`, `.jpeg`, `.svg`, `.webp`  |

## Tech Stack

- **Python** + ReportLab for CV PDF generation
- **GitHub Actions** for CI/CD automation
- **GitHub raw URLs** as CDN (zero-cost asset delivery)
- **Flutter Web** for the portfolio app (separate repo)

## License

Personal portfolio asset repository. All assets are proprietary unless stated otherwise.
