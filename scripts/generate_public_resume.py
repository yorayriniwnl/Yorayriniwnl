#!/usr/bin/env python3
"""Generate the privacy-safe public resume linked from the GitHub profile."""

from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.pagesizes import LETTER
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
    width, height = LETTER
    margin = 34
    content_width = width - margin * 2
    gap = 18
    right_width = 176
    left_width = content_width - right_width - gap
    left_x = margin
    right_x = left_x + left_width + gap

    raw_output.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(raw_output), pagesize=LETTER, pageCompression=1)
    pdf.setTitle(f'{profile["identity"]["name"]} - {profile["identity"]["role"]} Resume')
    pdf.setAuthor("Ayush Roy")
    pdf.setSubject("Public software engineering resume")

    pdf.setFillColor(INK)
    pdf.setFont(bold, 28)
    pdf.drawString(margin, height - 52, profile["identity"]["name"].upper())
    header_right_x = 357
    header_role, header_specialty = header_lines(profile)
    header_width = header_right_x - margin - 10
    pdf.setFillColor(CRIMSON)
    pdf.setFont(bold, fitted_font_size(header_role, bold, header_width, 10))
    pdf.drawString(margin, height - 70, header_role)
    pdf.setFont(bold, fitted_font_size(header_specialty, bold, header_width, 8.2))
    pdf.drawString(margin, height - 80, header_specialty)

    pdf.setFillColor(MUTED)
    pdf.setFont(regular, 7.4)
    pdf.drawRightString(width - margin, height - 47, profile["identity"]["location"])
    pdf.drawRightString(width - margin, height - 59, profile["availability"]["status"] + (" / remote" if profile["availability"]["remote"] else ""))
    draw_link(pdf, "ayushroy.dev@gmail.com", "mailto:ayushroy.dev@gmail.com", header_right_x, height - 73, regular, 7.1)
    draw_link(pdf, "yorayriniwnl.in", profile["contact"]["portfolio"], 470, height - 73, regular, 7.1)

    pdf.setStrokeColor(CRIMSON)
    pdf.setLineWidth(2)
    pdf.line(margin, height - 84, width - margin, height - 84)

    y_left = height - 107
    y_left = draw_section_title(pdf, "Profile", left_x, y_left, left_width, bold)
    y_left = draw_wrapped(
        pdf,
        profile["identity"]["positioning"] + " " + profile["availability"]["status"] + ".",
        left_x,
        y_left,
        left_width,
        regular,
        8.8,
        12,
        max_lines=4,
    ) - 7

    y_left = draw_section_title(pdf, "Experience", left_x, y_left, left_width, bold)
    experience = profile["experience"][0]
    pdf.setFillColor(INK)
    pdf.setFont(bold, 9.6)
    pdf.drawString(left_x, y_left, experience["role"])
    pdf.setFillColor(MUTED)
    pdf.setFont(regular, 7.1)
    pdf.drawRightString(left_x + left_width, y_left, experience["period"].upper())
    y_left -= 12
    pdf.setFillColor(CRIMSON)
    pdf.setFont(bold, 7.5)
    pdf.drawString(left_x, y_left, "BSNL / RGMTTC-CERTIFIED / CHENNAI HYBRID")
    y_left -= 12
    y_left = draw_wrapped(pdf, experience["summary"], left_x, y_left, left_width, regular, 8.1, 10.8, max_lines=3) - 9

    y_left = draw_section_title(pdf, "Selected Systems", left_x, y_left, left_width, bold)
    project_ids = ["portfolio", "vision", "zenith", "helios", "token-usage", "talks"]
    project_lookup = {project["id"]: project for project in profile["projects"]}
    vision_accuracy = next(
        proof for proof in project_lookup["vision"]["proof"] if "%" in proof
    )
    project_notes = {
        "portfolio": "4,000 GPU particles / 24 tests across 5 suites / automated GitHub sync",
        "helios": "FastAPI + WebSocket telemetry / targeted anomaly alerts / Docker Compose",
        "zenith": "3D roof planning / energy simulation / subsidy, ROI, and payback analysis",
        "vision": f"LBP + GLCM texture features / calibrated SVM / {vision_accuracy}",
        "token-usage": "Manifest V3 multi-AI usage cockpit / local-first capture / dashboards, exports, optional sync",
        "talks": "Realtime messaging / auth and conversation APIs / typed responsive UI",
    }
    for project_id in project_ids:
        project = project_lookup[project_id]
        pdf.setFillColor(INK)
        pdf.setFont(bold, 9.2)
        pdf.drawString(left_x, y_left, project["name"])
        status = project["status"].upper()
        pdf.setFillColor(CRIMSON)
        pdf.setFont(bold, 6.3)
        pdf.drawRightString(left_x + left_width, y_left, status)
        y_left -= 11
        y_left = draw_wrapped(pdf, project_notes[project_id], left_x, y_left, left_width, regular, 7.8, 10.2, MUTED, 2)
        label = project["live"] or project["repo"]
        visible = label.removeprefix("https://").removeprefix("www.")
        draw_link(pdf, visible, label, left_x, y_left, regular, 7.0)
        y_left -= 16

    y_left = draw_section_title(pdf, "Build Record", left_x, y_left, left_width, bold)
    for achievement in profile["achievements"]:
        pdf.setFillColor(CRIMSON)
        pdf.circle(left_x + 2.5, y_left + 2.5, 1.8, fill=1, stroke=0)
        y_left = draw_wrapped(pdf, achievement, left_x + 10, y_left, left_width - 10, regular, 7.9, 10.5, INK, 2) - 5

    y_right = height - 107
    y_right = draw_section_title(pdf, "Proof", right_x, y_right, right_width, bold)
    metric_width = (right_width - 8) / 2
    metrics = profile["proof"]
    draw_metric(pdf, metrics[0]["value"], "END-TO-END APPS", right_x, y_right, metric_width, bold, regular)
    draw_metric(pdf, metrics[1]["value"], "AUTOMATED TESTS", right_x + metric_width + 8, y_right, metric_width, bold, regular)
    y_right -= 51
    draw_metric(pdf, metrics[2]["value"], "HELD-OUT ACCURACY", right_x, y_right, metric_width, bold, regular)
    draw_metric(pdf, metrics[3]["value"], "DEVPOST BUILDS", right_x + metric_width + 8, y_right, metric_width, bold, regular)
    y_right -= 60

    y_right = draw_section_title(pdf, "Core Toolkit", right_x, y_right, right_width, bold)
    compact_skills = {
        "PRODUCT": "TypeScript, React, Next.js, Three.js, Tailwind",
        "BACKEND": "Python, FastAPI, Node.js, REST, WebSocket, SQL",
        "APPLIED ML": "OpenCV, Scikit-Learn, SVM, LBP, GLCM",
        "PLATFORM": "Docker, GitHub Actions, Vercel, Linux, Vitest",
    }
    for label, values in compact_skills.items():
        pdf.setFillColor(CRIMSON)
        pdf.setFont(bold, 7.1)
        pdf.drawString(right_x, y_right, label)
        y_right -= 10
        y_right = draw_wrapped(pdf, values, right_x, y_right, right_width, regular, 7.8, 10.2, MUTED, 3) - 8

    y_right = draw_section_title(pdf, "Education", right_x, y_right, right_width, bold)
    education = profile["education"][0]
    pdf.setFillColor(INK)
    pdf.setFont(bold, 8.6)
    pdf.drawString(right_x, y_right, "KIIT DEEMED UNIVERSITY")
    y_right -= 12
    y_right = draw_wrapped(pdf, education["degree"], right_x, y_right, right_width, regular, 7.8, 10.2, MUTED, 3)
    pdf.setFillColor(MUTED)
    pdf.setFont(regular, 7.3)
    pdf.drawString(right_x, y_right, education["period"])
    y_right -= 19

    y_right = draw_section_title(pdf, "Expanding Into", right_x, y_right, right_width, bold)
    expanding = "LLMs, RAG, AI agents, LangChain, AWS S3/Lambda, vector databases"
    y_right = draw_wrapped(pdf, expanding, right_x, y_right, right_width, regular, 7.8, 10.2, MUTED, 4) - 9

    y_right = draw_section_title(pdf, "Certifications", right_x, y_right, right_width, bold)
    for certification in profile["certifications"][:3]:
        pdf.setFillColor(INK)
        pdf.setFont(bold, 7.4)
        y_right = draw_wrapped(pdf, certification["name"], right_x, y_right, right_width, bold, 7.4, 9.6, INK, 2)
        pdf.setFillColor(MUTED)
        pdf.setFont(regular, 6.8)
        pdf.drawString(right_x, y_right, f"{certification['issuer']} / {certification['date']}")
        y_right -= 13

    y_right = draw_section_title(pdf, "Links", right_x, y_right, right_width, bold)
    links = [
        ("GitHub", profile["contact"]["github"]),
        ("LinkedIn", profile["contact"]["linkedin"]),
        ("Devpost", profile["contact"]["devpost"]),
    ]
    for label, url in links:
        draw_link(pdf, f"{label}  /  {url.removeprefix('https://').removeprefix('www.')}", url, right_x, y_right, regular, 6.9)
        y_right -= 13

    if min(y_left, y_right) < 38:
        raise RuntimeError(f"resume overflowed the one-page budget: left={y_left:.1f}, right={y_right:.1f}")

    pdf.setStrokeColor(HAIRLINE)
    pdf.setLineWidth(0.6)
    pdf.line(margin, 29, width - margin, 29)
    pdf.setFillColor(MUTED)
    pdf.setFont(regular, 6.3)
    pdf.drawString(margin, 18, "PUBLIC RESUME / UPDATED SEPTEMBER 2026")
    pdf.drawRightString(width - margin, 18, "BUILDING SOFTWARE FOR THE PHYSICAL WORLD")
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
    forbidden = ("+91", "89189", "yorayriniwnl@gmail.com", "deep learning", "CNN", "open to SWE internships", "open to software engineering internships", "CGPA")
    leaked = [term for term in forbidden if term.lower() in text.lower()]
    if leaked:
        raise RuntimeError(f"private or stale resume content found: {', '.join(leaked)}")

    profile = load_profile()
    required = ("ayushroy.dev@gmail.com", "LBP", "GLCM", "SVM", "78.5%", "BSNL", profile["identity"]["role"].upper(), profile["availability"]["status"])
    missing = [term for term in required if term not in text]
    if missing:
        raise RuntimeError(f"required resume evidence is missing: {', '.join(missing)}")

    annotations = sum(len(page.get("/Annots", [])) for page in reader.pages)
    if annotations < 10:
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
