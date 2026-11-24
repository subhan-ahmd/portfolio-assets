from pathlib import Path

import pytest

from cv_i18n import (
    cv_dirs,
    cv_filename,
    load_cv_strings,
    localize,
    skill_name,
    timestamped_regex,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_localize_merges_and_drops_i18n():
    item = {"id": 1, "slug": "x", "i18n": {"en": {"title": "T"}},
            "links": [{"url": "u", "i18n": {"en": {"label": "L"}}}]}
    assert localize(item, "en") == {
        "id": 1, "slug": "x", "title": "T", "links": [{"url": "u", "label": "L"}],
    }


def test_localize_keeps_null_fields():
    item = {"i18n": {"en": {"location": None, "description": []}}}
    assert localize(item, "en") == {"location": None, "description": []}


def test_localize_without_i18n_returns_copy():
    item = {"id": 0, "url": "mailto:x"}
    result = localize(item, "en")
    assert result == item and result is not item


def test_localize_missing_language_raises():
    with pytest.raises(KeyError):
        localize({"i18n": {"en": {}}}, "de")


def test_skill_name_neutral_and_translated():
    assert skill_name({"key": "flutter", "name": "Flutter"}, "de") == "Flutter"
    assert skill_name(
        {"key": "problem_solving", "i18n": {"en": {"name": "Problem Solving"}}}, "en"
    ) == "Problem Solving"


def test_cv_filename_variants():
    assert cv_filename("Subhan Ahmed", "CV") == "Subhan Ahmed - CV.pdf"
    assert cv_filename("Subhan Ahmed", "CV", timestamp="231126-1955") == \
        "Subhan Ahmed - CV - 231126-1955.pdf"
    assert cv_filename("Subhan Ahmed", "Lebenslauf", "Portfolio", "231126-1955") == \
        "Subhan Ahmed - Lebenslauf - Portfolio - 231126-1955.pdf"


def test_cv_filename_keeps_slash_lookalike():
    assert cv_filename("A", "CV", "AI/ML") == "A - CV - AI∕ML.pdf"


@pytest.mark.parametrize("label", ["A:B", "A*B", "A?B", 'A"B', "A<B", "A>B", "A|B", "A\\B", "A\nB"])
def test_cv_filename_rejects_invalid_chars(label):
    with pytest.raises(ValueError, match="label"):
        cv_filename("A", "CV", label)


def test_timestamped_regex_is_exact():
    generic = timestamped_regex("Subhan Ahmed", "CV")
    assert generic.fullmatch("Subhan Ahmed - CV - 231126-1955.pdf")
    assert not generic.fullmatch("Subhan Ahmed - CV - Portfolio - 231126-1955.pdf")
    assert not generic.fullmatch("Subhan Ahmed - CV.pdf")
    flavour = timestamped_regex("Subhan Ahmed", "CV", "AI/ML (x)")
    assert flavour.fullmatch("Subhan Ahmed - CV - AI∕ML (x) - 231126-1955.pdf")


def test_cv_dirs(tmp_path):
    assert cv_dirs(tmp_path, "de") == (
        tmp_path / "cv" / "de", tmp_path / "cv" / "latest" / "de",
    )


def test_cv_strings_languages_and_shape():
    strings = load_cv_strings(REPO_ROOT / "data")
    assert set(strings) == {"en", "de"}
    assert strings["en"]["contentLanguage"] == "en"
    assert strings["de"]["contentLanguage"] == "de"
    assert strings["de"]["documentWord"] == "Lebenslauf"
    assert strings["de"]["present"] == "heute"
    for lang in strings.values():
        assert len(lang["months"]) == 12
        assert set(lang["headings"]) == {"experience", "projects", "education", "skills", "languages"}
