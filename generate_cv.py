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
          is_first: bool = False) -> list:
    """Build a complete entry: title+date row, optional subtitle, bullet list."""
    elements = []
    if not is_first:
        elements.append(Spacer(1, 6))
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
    email = ""
    phone = ""
    for c in contacts:
        if "@" in c.get("name", ""):
            email = c["name"]
        else:
            phone = c["name"]
    contact_parts = [f'{profile["currentCity"]}, {profile["currentCountry"]}']
    if email:
        contact_parts.append(email)
    if phone:
        contact_parts.append(phone)
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
    sorted_exps = sort_by_id(experiences)
    for i, exp in enumerate(sorted_exps):
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
        ))
    return elements


def build_projects_section(projects: list, styles: dict) -> list:
    elements = section_heading("Projects", styles)
    sorted_projs = sort_by_id(projects)
    for i, proj in enumerate(sorted_projs):
        title_text = proj["title"]
        if proj.get("technology"):
            title_text += f', {proj["technology"]}'
        elements.extend(entry(
            title=title_text,
            is_first=(i == 0),
            date_range=format_date_range(proj["startDate"], proj.get("endDate")),
            styles=styles,
            descriptions=proj.get("description", []),
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


# --- Main ---

def delete_old_cvs():
    for old in OUTPUT_DIR.glob(CV_GLOB):
        old.unlink()


def generate_cv():
    profile = load_json("profile.json")
    contacts = filter_for_cv(load_json("contacts.json"))
    socials = filter_for_cv(load_json("socials.json"))
    experiences = filter_for_cv(load_json("experiences.json"))
    projects = filter_for_cv(load_json("projects.json"))
    education = filter_for_cv(load_json("education.json"))
    skills = load_json("skills.json")
    languages = load_json("languages.json")

    # Delete old CV files
    delete_old_cvs()

    # Generate timestamped filename
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%d%m%H%M")
    filename = f"{profile['name']} - CV - {timestamp}.pdf"
    output_file = OUTPUT_DIR / filename

    styles = create_styles()

    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=f"{profile['name']} - CV",
        author=profile["name"],
    )

    story = []
    story.extend(build_header(profile, contacts, socials, styles))
    story.extend(build_summary(profile, styles))
    story.extend(build_experience_section(experiences, styles))
    story.extend(build_projects_section(projects, styles))
    story.extend(build_education_section(education, styles))
    story.extend(build_skills_section(skills, styles))
    story.extend(build_languages_section(languages, styles))

    def draw_footer(canvas, doc):
        canvas.saveState()
        font_size = 7
        canvas.setFont(BASE_FONT, font_size)
        canvas.setFillColor(FOOTER_COLOR)
        y = MARGIN * 0.4

        seg1 = "Autogenerated from "
        seg2 = SOURCE_URL
        seg3 = "  |  "
        seg4 = "Get latest here"

        total_width = sum(canvas.stringWidth(s, BASE_FONT, font_size) for s in [seg1, seg2, seg3, seg4])
        x = (PAGE_WIDTH - total_width) / 2

        for seg in [seg1, seg2, seg3, seg4]:
            canvas.drawString(x, y, seg)
            x += canvas.stringWidth(seg, BASE_FONT, font_size)

        # Clickable link over SOURCE_URL
        link1_x = (PAGE_WIDTH - total_width) / 2 + canvas.stringWidth(seg1, BASE_FONT, font_size)
        link1_w = canvas.stringWidth(seg2, BASE_FONT, font_size)
        canvas.linkURL(f"https://{SOURCE_URL}", (link1_x, y - 1, link1_x + link1_w, y + 7), relative=0)

        # Clickable link over "Always up-to-date version"
        link2_x = link1_x + link1_w + canvas.stringWidth(seg3, BASE_FONT, font_size)
        link2_w = canvas.stringWidth(seg4, BASE_FONT, font_size)
        canvas.linkURL(f"https://{LATEST_CV_URL}", (link2_x, y - 1, link2_x + link2_w, y + 7), relative=0)

        canvas.restoreState()

    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)

    # Create stable cv.pdf copy
    stable_copy = OUTPUT_DIR / "cv.pdf"
    shutil.copy2(output_file, stable_copy)

    return output_file


def main():
    print("Generating CV PDF...")
    output_file = generate_cv()
    print(f"CV saved to {output_file}")


if __name__ == "__main__":
    main()
