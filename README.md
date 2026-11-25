# Portfolio Assets

> Headless CMS powering [subhan-ahmd.github.io](https://subhan-ahmd.github.io) — JSON data, media assets, skill icons, and automated multi-language CV generation, all served via GitHub raw URLs at zero hosting cost.

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
CV PDFs    Manifest
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
|   |-- experiences.json     # Work history
|   |-- projects.json        # Projects with tech stacks
|   |-- education.json       # Degrees, scores, duration
|   |-- skills.json          # Skill groups with stable skill keys
|   |-- languages.json       # Spoken languages
|   |-- contacts.json        # Email, phone
|   |-- socials.json         # LinkedIn, GitHub, portfolio links
|   |-- cv_flavours.json     # Tailored CV variants
|   +-- i18n/
|       +-- cv_strings.json  # CV structure text per language
|
|-- projects/{slug}/         # Project assets
|   |-- logo.png
|   |-- screenshots/         # .png, .jpg, .jpeg, .gif, .webp
|   |-- videos/              # .mp4, .mkv, .avi, .mov, .webm
|   |-- pdfs/                # .pdf
|   |-- docs/                # .md
|   +-- installers/          # .apk, .exe, .dmg, .msi
|
|-- experience/{slug}/       # Experience assets (logos, etc.)
|-- education/{slug}/        # Education assets
|-- certifications/{slug}/   # Certification assets
|-- skills/                  # Skill icons (SVG/PNG, keyed by skill key)
|
|-- cv/                      # Generated CVs (never edit by hand)
|   |-- {lang}/              # Timestamped CVs per language
|   +-- latest/{lang}/       # Stable-name copies per language
|
|-- profile.png              # Transparent cut-out (site hero + CV photo)
|-- profile.jpeg             # Full portrait (source of the cut-out)
|-- profile-linkedin.jpg     # 1024x1024 head-and-shoulders crop for LinkedIn
|-- manifest.json            # Auto-generated asset index
|
|-- cv_i18n.py               # Shared helpers: localization, CV filenames/folders
|-- generate_cv.py           # CV PDF generator (ReportLab)
|-- generate_manifest.py     # Asset manifest generator
|-- tests/                   # pytest suite for both scripts
|-- fonts/                   # Montserrat font files for CV
|-- requirements.txt         # Python dependencies
+-- .github/workflows/       # CI/CD pipelines
```

## Data & i18n

Every data item keeps its **language-neutral** fields (ids, slugs, dates, flags, URLs, scores and names) in its body. Its **translatable text** lives under `i18n.<lang>`:

```json
{
  "id": 2,
  "slug": "orbilon",
  "association": "Orbilon Technologies",
  "startDate": "2025-01-01T00:00:00.000",
  "endDate": "2026-07-01T00:00:00.000",
  "i18n": {
    "en": {
      "title": "Software Engineer",
      "location": "Lahore, Pakistan",
      "description": ["..."],
      "shortDescription": ["..."]
    }
  },
  "showInCv": true,
  "showInPortfolio": true
}
```

Facts exist once, so languages can't drift apart. To add a language, add an `i18n.<lang>` block next to `en`.

| File | Under `i18n.<lang>` |
|---|---|
| `profile.json` | `position`, `intro`, `shortDescription`, `currentCountry` |
| `experiences.json` | `title`, `location`, `description`, `shortDescription` |
| `projects.json` | `description`, `shortDescription` |
| `education.json` | `title`, `location`, `markingScheme`, `description`, `shortDescription` |
| links (any file) | `label` |
| `skills.json` | group `title`; the `name` of skills that need translating |
| `languages.json` | `name`, `fluency` |
| `contacts.json`, `socials.json`, `cv_flavours.json` | nothing |

Company, university and project names stay neutral.

### Skills

Each skill has a stable `key`, which matches its icon filename in `skills/` (`csharp` → `skills/csharp.svg`). Names that are the same in every language are neutral; others are translated:

```json
{"key": "flutter", "name": "Flutter"}
{"key": "problem_solving", "i18n": {"en": {"name": "Problem Solving"}}}
```

Key rule: lowercase, `#` → `sharp`, `+` → `p`, `.` removed, space and `/` → `_` (`ASP.NET Core` → `aspnet_core`, `CI/CD` → `ci_cd`). CV flavours refer to skills by key.

## CV Generation

CVs are generated from the JSON data with Python + ReportLab.

**Features:**
- Montserrat font, A4 layout, professional formatting
- Sections: header, summary, work experience, projects, education, skills, languages
- Experience, projects and education sorted by `id` descending (latest first)
- `showInCv` / `showInPortfolio` visibility flags on every data item
- Clickable footer linking to this repo
- One generic CV per language, plus one CV per enabled flavour

### Languages — `data/i18n/cv_strings.json`

Each key is a language. Its entry holds the CV structure text: section headings, month names, the word for "present", the footer, and the document word used in filenames (`CV` / `Lebenslauf`).

`contentLanguage` decides which `i18n` block the item text comes from. German is set to `"en"` until the German data exists, so German CVs currently have German structure with English content. Flip it to `"de"` once every item has an `i18n.de` block.

### Flavours — `data/cv_flavours.json`

A flavour is a tailored CV. Its `label`, `position` and `summary` are plain text written in the flavour's own language. `language` picks the structure text, the output folder and the content language. Flavours in different languages may share a slug.

```json
{
  "slug": "portfolio",
  "language": "en",
  "label": "Portfolio",
  "showPhoto": false,
  "showQr": true,
  "position": "Software Engineer",
  "summary": "Optional summary override",
  "hideProjects": ["sales_quotation_system"],
  "skills": {"technical": {"highlight": ["flutter", "dart"], "hide": ["cpp"]}}
}
```

Options: `disabled`, `showPhoto` (photo circle top right of the header, cut from `profile.png`; missing = `false`, generic CVs never show one), `showQr` (QR code linking to the portfolio site, captioned "Scan me ↗": top left next to a photo, otherwise top right; missing = `false`, generic CVs always show one), `position`, `summary`, `showProjects` / `showExperiences` / `showEducation` (pick and order by slug), `hideProjects` / `hideExperiences` / `hideEducation`, and `skills.<group>.highlight/hide` (skill keys).

### Output

Every run first deletes **all** PDFs under `cv/`, then writes:

| | Timestamped | Stable copy |
|---|---|---|
| Generic | `cv/{lang}/{name} - {word} - {ddmmyy-HHMM}.pdf` | `cv/latest/{lang}/{name} - {word}.pdf` |
| Flavour | `cv/{lang}/{name} - {word} - {label} - {ts}.pdf` | `cv/latest/{lang}/{name} - {word} - {label}.pdf` |

e.g. `cv/latest/de/Subhan Ahmed - Lebenslauf.pdf`. A `/` in a label is written as `∕` (a look-alike that is legal in filenames). Other characters not allowed in filenames (`\ : * ? " < > |`) stop the run with an error.

The English generic CV is also copied to `cv/latest/{name} - CV.pdf`, so the pre-i18n permalink keeps working.

Stable CV links have the form:
```
https://raw.githubusercontent.com/subhan-ahmd/portfolio-assets/main/cv/latest/en/Subhan%20Ahmed%20-%20CV.pdf
```

## Manifest Generation

`generate_manifest.py` scans the repo and produces `manifest.json`. CVs are indexed by language first, then by `generic` or flavour slug:

```json
{
  "generatedAt": "2026-11-23T20:00:00Z",
  "profile": "profile.png",
  "cv": {
    "en": {
      "generic": {"latest": "Subhan Ahmed - CV.pdf", "timestamped": "Subhan Ahmed - CV - 231126-2000.pdf"},
      "portfolio": {"latest": "Subhan Ahmed - CV - Portfolio.pdf", "timestamped": "..."}
    },
    "de": {
      "generic": {"latest": "Subhan Ahmed - Lebenslauf.pdf", "timestamped": "..."}
    }
  },
  "projects": {
    "quick_care": {
      "logo": "logo.png",
      "screenshots": ["quick_care_1.png", "quick_care_2.png"]
    }
  },
  "experience": {
    "orbilon": { "logo": "logo.webp" }
  },
  "skills": {
    "flutter": "flutter.svg",
    "firebase": "firebase.svg"
  }
}
```

`latest` files live in `cv/latest/{lang}/`, `timestamped` files in `cv/{lang}/`.

## Visibility Flags

Every item in `experiences.json`, `projects.json`, `education.json`, `contacts.json`, and `socials.json` has:

```json
{
  "showInCv": true,
  "showInPortfolio": true
}
```

The CV generator filters by `showInCv`, the portfolio app by `showInPortfolio`.

Education has additional flags: `showScoreInCv`, `showScoreInPortfolio`, `showDurationInCv`, `showDurationInPortfolio`.

## Links

Projects, experiences, and education entries use a `links` array. Each link has per-consumer visibility flags, an optional `type`, and a translatable `label`:

```json
{
  "links": [
    {"url": "https://...", "type": "url", "showInCv": true, "showInPortfolio": true,
     "i18n": {"en": {"label": "App Store"}}},
    {"url": "https://.../.md", "type": "md", "showInCv": false, "showInPortfolio": true,
     "i18n": {"en": {"label": "Case Study"}}}
  ]
}
```

- **`type: "url"`** (default) — external link, opens in browser
- **`type: "md"`** — portfolio fetches the markdown and renders it inline
- The CV uses the **first link** where `showInCv: true` (clickable entry title)
- The portfolio shows **all links** where `showInPortfolio: true`

Markdown files can also be placed in `projects/{slug}/docs/` and are picked up by the manifest generator.

## CI/CD Workflows

### Generate CV PDF
**Triggers:** Push to `data/**`, `generate_cv.py`, or `requirements.txt`

Generates all CVs, commits `cv/`, then triggers the manifest workflow.

### Generate Asset Manifest
**Triggers:** Push to asset directories, `generate_manifest.py`, or on CV workflow completion

Regenerates `manifest.json` and commits if changed.

Both workflows use `[skip ci]` to prevent infinite loops and `--rebase -X theirs` for conflict resolution.

## Running Locally

Requires Python 3.10+. With [uv](https://docs.astral.sh/uv/):

```bash
uv run --with reportlab python generate_cv.py
uv run python generate_manifest.py
uv run --with pytest --with reportlab --with pypdf pytest tests -q
```

Or with pip: `pip install -r requirements.txt`, then `python generate_cv.py`.

## Adding Content

### New project assets
```bash
mkdir -p projects/my_app/screenshots
cp ~/screenshots/*.png projects/my_app/screenshots/
git add . && git commit -m "feat: add my_app assets" && git push
```

### New data entry
Edit the relevant JSON file in `data/` (text under `i18n.en`), push, and the CVs regenerate automatically.

## Supported File Types

| Asset Type      | Extensions                                |
|-----------------|-------------------------------------------|
| **Logo**        | `.png`, `.jpg`, `.jpeg`, `.svg`, `.webp`  |
| **Screenshots** | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`  |
| **Videos**      | `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`   |
| **PDFs**        | `.pdf`                                    |
| **Installers**  | `.apk`, `.exe`, `.dmg`, `.msi`, `.deb`, `.rpm` |
| **Docs**        | `.md`                                     |
| **Skill Icons** | `.png`, `.jpg`, `.jpeg`, `.svg`, `.webp`  |

## Tech Stack

- **Python** + ReportLab for CV PDF generation, pytest for tests
- **GitHub Actions** for CI/CD automation
- **GitHub raw URLs** as CDN (zero-cost asset delivery)
- **Flutter Web** for the portfolio app (separate repo)

## License

Personal portfolio asset repository. All assets are proprietary unless stated otherwise.
