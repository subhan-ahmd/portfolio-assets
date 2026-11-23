"""
Shared i18n helpers for CV generation and the asset manifest.

Data items keep language-neutral fields in their body and translatable text
under ``i18n.<lang>``; ``localize`` flattens one language back into the item.
CV filenames and folders are defined here so both scripts agree on them.
"""

import json
import re
from pathlib import Path

SLASH_LOOKALIKE = "∕"  # DIVISION SLASH: looks like "/", legal in filenames
INVALID_FILENAME_CHARS = re.compile(r'[\\:*?"<>|\x00-\x1f]')
TIMESTAMP_PATTERN = r"\d{6}-\d{4}"


def load_cv_strings(data_dir: Path) -> dict:
    """Load per-language CV text (headings, dates, document word)."""
    with open(data_dir / "i18n" / "cv_strings.json", "r", encoding="utf-8") as f:
        return json.load(f)


def localize_link(link: dict, lang: str) -> dict:
    return localize(link, lang)


def localize(item: dict, lang: str) -> dict:
    """Merge ``item["i18n"][lang]`` into the item body and drop ``i18n``."""
    result = {k: v for k, v in item.items() if k != "i18n"}
    if "i18n" in item:
        result.update(item["i18n"][lang])
    if isinstance(result.get("links"), list):
        result["links"] = [localize_link(link, lang) for link in result["links"]]
    return result


def skill_name(skill: dict, lang: str) -> str:
    """Display name of a skill: neutral ``name`` or ``i18n.<lang>.name``."""
    if "name" in skill:
        return skill["name"]
    return skill["i18n"][lang]["name"]


def _filename_part(label: str) -> str:
    if INVALID_FILENAME_CHARS.search(label):
        raise ValueError(f"CV label {label!r} contains a character not allowed in filenames")
    return label.replace("/", SLASH_LOOKALIKE)


def cv_filename(name: str, word: str, label: str | None = None,
                timestamp: str | None = None) -> str:
    """``{name} - {word}[ - {label}][ - {timestamp}].pdf``"""
    parts = [name, word]
    if label:
        parts.append(_filename_part(label))
    if timestamp:
        parts.append(timestamp)
    return " - ".join(parts) + ".pdf"


def timestamped_regex(name: str, word: str, label: str | None = None) -> re.Pattern:
    """Exact pattern for the timestamped filename of one CV."""
    prefix = cv_filename(name, word, label)[: -len(".pdf")]
    return re.compile(re.escape(prefix) + " - " + TIMESTAMP_PATTERN + re.escape(".pdf"))


def cv_dirs(repo_root: Path, lang: str) -> tuple[Path, Path]:
    """(timestamped dir, stable "latest" dir) for one language."""
    return repo_root / "cv" / lang, repo_root / "cv" / "latest" / lang
