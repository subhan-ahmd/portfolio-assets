import json
from pathlib import Path

import pytest

from cv_i18n import load_cv_strings, skill_name

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA = REPO_ROOT / "data"

# file -> fields that must live only under i18n.<lang>
TRANSLATABLE = {
    "experiences.json": ["title", "location", "description", "shortDescription"],
    "projects.json": ["description", "shortDescription"],
    "education.json": ["title", "location", "markingScheme", "description", "shortDescription"],
    "languages.json": ["name", "fluency"],
}
PROFILE_TRANSLATABLE = ["position", "intro", "shortDescription", "currentCountry"]


def load(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("filename,fields", TRANSLATABLE.items())
def test_translatable_fields_only_under_i18n(filename, fields):
    for item in load(DATA / filename):
        for field in fields:
            assert field not in item, f"{filename} {item.get('slug', item.get('id'))}: {field} in body"
            assert field in item["i18n"]["en"], f"{filename}: {field} missing from i18n.en"
        for link in item.get("links", []):
            assert "label" not in link and "label" in link["i18n"]["en"]


def test_profile_translatable_fields_only_under_i18n():
    profile = load(DATA / "profile.json")
    for field in PROFILE_TRANSLATABLE:
        assert field not in profile and field in profile["i18n"]["en"]


def test_skill_keys_are_unique():
    keys = [s["key"] for g in load(DATA / "skills.json") for s in g["skills"]]
    assert len(keys) == len(set(keys))


def test_skill_keys_follow_icon_slug_rule():
    for group in load(DATA / "skills.json"):
        for skill in group["skills"]:
            name = skill_name(skill, "en")
            expected = (name.lower().replace("#", "sharp").replace("+", "p")
                        .replace(".", "").replace(" ", "_").replace("/", "_"))
            assert skill["key"] == expected


def test_flavour_skill_refs_are_keys():
    keys = {s["key"] for g in load(DATA / "skills.json") for s in g["skills"]}
    for flavour in load(DATA / "cv_flavours.json"):
        for config in flavour.get("skills", {}).values():
            for ref in config.get("highlight", []) + config.get("hide", []):
                assert ref in keys, f"{flavour['slug']}: {ref}"


def test_flavours_have_language_and_no_i18n():
    languages = set(load_cv_strings(DATA))
    for flavour in load(DATA / "cv_flavours.json"):
        assert flavour["language"] in languages and "i18n" not in flavour


def _i18n_blocks(node):
    if isinstance(node, dict):
        if "i18n" in node:
            yield node["i18n"]
        for value in node.values():
            yield from _i18n_blocks(value)
    elif isinstance(node, list):
        for value in node:
            yield from _i18n_blocks(value)


@pytest.mark.parametrize("filename", sorted(p.name for p in DATA.glob("*.json")))
def test_every_text_block_has_german_with_same_fields(filename):
    for block in _i18n_blocks(load(DATA / filename)):
        assert set(block) == {"en", "de"}
        assert set(block["de"]) == set(block["en"])


def test_german_spoken_language_listed():
    langs = {l["i18n"]["en"]["name"]: l["i18n"] for l in load(DATA / "languages.json")}
    assert langs["German"]["en"]["fluency"] == "Elementary/A2"
    assert langs["German"]["de"] == {"name": "Deutsch", "fluency": "Grundkenntnisse/A2"}


def test_site_languages_file():
    assert load(DATA / "i18n" / "languages.json") == [
        {"code": "en", "name": "English", "default": True},
        {"code": "de", "name": "Deutsch"},
    ]


def test_german_portfolio_flavour():
    flavours = [f for f in load(DATA / "cv_flavours.json") if f["slug"] == "portfolio"]
    assert {f["language"] for f in flavours} == {"en", "de"}
    de = next(f for f in flavours if f["language"] == "de")
    assert de["hideProjects"] == ["sales_quotation_system"] and not de.get("disabled")
