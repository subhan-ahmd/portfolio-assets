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
    assert pdf_names(repo / "cv" / "latest" / "de") == {
        "Subhan Ahmed - Lebenslauf.pdf", "Subhan Ahmed - Lebenslauf - Portfolio.pdf",
    }
    en_ts = pdf_names(repo / "cv" / "en")
    assert len(en_ts) == 3 and all(n.startswith(f"{NAME} - CV") for n in en_ts)
    de_ts = pdf_names(repo / "cv" / "de")
    assert len(de_ts) == 2 and all(n.startswith(f"{NAME} - Lebenslauf - ") for n in de_ts)
    assert not list((repo / "cv").glob("*.pdf"))
    assert {(lang, slug) for lang, slug, _, _ in result} == {
        ("en", "generic"), ("en", "mobile-app-dev"), ("en", "portfolio"),
        ("de", "generic"), ("de", "portfolio"),
    }


def test_german_uses_german_strings(generated):
    repo, _ = generated
    text = pdf_text(repo / "cv" / "latest" / "de" / "Subhan Ahmed - Lebenslauf.pdf")
    for expected in ["BERUFSERFAHRUNG", "PROJEKTE", "AUSBILDUNG", "KENNTNISSE", "SPRACHKENNTNISSE",
                     "Jan 2025 - Jul 2026", "Mär 2025 - Aug 2025", "Okt 2026 - heute",
                     "Automatisch erstellt aus"]:
        assert expected in text, expected
    assert "Present" not in text and "WORK EXPERIENCE" not in text
    assert "Deutsch - Grundkenntnisse/A2" in text and "Softwareentwickler" in text


def test_english_lists_german_language(generated):
    repo, _ = generated
    text = pdf_text(repo / "cv" / "latest" / "en" / "Subhan Ahmed - CV.pdf")
    assert "German - Elementary/A2" in text and "Deutsch" not in text


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


def test_legacy_english_generic_link_kept(generated):
    repo, _ = generated
    legacy = repo / "cv" / "latest" / "Subhan Ahmed - CV.pdf"
    current = repo / "cv" / "latest" / "en" / "Subhan Ahmed - CV.pdf"
    assert legacy.exists()
    assert legacy.read_bytes() == current.read_bytes()


@pytest.mark.parametrize("path", [
    ("en", "Subhan Ahmed - CV.pdf"),
    ("en", "Subhan Ahmed - CV - Portfolio.pdf"),
    ("en", "Subhan Ahmed - CV - Mobile Application Developer.pdf"),
    ("de", "Subhan Ahmed - Lebenslauf.pdf"),
    ("de", "Subhan Ahmed - Lebenslauf - Portfolio.pdf"),
])
def test_education_latest_first(generated, path):
    repo, _ = generated
    text = pdf_text(repo / "cv" / "latest" / path[0] / path[1])
    assert text.index("M.Sc. in Computer Science International") < text.index("B.S. in Computer Science")


# --- Profile photo (showPhoto per flavour) ---

from pypdf import PdfReader as _Reader

DE_PORTFOLIO = ("de", "Subhan Ahmed - Lebenslauf - Portfolio.pdf")
NO_PHOTO = [
    ("en", "Subhan Ahmed - CV.pdf"),
    ("en", "Subhan Ahmed - CV - Portfolio.pdf"),
    ("en", "Subhan Ahmed - CV - Mobile Application Developer.pdf"),
    ("de", "Subhan Ahmed - Lebenslauf.pdf"),
]


def image_count(path: Path) -> int:
    return sum(len(page.images) for page in _Reader(path).pages)


@pytest.fixture(scope="module")
def with_photo(tmp_path_factory):
    repo = make_repo(tmp_path_factory.mktemp("photo"))
    shutil.copy2(REPO_ROOT / "profile.png", repo / "profile.png")
    generate_cv.generate_all_cvs(repo)
    return repo


@pytest.mark.parametrize("path", NO_PHOTO)
def test_cv_without_photo_unchanged(with_photo, generated, path):
    # A CV that doesn't show the photo must come out identical whether or not
    # profile.png exists (independent of other layout changes over time).
    repo, _ = generated
    new = with_photo / "cv" / "latest" / path[0] / path[1]
    old = repo / "cv" / "latest" / path[0] / path[1]
    assert len(_Reader(new).pages) == len(_Reader(old).pages)
    assert [p.extract_text() for p in _Reader(new).pages] == [p.extract_text() for p in _Reader(old).pages]
    assert image_count(new) == 0


def test_photo_flavour_has_image(with_photo):
    path = with_photo / "cv" / "latest" / DE_PORTFOLIO[0] / DE_PORTFOLIO[1]
    assert len(_Reader(path).pages[0].images) == 1


def test_missing_photo_file_skips_photo(generated):
    repo, _ = generated
    assert not (repo / "profile.png").exists()
    path = repo / "cv" / "latest" / DE_PORTFOLIO[0] / DE_PORTFOLIO[1]
    assert image_count(path) == 0
    assert "Softwareentwickler" in pdf_text(path)


def test_every_flavour_sets_show_photo():
    flavours = json.loads((REPO_ROOT / "data" / "cv_flavours.json").read_text(encoding="utf-8"))
    assert {f["slug"] + "/" + f["language"]: f.get("showPhoto") for f in flavours} == {
        f["slug"] + "/" + f["language"]: f["language"] == "de" for f in flavours
    }


@pytest.mark.parametrize("path,headings", [
    (("en", "Subhan Ahmed - CV.pdf"), ("WORK EXPERIENCE", "EDUCATION", "PROJECTS")),
    (("en", "Subhan Ahmed - CV - Portfolio.pdf"), ("WORK EXPERIENCE", "EDUCATION", "PROJECTS")),
    (("de", "Subhan Ahmed - Lebenslauf.pdf"), ("BERUFSERFAHRUNG", "AUSBILDUNG", "PROJEKTE")),
    (("de", "Subhan Ahmed - Lebenslauf - Portfolio.pdf"), ("BERUFSERFAHRUNG", "AUSBILDUNG", "PROJEKTE")),
])
def test_education_comes_before_projects(generated, path, headings):
    repo, _ = generated
    text = pdf_text(repo / "cv" / "latest" / path[0] / path[1])
    experience, education, projects = (text.index(h) for h in headings)
    assert experience < education < projects
