#!/usr/bin/env python3
"""Generate the privacy-safe public resume linked from the GitHub profile."""

from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from profile_data import ROOT, load_design_tokens, load_profile


DEFAULT_OUTPUT = ROOT / "output" / "pdf" / "Ayush_Roy_Resume_Public.pdf"
TMP_DIR = ROOT / "tmp" / "pdfs"

TOKENS = load_design_tokens()
# A white-paper document needs its own contrast mapping, not dark-UI ink.
INK = HexColor("#21171b")
MUTED = HexColor("#65515a")
CRIMSON = HexColor(TOKENS["color"]["deepCrimson"])
DEEP_CRIMSON = HexColor(TOKENS["color"]["deepCrimson"])
PALE = HexColor("#fff1f3")
HAIRLINE = HexColor("#d9c8ce")
WHITE = HexColor("#ffffff")


def register_fonts() -> tuple[str, str]:
    regular = Path("C:/Windows/Fonts/arial.ttf")
    bold = Path("C:/Windows/Fonts/arialbd.ttf")
    if regular.is_file() and bold.is_file():
        pdfmetrics.registerFont(TTFont("ResumeSans", regular))
        pdfmetrics.registerFont(TTFont("ResumeSans-Bold", bold))
        return "ResumeSans", "ResumeSans-Bold"
    return "Helvetica", "Helvetica-Bold"


def wrapped_lines(text: str, font: str, size: float, width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and pdfmetrics.stringWidth(candidate, font, size) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def header_lines(profile: dict) -> tuple[str, str]:
    identity = profile["identity"]
    return identity["role"].upper(), f'/ {identity["specialty"].upper()}'


def fitted_font_size(
    text: str,
    font: str,
    max_width: float,
    start_size: float,
    min_size: float = 7.5,
    step: float = 0.1,
) -> float:
    size = start_size
    while size > min_size and pdfmetrics.stringWidth(text, font, size) > max_width:
        size = round(size - step, 2)
    return size


def draw_wrapped(
    pdf: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    font: str,
    size: float,
    leading: float,
    color: Color = INK,
    max_lines: int | None = None,
) -> float:
    lines = wrapped_lines(text, font, size, width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines and pdfmetrics.stringWidth(lines[-1] + "...", font, size) > width:
            lines[-1] = lines[-1].rsplit(" ", 1)[0]
        if lines:
            lines[-1] += "..."
    pdf.setFillColor(color)
    pdf.setFont(font, size)
    for line in lines:
        pdf.drawString(x, y, line)
        y -= leading
    return y


def draw_section_title(pdf: canvas.Canvas, title: str, x: float, y: float, width: float, bold: str) -> float:
    pdf.setFillColor(CRIMSON)
    pdf.setFont(bold, 8.3)
    pdf.drawString(x, y, title.upper())
    pdf.setStrokeColor(HAIRLINE)
    pdf.setLineWidth(0.65)
    pdf.line(x, y - 5, x + width, y - 5)
    return y - 17


def draw_link(pdf: canvas.Canvas, label: str, url: str, x: float, y: float, font: str, size: float) -> float:
    pdf.setFillColor(DEEP_CRIMSON)
    pdf.setFont(font, size)
    pdf.drawString(x, y, label)
    width = pdfmetrics.stringWidth(label, font, size)
    pdf.linkURL(url, (x, y - 2, x + width, y + size + 1), relative=0)
    return width


def draw_metric(pdf: canvas.Canvas, value: str, label: str, x: float, y: float, width: float, bold: str, regular: str) -> None:
    pdf.setFillColor(PALE)
    pdf.roundRect(x, y - 43, width, 43, 5, fill=1, stroke=0)
    pdf.setFillColor(CRIMSON)
    pdf.setFont(bold, 18)
    pdf.drawString(x + 8, y - 20, value)
    pdf.setFillColor(MUTED)
    pdf.setFont(regular, 5.9)
    pdf.drawString(x + 8, y - 34, label)


def build_resume(raw_output: Path) -> None:
    profile = load_profile()
    regular, bold = register_fonts()
    width, height = A4
    margin = 34
    content_width = width - margin * 2

    raw_output.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(raw_output), pagesize=A4, pageCompression=1)
    pdf.setTitle(f'{profile["identity"]["name"]} - {profile["identity"]["role"]} Resume')
    pdf.setAuthor("Ayush Roy")
    pdf.setSubject("Public software engineering resume")

    # Header
    pdf.setFillColor(INK)
    pdf.setFont(bold, 24)
    name = profile["identity"]["name"].upper()
    pdf.drawCentredString(width / 2, height - 43, name)

    role = profile["identity"]["role"]
    pdf.setFont(bold, fitted_font_size(role, bold, content_width, 11.2, min_size=9.0))
    pdf.drawCentredString(width / 2, height - 60, role)

    y = height - 77
    contact_parts = [
        ("ayushroy.dev@gmail.com", "mailto:ayushroy.dev@gmail.com"),
        ("GitHub", profile["contact"]["github"]),
        ("Portfolio", profile["contact"]["portfolio"]),
        ("LinkedIn", profile["contact"]["linkedin"]),
    ]
    x = margin
    pdf.setFont(regular, 7.8)
    for index, (label, url) in enumerate(contact_parts):
        if index:
            pdf.setFillColor(MUTED)
            pdf.drawString(x, y, "  |  ")
            x += pdfmetrics.stringWidth("  |  ", regular, 7.8)
        x += draw_link(pdf, label, url, x, y, regular, 7.8)

    pdf.setFillColor(MUTED)
    pdf.setFont(regular, 8.5)
    location = profile["identity"]["location"]
    pdf.drawRightString(width - margin, y, location)

    y -= 16
    summary = (
        "B.Tech CSCE student at KIIT (2027) building backend-heavy product systems with Python, "
        "TypeScript, PostgreSQL, Redis, realtime APIs, automated testing, Docker, and applied ML."
    )
    y = draw_wrapped(pdf, summary, margin, y, content_width, regular, 8.7, 11.2, MUTED, 2) - 6

    # Experience and selection
    y = draw_section_title(pdf, "Experience & Selection", margin, y, content_width, bold)
    pdf.setFillColor(INK)
    pdf.setFont(bold, 9.5)
    pdf.drawString(margin, y, "KPIT Technologies - Associate Engineer 2027 (Campus Selection)")
    pdf.setFillColor(MUTED)
    pdf.setFont(regular, 7.5)
    pdf.drawRightString(width - margin, y, "SELECTED AUG 2026")
    y -= 12
    y = draw_wrapped(
        pdf,
        "Selected through KIIT campus recruitment; Letter of Intent accepted. Role commencement and onboarding are pending, so this is listed as a selection rather than current employment.",
        margin + 8,
        y,
        content_width - 8,
        regular,
        8.2,
        10.6,
        INK,
        3,
    ) - 6

    experience = profile["experience"][0]
    pdf.setFillColor(INK)
    pdf.setFont(bold, 9.5)
    pdf.drawString(margin, y, "Bharat Sanchar Nigam Limited (BSNL) - Telecom & Data Network Intern")
    pdf.setFillColor(MUTED)
    pdf.setFont(regular, 7.5)
    pdf.drawRightString(width - margin, y, "JUN 2026")
    y -= 12
    y = draw_wrapped(
        pdf,
        "Completed a 4-week RGMTTC-certified hybrid program in Chennai covering telecom infrastructure, data-network systems, and operational concepts.",
        margin + 8,
        y,
        content_width - 8,
        regular,
        8.2,
        10.6,
        INK,
        2,
    ) - 7

    # Selected projects
    y = draw_section_title(pdf, "Selected Engineering Projects", margin, y, content_width, bold)
    projects = [
        {
            "title": "CandidateX - Candidate Capability Intelligence",
            "period": "SEP 2026 - PRESENT",
            "url": "https://github.com/yorayriniwnl/CandidateX",
            "stack": "Python, FastAPI, Next.js, PostgreSQL, Redis, Docker",
            "bullets": [
                "Built a research prototype for synthetic candidate documents and selected public technical evidence, producing provenance-linked evidence graphs, role-aware capability signals, contradiction diagnostics, and targeted interview probes.",
                "Implemented static repository analysis without executing untrusted code; the repository documents 131 backend unit, golden, property, security, database, and theorem tests plus GitHub Actions validation.",
                "Kept experiment provenance explicit: the 4,800-sample repository ablation is separate from the paper's 28,800 synthetic candidate-role benchmark; neither is claimed as real-world hiring validity.",
            ],
        },
        {
            "title": "Yor Talks V2 - Realtime Social Platform",
            "period": "2026",
            "url": "https://github.com/yorayriniwnl/yor-talksv2",
            "stack": "React, Vite, Express 5, Socket.IO, PostgreSQL, Drizzle, Redis",
            "bullets": [
                "Engineered authenticated REST and Socket.IO workflows, PostgreSQL/Drizzle persistence, Redis-backed queues, messaging, notifications, privacy controls, and server-owned authorization.",
                "Added regression coverage for audience visibility, stale-cache authorization, session boundaries, database migrations, failure handling, and browser flows; production deployment remains explicitly gated on external infrastructure checks.",
            ],
        },
        {
            "title": "Yor Token Usage - Privacy-Aware AI Usage Analytics",
            "period": "APR 2026 - PRESENT",
            "url": "https://github.com/yorayriniwnl/Yor_Token_Usage",
            "stack": "JavaScript, Chrome MV3, Node.js, PostgreSQL, Redis, Playwright",
            "bullets": [
                "Built a local-first Manifest V3 extension estimating token usage across ChatGPT, Claude, Gemini, Perplexity, and Grok without uploading prompt text.",
                "Added optional PostgreSQL/Redis sync, OIDC/JWKS architecture, idempotent batching, Playwright regressions, and explicit calibration/error-bound reporting.",
            ],
        },
    ]

    for project in projects:
        pdf.setFillColor(INK)
        pdf.setFont(bold, 9.35)
        pdf.drawString(margin, y, project["title"])
        pdf.setFillColor(MUTED)
        pdf.setFont(regular, 7.2)
        pdf.drawRightString(width - margin, y, project["period"])
        y -= 11

        link_label = project["url"].removeprefix("https://")
        x_after = draw_link(pdf, link_label, project["url"], margin, y, regular, 7.4)
        pdf.setFillColor(MUTED)
        pdf.setFont(regular, 7.4)
        pdf.drawString(margin + x_after + 7, y, "|  " + project["stack"])
        y -= 11

        for bullet_text in project["bullets"]:
            pdf.setFillColor(CRIMSON)
            pdf.circle(margin + 2.2, y + 2.2, 1.45, fill=1, stroke=0)
            y = draw_wrapped(
                pdf,
                bullet_text,
                margin + 9,
                y,
                content_width - 9,
                regular,
                8.05,
                10.1,
                INK,
                3,
            ) - 2
        y -= 2

    # Education
    y = draw_section_title(pdf, "Education", margin, y, content_width, bold)
    education = profile["education"][0]
    pdf.setFillColor(INK)
    pdf.setFont(bold, 9.3)
    pdf.drawString(margin, y, "KIIT Deemed University - B.Tech, Computer Science & Communication Engineering")
    pdf.setFillColor(MUTED)
    pdf.setFont(regular, 7.4)
    pdf.drawRightString(width - margin, y, "2023 - 2027")
    y -= 12
    y = draw_wrapped(
        pdf,
        "Relevant coursework: Data Structures & Algorithms, Operating Systems, DBMS, Computer Networks, Object-Oriented Programming.",
        margin,
        y,
        content_width,
        regular,
        8.05,
        10.1,
        INK,
        2,
    ) - 6

    # Skills
    y = draw_section_title(pdf, "Technical Skills", margin, y, content_width, bold)
    skill_lines = [
        ("Languages", "Python, TypeScript, JavaScript, SQL | Foundational: Java, C, C++"),
        ("Backend & Databases", "FastAPI, Flask, Node.js, Express, PostgreSQL, Redis, SQLAlchemy, REST APIs, WebSocket, Socket.IO"),
        ("Frontend", "React, Next.js, Vite, HTML/CSS, Tailwind CSS"),
        ("Testing", "Pytest, Playwright, Vitest, unit, integration, E2E testing"),
        ("DevOps & Tooling", "Docker, Docker Compose, Git, GitHub Actions, Linux, Vercel"),
        ("Applied ML", "OpenCV, scikit-learn, SVM, feature engineering, model evaluation"),
    ]
    for label, values in skill_lines:
        pdf.setFillColor(CRIMSON)
        pdf.setFont(bold, 7.9)
        pdf.drawString(margin, y, label + ":")
        label_width = pdfmetrics.stringWidth(label + ": ", bold, 7.9)
        pdf.setFillColor(INK)
        pdf.setFont(regular, 7.9)
        pdf.drawString(margin + label_width, y, values)
        y -= 10.0

    if y < 34:
        raise RuntimeError(f"resume overflowed the one-page budget: y={y:.1f}")

    pdf.setStrokeColor(HAIRLINE)
    pdf.setLineWidth(0.6)
    pdf.line(margin, 24, width - margin, 24)
    pdf.setFillColor(MUTED)
    pdf.setFont(regular, 6.2)
    pdf.drawString(margin, 14, "PUBLIC RESUME / UPDATED SEPTEMBER 2026")
    pdf.drawRightString(width - margin, 14, "BACKEND / FULL-STACK SOFTWARE ENGINEERING")
    pdf.showPage()
    pdf.save()

def sanitize_metadata(raw_path: Path, output_path: Path) -> None:
    profile = load_profile()
    reader = PdfReader(raw_path)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    writer.add_metadata(
        {
            "/Title": f'{profile["identity"]["name"]} - {profile["identity"]["role"]} Resume',
            "/Author": "Ayush Roy",
            "/Subject": "Public software engineering resume",
            "/Keywords": "full-stack, software engineering, applied machine learning",
            "/Creator": "",
            "/Producer": "",
        }
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as stream:
        writer.write(stream)


def validate_resume(output_path: Path) -> None:
    reader = PdfReader(output_path)
    if len(reader.pages) != 1:
        raise RuntimeError("public resume must remain exactly one page")

    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    forbidden = (
        "+91",
        "89189",
        "yorayriniwnl@gmail.com",
        "deep learning",
        "CNN",
        "open to SWE internships",
        "open to software engineering internships",
        "CGPA",
        "Associate Engineer · Automotive Technology Services",
        "Expanding Into",
        "LangChain",
    )
    leaked = [term for term in forbidden if term.lower() in text.lower()]
    if leaked:
        raise RuntimeError(f"private or stale resume content found: {', '.join(leaked)}")

    profile = load_profile()
    required = (
        "ayushroy.dev@gmail.com",
        "KPIT Technologies",
        "onboarding are pending",
        "CandidateX",
        "131 backend",
        "28,800 synthetic candidate-role benchmark",
        "Yor Talks V2",
        "Yor Token Usage",
        "BSNL",
        profile["identity"]["role"],
    )
    missing = [term for term in required if term not in text]
    if missing:
        raise RuntimeError(f"required resume evidence is missing: {', '.join(missing)}")

    annotations = sum(len(page.get("/Annots", [])) for page in reader.pages)
    if annotations < 7:
        raise RuntimeError("public resume lost one or more clickable links")

    metadata = reader.metadata or {}
    if metadata.get("/Creator") or metadata.get("/Producer"):
        raise RuntimeError("public resume contains tool or machine metadata")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = TMP_DIR / "Ayush_Roy_Resume_Public.raw.pdf"
    build_resume(raw_path)
    sanitize_metadata(raw_path, args.output)
    validate_resume(args.output)
    raw_path.unlink(missing_ok=True)
    print(f"wrote {args.output} ({args.output.stat().st_size / 1024:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
