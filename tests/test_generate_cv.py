import json
import shutil
from pathlib import Path

import pytest
from pypdf import PdfReader

import generate_cv

REPO_ROOT = Path(__file__).resolve().parent.parent
NAME = "Subhan Ahmed"
EN_FILES = {
    "generic": "Subhan Ahmed - CV.pdf",
    "mobile-app-dev": "Subhan Ahmed - CV - Mobile Application Developer.pdf",
    "portfolio": "Subhan Ahmed - CV - Portfolio.pdf",
}


def make_repo(tmp: Path) -> Path:
    shutil.copytree(REPO_ROOT / "data", tmp / "data")
    shutil.copytree(REPO_ROOT / "fonts", tmp / "fonts")
    return tmp


def pdf_text(path: Path) -> str:
    return "".join(page.extract_text() for page in PdfReader(path).pages)


def pdf_names(folder: Path) -> set[str]:
    return {p.name for p in folder.glob("*.pdf")}


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    repo = make_repo(tmp_path_factory.mktemp("repo"))
    result = generate_cv.generate_all_cvs(repo)
    return repo, result


def test_outputs_per_language(generated):
    repo, result = generated
    assert pdf_names(repo / "cv" / "latest" / "en") == set(EN_FILES.values())
    assert pdf_names(repo / "cv" / "latest" / "de") == {"Subhan Ahmed - Lebenslauf.pdf"}
    en_ts = pdf_names(repo / "cv" / "en")
    assert len(en_ts) == 3 and all(n.startswith(f"{NAME} - CV") for n in en_ts)
    de_ts = pdf_names(repo / "cv" / "de")
    assert len(de_ts) == 1 and next(iter(de_ts)).startswith(f"{NAME} - Lebenslauf - ")
    assert not list((repo / "cv").glob("*.pdf"))
    assert {(lang, slug) for lang, slug, _, _ in result} == {
        ("en", "generic"), ("en", "mobile-app-dev"), ("en", "portfolio"), ("de", "generic"),
    }


def test_german_uses_german_strings(generated):
    repo, _ = generated
    text = pdf_text(repo / "cv" / "latest" / "de" / "Subhan Ahmed - Lebenslauf.pdf")
    for expected in ["BERUFSERFAHRUNG", "PROJEKTE", "AUSBILDUNG", "KENNTNISSE", "SPRACHKENNTNISSE",
                     "Jan 2025 - Jul 2026", "Mär 2025 - Aug 2025", "Okt 2026 - heute",
                     "Automatisch erstellt aus"]:
        assert expected in text, expected
    assert "Present" not in text and "WORK EXPERIENCE" not in text


def test_flavour_language_controls_structure(tmp_path):
    repo = make_repo(tmp_path)
    flavours_file = repo / "data" / "cv_flavours.json"
    flavours = json.loads(flavours_file.read_text(encoding="utf-8"))
    flavours.append({"slug": "portfolio", "language": "de", "label": "Portfolio",
                     "position": "Softwareentwickler", "hideProjects": ["sales_quotation_system"]})
    flavours_file.write_text(json.dumps(flavours, ensure_ascii=False), encoding="utf-8")

    generate_cv.generate_all_cvs(repo)

    de_portfolio = repo / "cv" / "latest" / "de" / "Subhan Ahmed - Lebenslauf - Portfolio.pdf"
    text = pdf_text(de_portfolio)
    assert "BERUFSERFAHRUNG" in text and "Softwareentwickler" in text
    assert "Sales Quotation Management System" not in text
    assert (repo / "cv" / "latest" / "en" / EN_FILES["portfolio"]).exists()


def test_cleanup_removes_every_pdf_under_cv(tmp_path):
    repo = make_repo(tmp_path)
    stale = [repo / "cv" / "old.pdf", repo / "cv" / "latest" / "old.pdf", repo / "cv" / "fr" / "x.pdf"]
    for path in stale:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"%PDF-stale")

    generate_cv.generate_all_cvs(repo)

    assert not any(p.exists() for p in stale)


def test_disabled_flavour_not_generated(generated):
    repo, _ = generated
    names = {p.name for p in (repo / "cv").rglob("*.pdf")}
    assert not any("Flutter Mobile" in n or "Full Stack" in n for n in names)
