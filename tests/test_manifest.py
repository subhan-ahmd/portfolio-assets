import json
import shutil
from pathlib import Path

import pytest

import generate_cv
import generate_manifest

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSET_DIRS = ["projects", "education", "experience", "skills"]


def make_repo(tmp: Path) -> Path:
    for d in ["data", "fonts", *ASSET_DIRS]:
        shutil.copytree(REPO_ROOT / d, tmp / d)
    shutil.copy2(REPO_ROOT / "profile.jpeg", tmp / "profile.jpeg")
    return tmp


@pytest.fixture
def repo(tmp_path):
    repo = make_repo(tmp_path)
    generate_cv.generate_all_cvs(repo)
    return repo


def test_manifest_cv_shape(repo):
    cv = generate_manifest.generate_manifest(repo)["cv"]
    assert set(cv) == {"en", "de"}
    assert set(cv["en"]) == {"generic", "mobile-app-dev", "portfolio"}
    assert set(cv["de"]) == {"generic"}
    assert cv["en"]["portfolio"]["latest"] == "Subhan Ahmed - CV - Portfolio.pdf"
    assert cv["de"]["generic"]["latest"] == "Subhan Ahmed - Lebenslauf.pdf"
    ts = cv["en"]["portfolio"]["timestamped"]
    assert ts.startswith("Subhan Ahmed - CV - Portfolio - ") and (repo / "cv" / "en" / ts).exists()


def test_manifest_generic_ignores_flavour_and_other_language_files(repo):
    stray = repo / "cv" / "en" / "Subhan Ahmed - CV - DE - 991231-2359.pdf"
    stray.write_bytes(b"%PDF-stray")
    generic = generate_manifest.generate_manifest(repo)["cv"]["en"]["generic"]
    assert generic["timestamped"] != stray.name
    assert generic["timestamped"].startswith("Subhan Ahmed - CV - ")
    assert (repo / "cv" / "en" / generic["timestamped"]).exists()


def test_manifest_lists_same_slug_in_two_languages(tmp_path):
    repo = make_repo(tmp_path)
    flavours_file = repo / "data" / "cv_flavours.json"
    flavours = json.loads(flavours_file.read_text(encoding="utf-8"))
    flavours.append({"slug": "portfolio", "language": "de", "label": "Portfolio"})
    flavours_file.write_text(json.dumps(flavours, ensure_ascii=False), encoding="utf-8")
    generate_cv.generate_all_cvs(repo)

    cv = generate_manifest.generate_manifest(repo)["cv"]
    assert cv["en"]["portfolio"]["latest"] == "Subhan Ahmed - CV - Portfolio.pdf"
    assert cv["de"]["portfolio"]["latest"] == "Subhan Ahmed - Lebenslauf - Portfolio.pdf"
