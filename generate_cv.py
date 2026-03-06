#!/usr/bin/env python3
"""
CV PDF Generator
Generates a professional CV PDF from portfolio data files using reportlab.
"""

import json
import re
import shutil
from pathlib import Path
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.colors import black, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- Constants ---
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 0.55 * inch
AVAILABLE_WIDTH = PAGE_WIDTH - 2 * MARGIN
DATA_DIR = Path(__file__).parent / "data"
FONTS_DIR = Path(__file__).parent / "fonts"
OUTPUT_DIR = Path(__file__).parent
CV_GLOB = "*- CV - *.pdf"
BULLET_CHAR = "\u25cf"  # ● filled circle matching reference PDF
DIVIDER_COLOR = HexColor("#444444")
FOOTER_COLOR = HexColor("#999999")
SOURCE_URL = "github.com/subhan-ahmd/portfolio-assets"
LATEST_CV_URL = "raw.githubusercontent.com/subhan-ahmd/portfolio-assets/main/cv.pdf"

# --- Font Registration ---
pdfmetrics.registerFont(TTFont("Montserrat", str(FONTS_DIR / "Montserrat-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Montserrat-Bold", str(FONTS_DIR / "Montserrat-Bold.ttf")))
pdfmetrics.registerFontFamily("Montserrat", normal="Montserrat", bold="Montserrat-Bold")

BASE_FONT = "Montserrat"
BOLD_FONT = "Montserrat-Bold"


# --- Data Loading ---

def load_json(filename: str):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def filter_for_cv(items: list) -> list:
    return [item for item in items if item.get("showInCv", True)]


def get_cv_link(item: dict) -> dict | None:
    """Return the first link visible in CV, or None."""
    for link in item.get("links", []):
        if link.get("showInCv", True):
            return link
    return None


def format_date(date_str: str | None) -> str:
    if date_str is None:
        return "Present"
    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    return dt.strftime("%b %Y")


def format_date_range(start: str, end: str | None) -> str:
    return f"{format_date(start)} - {format_date(end)}"


def extract_handle(url: str) -> str:
    """Extract username/handle from a social URL."""
    match = re.search(r"(?:github\.com|linkedin\.com/in)/([^/]+)/?$", url)
    if match:
        return match.group(1)
    host_match = re.search(r"https?://([^/]+)", url)
    return host_match.group(1) if host_match else url


def sort_by_id(items: list) -> list:
    """Sort items by id descending (highest/latest first)."""
    return sorted(items, key=lambda item: item.get("id", 0), reverse=True)


def to_list(value) -> list:
    """Normalize a string or list value to a list."""
    if isinstance(value, str):
        return [value] if value else []
    return value if value else []


# --- Styles ---

def create_styles() -> dict:
    return {
        "name": ParagraphStyle(
            "Name", fontName=BOLD_FONT, fontSize=24,
            alignment=TA_CENTER, spaceAfter=2, leading=28,
        ),
        "position": ParagraphStyle(
            "Position", fontName=BOLD_FONT, fontSize=13,
            alignment=TA_CENTER, spaceAfter=4, leading=16,
        ),
        "info_line": ParagraphStyle(
            "InfoLine", fontName=BASE_FONT, fontSize=10,
            alignment=TA_CENTER, spaceAfter=2, leading=13,
        ),
        "summary": ParagraphStyle(
            "Summary", fontName=BASE_FONT, fontSize=10,
            alignment=TA_JUSTIFY, spaceAfter=4, leading=13,
        ),
        "section_heading": ParagraphStyle(
            "SectionHeading", fontName=BOLD_FONT, fontSize=11,
            spaceBefore=8, spaceAfter=0, leading=14,
        ),
        "entry_title": ParagraphStyle(
            "EntryTitle", fontName=BOLD_FONT, fontSize=10.5,
            alignment=TA_LEFT, leading=13,
        ),
        "entry_date": ParagraphStyle(
            "EntryDate", fontName=BOLD_FONT, fontSize=10.5,
            alignment=TA_RIGHT, leading=13,
        ),
        "entry_subtitle": ParagraphStyle(
            "EntrySubtitle", fontName=BASE_FONT, fontSize=9,
            alignment=TA_LEFT, spaceAfter=2, leading=12,
        ),
        "bullet": ParagraphStyle(
            "Bullet", fontName=BASE_FONT, fontSize=10,
            alignment=TA_JUSTIFY, leading=13,
            leftIndent=24, bulletIndent=8,
            bulletFontSize=7,
            spaceAfter=1,
        ),
        "skills_label": ParagraphStyle(
            "SkillsLabel", fontName=BOLD_FONT, fontSize=10.5,
            spaceAfter=2, leading=13,
        ),
        "skills_text": ParagraphStyle(
            "SkillsText", fontName=BASE_FONT, fontSize=10,
            alignment=TA_JUSTIFY, spaceAfter=6, leading=13,
        ),
        "entry_subtitle_small": ParagraphStyle(
            "EntrySubtitleSmall", fontName=BASE_FONT, fontSize=8,
            alignment=TA_RIGHT, spaceAfter=2, leading=11,
        ),
        "lang_bullet": ParagraphStyle(
            "LangBullet", fontName=BASE_FONT, fontSize=10,
            alignment=TA_LEFT, leading=13,
            leftIndent=24, bulletIndent=8,
            bulletFontSize=7,
            spaceAfter=1,
        ),
    }


# --- Reusable Builders ---

def hr(space_before=0, space_after=3):
    """Create a horizontal rule divider."""
    return HRFlowable(
        width="100%", thickness=0.75, color=DIVIDER_COLOR,
        spaceBefore=space_before, spaceAfter=space_after,
    )


def left_right_row(left_text: str, right_text: str, styles: dict,
                    left_style="entry_title", right_style="entry_date",
                    bold=True, left_ratio=0.7) -> Table:
    """Create a two-column row: left-aligned text + right-aligned text."""
    left = f"<b>{left_text}</b>" if bold else left_text
    right = f"<b>{right_text}</b>" if bold else right_text
    t = Table(
        [[
            Paragraph(left, styles[left_style]),
            Paragraph(right, styles[right_style]),
        ]],
        colWidths=[AVAILABLE_WIDTH * left_ratio, AVAILABLE_WIDTH * (1 - left_ratio)],
        hAlign="LEFT",
    )
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (1, 0), (1, 0), 10),
    ]))
    return t


def info_line(text: str, styles: dict) -> list:
    """Centered info line followed by an HR."""
    return [Paragraph(text, styles["info_line"]), hr()]


def section_heading(title: str, styles: dict) -> list:
    """Section title (uppercase bold) followed by a thin HR."""
    return [
        Paragraph(title.upper(), styles["section_heading"]),
        hr(),
    ]


def bullet_list(items: list, styles: dict) -> list:
    """Build bullet points from a list of strings."""
    return [
        Paragraph(item, styles["bullet"], bulletText=BULLET_CHAR)
        for item in items
    ] if items else []


def entry(title: str, date_range: str, styles: dict,
          subtitle: str = None, descriptions: list = None,
          is_first: bool = False, link: dict = None) -> list:
    """Build a complete entry: title+date row, optional subtitle, bullet list."""
    elements = []
    if not is_first:
        elements.append(Spacer(1, 6))
    if link:
        title = f'<a href="{link["url"]}" color="black">{title}</a>'
    elements.append(left_right_row(title, date_range, styles))
    if subtitle:
        elements.append(Paragraph(subtitle, styles["entry_subtitle"]))
    elements.extend(bullet_list(to_list(descriptions), styles))
    return elements


# --- Section Builders ---

def build_header(profile: dict, contacts: list, socials: list, styles: dict) -> list:
    elements = []

    # Name + Position
    elements.append(Paragraph(profile["name"].upper(), styles["name"]))
    elements.append(Paragraph(profile["position"], styles["position"]))
    elements.append(hr())

    # Contact line + HR
    contact_parts = [f'{profile["currentCity"]}, {profile["currentCountry"]}']
    for c in contacts:
        url = c.get("url", "")
        name = c.get("name", "")
        if url:
            contact_parts.append(f'<a href="{url}" color="black">{name}</a>')
        elif name:
            contact_parts.append(name)
    elements.extend(info_line(" <b>|</b> ".join(contact_parts), styles))

    # Social line + HR
    social_parts = []
    for s in socials:
        handle = extract_handle(s["url"])
        short = s["shortName"]
        if short.lower() != "ln":
            short = short.lower()
        social_parts.append(f'<a href="{s["url"]}" color="black">{short}@{handle}</a>')
    elements.extend(info_line(" <b>|</b> ".join(social_parts), styles))

    return elements


def build_summary(profile: dict, styles: dict) -> list:
    return [Paragraph(profile["shortDescription"], styles["summary"])]


def build_experience_section(experiences: list, styles: dict) -> list:
    elements = section_heading("Work Experience", styles)
    for i, exp in enumerate(experiences):
        subtitle_parts = [exp["association"]]
        if exp.get("location"):
            subtitle_parts.append(exp["location"])
        elements.extend(entry(
            title=exp["title"],
            date_range=format_date_range(exp["startDate"], exp.get("endDate")),
            styles=styles,
            subtitle=", ".join(subtitle_parts),
            descriptions=exp.get("shortDescription", exp.get("description", [])),
            is_first=(i == 0),
            link=get_cv_link(exp),
        ))
    return elements


def build_projects_section(projects: list, styles: dict) -> list:
    elements = section_heading("Projects", styles)
    for i, proj in enumerate(projects):
        title_text = proj["title"]
        if proj.get("technology"):
            title_text += f', {proj["technology"]}'
        elements.extend(entry(
            title=title_text,
            is_first=(i == 0),
            date_range=format_date_range(proj["startDate"], proj.get("endDate")),
            styles=styles,
            descriptions=proj.get("description", []),
            link=get_cv_link(proj),
        ))
    return elements


def build_education_section(education: list, styles: dict) -> list:
    elements = section_heading("Education", styles)
    for edu in education:
        date_text = format_date_range(edu["startDate"], edu.get("endDate")) if edu.get("showDurationInCv", True) else ""
        elements.append(left_right_row(
            edu["title"],
            date_text,
            styles,
        ))

        # Subtitle: University, Location  +  CGPA on the right
        left_text = edu["association"]
        if edu.get("location"):
            left_text += f', {edu["location"]}'

        right_text = ""
        if edu.get("showScoreInCv", True) and edu.get("obtainedScore") and edu.get("maximumScore"):
            right_text = f'{edu["markingScheme"]}: {edu["obtainedScore"]}/{edu["maximumScore"]}'

        if right_text:
            elements.append(left_right_row(
                left_text, right_text, styles,
                left_style="entry_subtitle", right_style="entry_subtitle_small",
                bold=False, left_ratio=0.8,
            ))
        else:
            elements.append(Paragraph(left_text, styles["entry_subtitle"]))

        descriptions = to_list(edu.get("shortDescription", edu.get("description", [])))
        elements.extend(bullet_list(descriptions, styles))

    return elements


def build_skills_section(skills: list, styles: dict) -> list:
    elements = section_heading("Skills", styles)
    for group in skills:
        elements.append(Paragraph(f'<b>{group["title"]}</b>', styles["skills_label"]))
        elements.append(Paragraph(" <b>|</b> ".join(group["skills"]), styles["skills_text"]))
    return elements


def build_languages_section(languages: list, styles: dict) -> list:
    elements = section_heading("Languages", styles)
    for lang in languages:
        elements.append(Paragraph(
            f'<b>{lang["name"]}</b> - {lang["fluency"]}',
            styles["lang_bullet"],
            bulletText=BULLET_CHAR,
        ))
    return elements


# --- Flavour Support ---

def apply_flavour(flavour, profile, experiences, projects, education, skills):
    """Apply a flavour overlay to raw data. Returns modified copies."""
    profile = dict(profile)
    if "position" in flavour:
        profile["position"] = flavour["position"]
    if "summary" in flavour:
        profile["shortDescription"] = flavour["summary"]

    def reorder_by_slugs(items, slugs):
        slug_map = {item["slug"]: item for item in items}
        return [slug_map[s] for s in slugs if s in slug_map]

    if "showExperiences" in flavour:
        experiences = reorder_by_slugs(experiences, flavour["showExperiences"])
    else:
        experiences = sort_by_id(filter_for_cv(experiences))

    if "showProjects" in flavour:
        projects = reorder_by_slugs(projects, flavour["showProjects"])
    else:
        projects = sort_by_id(filter_for_cv(projects))

    if "showEducation" in flavour:
        education = reorder_by_slugs(education, flavour["showEducation"])
    else:
        education = filter_for_cv(education)

    if "skills" in flavour:
        flavour_skills = flavour["skills"]
        new_skills = []
        for group in skills:
            group_slug = group.get("slug", "")
            if group_slug in flavour_skills:
                config = flavour_skills[group_slug]
                hide = set(config.get("hide", []))
                highlight = config.get("highlight", [])
                remaining = [s for s in group["skills"] if s not in hide]
                if not remaining:
                    continue
                highlighted = [s for s in highlight if s in remaining]
                non_highlighted = [s for s in remaining if s not in set(highlighted)]
                new_skills.append({**group, "skills": highlighted + non_highlighted})
            else:
                new_skills.append(group)
        skills = new_skills

    return profile, experiences, projects, education, skills


# --- Footer ---

def draw_footer(canvas, doc):
    canvas.saveState()
    font_size = 7
    canvas.setFont(BASE_FONT, font_size)
    canvas.setFillColor(FOOTER_COLOR)
    y = MARGIN * 0.4

    seg1 = "Autogenerated from "
    seg2 = SOURCE_URL
    # seg3 = "  |  "
    # seg4 = "Get latest here"

    total_width = sum(canvas.stringWidth(s, BASE_FONT, font_size) for s in [seg1, seg2])
    x = (PAGE_WIDTH - total_width) / 2

    for seg in [seg1, seg2]:
        canvas.drawString(x, y, seg)
        x += canvas.stringWidth(seg, BASE_FONT, font_size)

    # Clickable link over SOURCE_URL
    link1_x = (PAGE_WIDTH - total_width) / 2 + canvas.stringWidth(seg1, BASE_FONT, font_size)
    link1_w = canvas.stringWidth(seg2, BASE_FONT, font_size)
    canvas.linkURL(f"https://{SOURCE_URL}", (link1_x, y - 1, link1_x + link1_w, y + 7), relative=0)

    # # Clickable link over "Get latest here"
    # link2_x = link1_x + link1_w + canvas.stringWidth(seg3, BASE_FONT, font_size)
    # link2_w = canvas.stringWidth(seg4, BASE_FONT, font_size)
    # canvas.linkURL(f"https://{LATEST_CV_URL}", (link2_x, y - 1, link2_x + link2_w, y + 7), relative=0)

    canvas.restoreState()


# --- Main ---

def delete_old_cvs():
    """Delete all previously generated CV files."""
    for old in OUTPUT_DIR.glob(CV_GLOB):
        old.unlink()
    for old in OUTPUT_DIR.glob("cv-*.pdf"):
        old.unlink()
    stable = OUTPUT_DIR / "cv.pdf"
    if stable.exists():
        stable.unlink()


def generate_single_cv(profile, contacts, socials, experiences, projects,
                       education, skills, languages, timestamp,
                       label=None, slug=None):
    """Generate a single CV PDF. Returns (timestamped_path, stable_path)."""
    if label:
        filename = f"{profile['name']} - CV - {label} - {timestamp}.pdf"
        stable_name = f"cv-{slug}.pdf"
    else:
        filename = f"{profile['name']} - CV - {timestamp}.pdf"
        stable_name = "cv.pdf"

    output_file = OUTPUT_DIR / filename
    stable_file = OUTPUT_DIR / stable_name

    styles = create_styles()

    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title=f"{profile['name']} - CV",
        author=profile["name"],
    )

    story = []
    story.extend(build_header(profile, contacts, socials, styles))
    story.extend(build_summary(profile, styles))
    if experiences:
        story.extend(build_experience_section(experiences, styles))
    if projects:
        story.extend(build_projects_section(projects, styles))
    if education:
        story.extend(build_education_section(education, styles))
    story.extend(build_skills_section(skills, styles))
    story.extend(build_languages_section(languages, styles))

    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)

    shutil.copy2(output_file, stable_file)

    return output_file, stable_file


def generate_all_cvs():
    """Generate generic CV + all flavoured variants."""
    profile = load_json("profile.json")
    contacts = filter_for_cv(load_json("contacts.json"))
    socials = filter_for_cv(load_json("socials.json"))
    raw_experiences = load_json("experiences.json")
    raw_projects = load_json("projects.json")
    raw_education = load_json("education.json")
    skills = load_json("skills.json")
    languages = load_json("languages.json")
    flavours = load_json("cv_flavours.json")

    delete_old_cvs()

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%d%m%y-%H%M")
    generated = []

    # Generic CV (showInCv defaults, sorted by id desc)
    ts_path, stable_path = generate_single_cv(
        dict(profile), contacts, socials,
        sort_by_id(filter_for_cv(raw_experiences)),
        sort_by_id(filter_for_cv(raw_projects)),
        filter_for_cv(raw_education),
        skills, languages, timestamp,
    )
    generated.append(("generic", ts_path, stable_path))

    # Flavoured CVs
    for flavour in flavours:
        f_profile, f_exp, f_proj, f_edu, f_skills = apply_flavour(
            flavour, profile, raw_experiences, raw_projects, raw_education, skills,
        )
        ts_path, stable_path = generate_single_cv(
            f_profile, contacts, socials,
            f_exp, f_proj, f_edu,
            f_skills, languages, timestamp,
            label=flavour["label"], slug=flavour["slug"],
        )
        generated.append((flavour["slug"], ts_path, stable_path))

    return generated


def main():
    print("Generating CVs...")
    generated = generate_all_cvs()
    for slug, ts_path, stable_path in generated:
        print(f"  [{slug}] {ts_path.name} -> {stable_path.name}")
    print(f"Generated {len(generated)} CV(s)")


if __name__ == "__main__":
    main()
