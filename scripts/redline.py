"""Crimson editorial surfaces for the GitHub profile.

Each image owns its typography and has a separately composed narrow variant.
GitHub supplies the links and disclosures; SVG supplies the visual language.
Project photographs and the approved portrait are owned by generate_assets.
"""
from __future__ import annotations

import base64
import html
import math
import textwrap
from functools import lru_cache
from pathlib import Path

from profile_data import load_design_tokens

ROOT = Path(__file__).resolve().parents[1]
DESIGN_TOKENS = load_design_tokens()
COLORS = DESIGN_TOKENS["color"]
WORLD_TOKENS = DESIGN_TOKENS["worlds"]
RED, PAPER, MUTED = (COLORS[k] for k in ("crimson", "paper", "muted"))
LINE, BG = "#3b121b", "#080406"
REVISION = "command-v1"
ORDER = ("portfolio", "vision", "zenith", "helios", "token-usage", "talks")
SHORT = {"portfolio": "PORTFOLIO", "vision": "AI VS. REAL", "zenith": "ZENITH",
         "helios": "HELIOS", "token-usage": "TOKEN USAGE", "talks": "TALKS V2"}
# These short descriptions are editorial summaries, not new performance claims.
DECK = {
    "portfolio": "An interactive portfolio built around 3D, motion, and case studies.",
    "vision": "Texture features and a calibrated SVM distinguish AI images from real ones.",
    "zenith": "Plan rooftop solar, simulate output, and explore the financial tradeoffs.",
    "helios": "Follow meter readings from anomaly detection to operator investigation.",
    "token-usage": "Estimate AI token usage across five sites, with local history and exports.",
    "talks": "A realtime social platform for conversations, creators, and communities.",
}
NAV = {
    "portfolio": ("PORTFOLIO", "Explore the work", "product"),
    "resume": ("RÉSUMÉ", "Read the background", "file"),
    "linkedin": ("LINKEDIN", "Connect professionally", "network"),
    "live": ("OPEN PROJECT", "Explore the demo", "arrow"),
    "source": ("SOURCE CODE", "View on GitHub", "code"),
    "email": ("EMAIL", "Start a conversation", "mail"),
    "github": ("GITHUB", "Follow the builds", "code"),
    "devpost": ("DEVPOST", "Explore prototypes", "layers"),
    "steam": ("STEAM", "Off the clock", "target"),
}
SECTIONS = (
    ("projects", "01", "Selected systems.", "SIX PROJECTS / ONE BUILDER"),
    ("field", "02", "Out in the field.", "EXPERIENCE / EDUCATION"),
    ("arsenal", "03", "Tools of the trade.", "PRODUCT / BACKEND / APPLIED ML"),
    ("record", "04", "The build record.", "PUBLIC ACTIVITY / PROFILE VIEWS"),
    ("operator", "05", "Behind the work.", "PROCESS / PRINCIPLES / HUMAN"),
    ("channel", "06", "Let's build something.", "JOBS / COLLABORATION"),
)


def esc(value):
    return html.escape(str(value), quote=True)


@lru_cache(maxsize=4)
def font_data(name):
    return base64.b64encode((ROOT / "scripts" / "fonts" / name).read_bytes()).decode()


@lru_cache(maxsize=8)
def raster(path):
    return "data:image/jpeg;base64," + base64.b64encode((ROOT / path).read_bytes()).decode()


def text(value, x, y, size=18, fill=PAPER, face="sans", **attrs):
    extra = " ".join(f'{key.replace("_", "-")}="{esc(val)}"' for key, val in attrs.items())
    return f'<text x="{x}" y="{y}" class="{face}" font-size="{size}" fill="{fill}" {extra}>{esc(value)}</text>'


def lines(value, x, y, width, size=18, fill=MUTED, leading=None, face="sans"):
    # Conservative wrap; the render audit also measures actual browser bounds.
    leading = leading or round(size * 1.45)
    count = max(12, int(width / (size * (.62 if face == "mono" else .56))))
    rows = textwrap.wrap(value, count, break_long_words=False, break_on_hyphens=False)
    return "".join(text(row, x, y + i * leading, size, fill, face) for i, row in enumerate(rows)), y + len(rows) * leading


def rule(x, y, width):
    return f'<path d="M{x} {y}h{width}" stroke="{LINE}"/>'


def glyph(kind, x, y, size=24):
    paths = {
        "code": '<path d="m8 5-6 7 6 7m8-14 6 7-6 7m-3-16-2 18"/>',
        "product": '<rect x="2" y="3" width="20" height="15" rx="2"/><path d="M8 22h8m-4-4v4M2 8h20"/>',
        "layers": '<path d="m12 2 10 6-10 6L2 8Zm-10 11 10 6 10-6M2 18l10 6 10-6"/>',
        "file": '<path d="M5 2h9l5 5v15H5Zm9 0v6h5M8 12h8m-8 4h8"/>',
        "network": '<circle cx="5" cy="5" r="3"/><circle cx="19" cy="5" r="3"/><circle cx="12" cy="20" r="3"/><path d="m7 8 4 9m6-9-4 9M8 5h8"/>',
        "arrow": '<path d="M4 20 20 4M5 4h15v15"/>',
        "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m3 6 9 7 9-7"/>',
        "target": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 0v5m0 14v5M0 12h5m14 0h5"/>',
        "realtime": '<path d="M0 13h5l3-8 5 15 3-9 3 2h5"/>',
        "education": '<path d="m1 8 11-6 11 6-11 6ZM5 11v7q7 6 14 0v-7m4-3v12"/>',
        "telecom": '<path d="m7 22 5-13 5 13M8 18h8M4 4q-6 7 0 14M20 4q6 7 0 14"/><circle cx="12" cy="7" r="3"/>',
    }
    aliases = {"gpu": "product", "vision": "target", "ml": "target", "backend": "network", "platform": "layers",
               "expanding": "arrow", "mission": "target", "proof": "realtime", "stack": "layers",
               "apps": "product", "tests": "code", "accuracy": "target", "prototypes": "layers"}
    shape = paths.get(aliases.get(kind, kind), paths["code"])
    return f'<g data-kinetic-glyph="{esc(kind)}" transform="translate({x} {y}) scale({size/24})" fill="none" stroke="{RED}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{shape}</g>'


def page(title, width, height, body, desc="", layer="surface"):
    fonts = ''
    if 'class="serif"' in body:
        fonts += f"@font-face{{font-family:Editorial;src:url(data:font/woff2;base64,{font_data('cormorant-garamond-600.woff2')}) format('woff2');font-weight:600}}"
    if 'class="mono"' in body:
        fonts += f"@font-face{{font-family:Mono;src:url(data:font/woff2;base64,{font_data('dm-mono-500.woff2')}) format('woff2');font-weight:500}}"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description" data-visual-treatment="{REVISION}" data-visual-layer="{layer}">
<title id="title">{esc(title)}</title><desc id="description">{esc(desc or title)}</desc>
<defs><style>
{fonts}
.sans{{font-family:Arial,Helvetica,sans-serif}}.serif{{font-family:Editorial,Georgia,serif;font-weight:600}}.mono{{font-family:Mono,monospace;font-weight:500}}
.edge-flow{{stroke-dasharray:56 720;animation:flow 16s linear infinite}}.beacon{{animation:beacon 5s ease-in-out infinite}}
@keyframes flow{{to{{stroke-dashoffset:-776}}}}@keyframes beacon{{0%,100%{{opacity:.4}}50%{{opacity:1}}}}
@media (prefers-reduced-motion: reduce){{.edge-flow,.beacon{{animation:none!important}}}}
</style><linearGradient id="rim"><stop stop-color="{RED}"/><stop offset=".45" stop-color="{LINE}"/><stop offset="1" stop-color="{BG}"/></linearGradient>
<radialGradient id="depth" cx="100%" cy="100%" r="95%"><stop stop-color="#8f0014" stop-opacity=".33"/><stop offset=".62" stop-color="#30050e" stop-opacity=".14"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
<linearGradient id="shade"><stop stop-color="{BG}"/><stop offset=".45" stop-color="{BG}" stop-opacity=".94"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></linearGradient>
<clipPath id="frame"><rect x="1" y="1" width="{width-2}" height="{height-2}" rx="12"/></clipPath></defs>
<g clip-path="url(#frame)"><rect width="{width}" height="{height}" fill="{BG}"/><rect width="{width}" height="{height}" fill="url(#depth)"/>{body}</g>
<g aria-hidden="true" pointer-events="none"><rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="12" fill="none" stroke="{LINE}"/>
<path d="M18 .5H{width-18}" stroke="url(#rim)"/><path class="edge-flow" d="M18 .5H{width-18}" stroke="{RED}" opacity=".75"/></g></svg>'''


def button(label, subtitle, kind, width=180):
    b = glyph(kind, 15, 19, 22) + text(label, 48, 25, 14, PAPER, "mono")
    b += text(subtitle, 48, 43, 11, MUTED)
    return page(label, width, 62, b, subtitle, "control")


def section(index, title, subtitle, mobile=False):
    w = 360 if mobile else 720
    b = text(f"SYS / {index} / 06", 20, 35, 11 if mobile else 12, RED, "mono")
    b += text(subtitle, 113 if mobile else 128, 34, 9.5 if mobile else 11, MUTED, "mono")
    b += text(title, 20, 81, 34 if mobile else 43, PAPER, "serif")
    if not mobile:
        b += f'<path d="M610 82h56m10-26 18 18m-6-18 18 18m-6-18 18 18" stroke="{RED}" stroke-width="2"/>'
        b += f'<circle cx="620" cy="30" r="3" fill="{RED}" class="beacon"/>'
    return page(title, w, 108, b)


def identity(profile, mobile=False):
    w, h = (360, 462) if mobile else (720, 318)
    art = raster(profile["visual_contract"]["delivery"]["supporting_art"]["identity"])
    if mobile:
        b = f'<image href="{art}" x="0" y="0" width="{w}" height="188" preserveAspectRatio="xMidYMid slice"/>'
        b += f'<rect x="0" y="0" width="{w}" height="188" fill="{BG}" opacity=".42"/>'
        b += '<path d="M0 176H360" stroke="url(#rim)" stroke-width="2"/>'
        cx, cy = 302, 76
        b += f'<circle cx="{cx}" cy="{cy}" r="55" fill="none" stroke="{RED}" opacity=".38" stroke-dasharray="2 7"/>'
        b += f'<circle cx="{cx}" cy="{cy}" r="39" fill="none" stroke="{RED}" opacity=".52"/>'
        b += f'<circle cx="{cx}" cy="{cy}" r="18" fill="{LINE}" stroke="{RED}"/>'
        b += f'<circle cx="{cx}" cy="{cy}" r="4" fill="{PAPER}" class="beacon"/>'
        b += text("YOR / ENTRY 00", 22, 214, 11, RED, "mono")
        b += text("Interfaces with intent.", 22, 255, 31, PAPER, "serif")
        b += text("Systems with depth.", 22, 292, 31, PAPER, "serif")
        b += text("CURRENT / " + profile["identity"]["role"].upper(), 22, 319, 9.2, RED, "mono")
        body, _ = lines("Full-stack products, realtime systems, and applied ML.", 22, 352, 316, 15)
        b += body
    else:
        b = f'<image href="{art}" x="0" y="0" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice"/>'
        b += f'<rect width="{w}" height="{h}" fill="{BG}" opacity=".66"/><rect width="{w}" height="{h}" fill="url(#shade)"/>'
        b += '<path d="M0 0H720M0 8H720" stroke="url(#rim)" opacity=".75"/>'
        b += text("YOR / OPERATOR PROFILE / ENTRY 00", 24, 35, 11, RED, "mono")
        b += text("Interfaces with intent.", 24, 91, 42, PAPER, "serif")
        b += text("Systems with depth.", 24, 133, 42, PAPER, "serif")
        b += text("CURRENT / " + profile["identity"]["role"].upper(), 25, 164, 10.5, RED, "mono")
        body, _ = lines("Full-stack products, realtime systems, and applied ML.", 25, 197, 414, 16)
        b += body
        cx, cy = 586, 145
        b += f'<circle cx="{cx}" cy="{cy}" r="96" fill="none" stroke="{LINE}" stroke-width="1"/>'
        b += f'<circle cx="{cx}" cy="{cy}" r="78" fill="none" stroke="{RED}" opacity=".55" stroke-dasharray="3 7"/>'
        b += f'<circle cx="{cx}" cy="{cy}" r="57" fill="none" stroke="{RED}" opacity=".42"/>'
        for i in range(6):
            angle = (-90 + i * 60) * 3.141592653589793 / 180
            nx, ny = cx + 78 * math.cos(angle), cy + 78 * math.sin(angle)
            b += f'<path d="M{cx} {cy}L{nx:.1f} {ny:.1f}" stroke="{LINE}"/>'
            b += f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="4" fill="{RED}" class="beacon"/>'
        b += f'<circle cx="{cx}" cy="{cy}" r="26" fill="{BG}" stroke="{RED}" stroke-width="1.5"/>'
        b += text("YOR", cx, cy+6, 16, PAPER, "mono", text_anchor="middle")
        b += text("06 / SELECTED SYSTEMS", cx, cy+111, 8.7, MUTED, "mono", text_anchor="middle")
    b += rule(22, h-46, w-44)
    b += text("INDIA / REMOTE", 22, h-23, 10.5, MUTED, "mono")
    b += text(profile["availability"]["status"].upper(), w-22, h-23, 10, PAPER, "mono", text_anchor="end")
    return page(f'Ayush Roy — {profile["identity"]["role"]} and applied ML builder', w, h, b,
                profile["identity"]["positioning"] + " " + profile["availability"]["status"] + ". Illustrative developer studio.")


def signal(mobile=False):
    labels = (("PRODUCT", "product"), ("REALTIME", "realtime"), ("COMPUTER VISION", "vision"),
              ("3D / WEB", "gpu"), ("APPLIED ML", "ml"), ("PHYSICAL SYSTEMS", "telecom"))
    w = 360 if mobile else 720
    cols, cell_h, gap_x = (2, 42, 8) if mobile else (3, 36, 8)
    margin = 18
    cell_w = (w - margin * 2 - gap_x * (cols - 1)) / cols
    b = ''
    for i, (label, kind) in enumerate(labels):
        col, row = i % cols, i // cols
        x, y = margin + col * (cell_w + gap_x), 8 + row * (cell_h + 7)
        b += f'<path d="M{x} {y+8}v{cell_h-16}m0-8h5m{cell_w-5} 0h-5" stroke="{LINE}"/>'
        b += glyph(kind, x+10, y+8, 19 if mobile else 18)
        b += text(label, x+39, y+25, 10.2 if mobile else 10.5, PAPER, "mono")
        b += f'<circle cx="{x+cell_w-9}" cy="{y+cell_h/2}" r="2" fill="{RED}" class="beacon"/>'
    row_count = (len(labels) + cols - 1) // cols
    height = 8 + row_count * (cell_h + 7) - 7 + 8
    return page("Product, realtime systems, computer vision, 3D, applied ML and physical systems", w, height, b)


def proof_card(item):
    b = glyph(item["id"], 296, 24, 26) + text(item["value"], 22, 68, 57, PAPER, "serif")
    b += text(item["label"], 22, 97, 12, RED, "mono")
    detail, end = lines(item["detail"], 22, 124, 302, 13)
    return page(item["label"], 350, max(172, end+18), b+detail, item["detail"])


def summary(project, mobile=False):
    w, margin = (360 if mobile else 720), 22
    main_width = w-44 if mobile else 520
    kind={"portfolio":"product","vision":"target","zenith":"target","helios":"realtime","token-usage":"layers","talks":"network"}[project["id"]]
    accent = WORLD_TOKENS[project["id"]]["accent"]
    b = f'<path d="M0 0h{w}M0 5h{w}" stroke="{accent}" opacity=".45"/>'
    b += text(f'SECTOR {project["order"]:02d} / {project["status"].upper()}', margin, 29, 10.5, accent, "mono")
    b += glyph(kind,w-47,13,22)
    if mobile:
        title, title_end = lines(project["name"].upper(), margin, 66, main_width, 22 if len(project["name"]) > 24 else 25, PAPER, 28)
        b += title
        y = title_end + 4
        deck, end = lines(DECK[project["id"]], margin, y, main_width, 15.5, PAPER, 22)
        b += deck + rule(margin, end+7, main_width)
        stack, end = lines(" / ".join(project["stack"][:4]), margin, end+27, main_width, 11.5, MUTED, 17, "mono")
        b += text("STACK / ", margin, end+5, 9.5, accent, "mono") + stack
        height = end+35
    else:
        title, title_end = lines(project["name"].upper(), margin, 70, main_width, 27, PAPER, 32)
        b += title
        deck, end = lines(DECK[project["id"]], margin, title_end+3, main_width, 17.5, PAPER, 25)
        b += deck + rule(margin, end+6, main_width)
        b += text("STACK / ", margin, end+25, 9.5, accent, "mono")
        stack, stack_end = lines(" / ".join(project["stack"][:4]), margin+63, end+25, main_width-63, 12.5, MUTED, 18, "mono")
        b += stack
        cx, cy = w-86, 94
        b += f'<circle cx="{cx}" cy="{cy}" r="47" fill="{BG}" stroke="{LINE}" stroke-width="7"/>'
        b += f'<circle cx="{cx}" cy="{cy}" r="47" fill="none" stroke="{accent}" stroke-width="2" stroke-dasharray="2 8"/>'
        b += f'<circle cx="{cx}" cy="{cy}" r="34" fill="none" stroke="{LINE}" stroke-dasharray="2 5"/>'
        b += text(f'{project["order"]:02d}', cx, cy+7, 24, PAPER, "serif", text_anchor="middle")
        b += text("SECTOR / 06", cx, cy+24, 8.5, MUTED, "mono", text_anchor="middle")
        b += text("PROJECT SECTOR", cx, cy+71, 8, accent, "mono", text_anchor="middle")
        height = max(end+49, stack_end+10, 172)
    return page(project["name"], w, height, b, project["summary"], "project-summary")


def system_atlas(profile, mobile=False):
    """Render the six curated projects as one static, scan-friendly command map."""
    projects = {project["id"]: project for project in profile["projects"]}
    kinds = {"portfolio":"product", "vision":"target", "zenith":"target", "helios":"realtime",
             "token-usage":"layers", "talks":"network"}
    if mobile:
        w, h = 360, 742
        b = text("SYSTEMS ARCHIVE", 20, 34, 18, PAPER, "serif")
        b += text("SIX SECTORS / INDEXED BELOW", 20, 57, 9.5, RED, "mono")
        b += f'<circle cx="310" cy="40" r="24" fill="{BG}" stroke="{RED}"/><circle cx="310" cy="40" r="14" fill="none" stroke="{LINE}" stroke-dasharray="2 4"/>'
        b += text("06", 310, 44, 11, PAPER, "mono", text_anchor="middle")
        b += f'<path d="M16 96v558" stroke="{LINE}" stroke-width="2"/>'
        for i, project_id in enumerate(ORDER):
            project = projects[project_id]
            accent = WORLD_TOKENS[project_id]["accent"]
            x, y, pw, ph = 28, 98+i*91, 314, 76
            b += f'<path d="M{x+10} {y}h{pw-10}l10 10v{ph-20}l-10 10H{x}v-{ph-10}Z" fill="#0d070a" stroke="{LINE}"/>'
            b += f'<path d="M{x} {y+11}v{ph-22}" stroke="{accent}" stroke-width="3"/>'
            b += f'<circle cx="16" cy="{y+ph/2}" r="4" fill="{accent}" class="beacon"/>'
            b += text(f'{i+1:02d}', x+16, y+29, 14, accent, "mono")
            b += text(SHORT[project_id], x+60, y+28, 13.5, PAPER, "mono")
            b += text(project["status"].upper(), x+60, y+52, 9.5, MUTED, "mono")
            b += glyph(kinds[project_id], x+pw-29, y+18, 17)
            for tick in range(6):
                tx = x+60+tick*9
                b += f'<rect x="{tx}" y="{y+59}" width="6" height="3" fill="{accent if tick == i else LINE}"/>'
        b += text("SELECT A PROJECT BELOW TO OPEN ITS DOSSIER", 20, 715, 9, MUTED, "mono")
    else:
        w, h = 720, 408
        b = text("COMMAND DECK / SELECTED SYSTEMS", 22, 32, 11.5, RED, "mono")
        b += text("06 PROJECT WORLDS / INDEXED BELOW", 698, 32, 9, MUTED, "mono", text_anchor="end")
        b += f'<path d="M18 48h684" stroke="{LINE}"/>'
        cx, cy = 360, 225
        xs, top_y, bottom_y, pw, ph = (17, 253, 489), 66, 300, 214, 76
        for i, project_id in enumerate(ORDER):
            col, row = i % 3, i // 3
            x, y = xs[col], top_y if row == 0 else bottom_y
            ax = x + pw/2
            accent = WORLD_TOKENS[project_id]["accent"]
            if row == 0:
                ex = cx + (ax-cx)*.24
                ey = cy - 56
                path = f'M{ax} {y+ph} C{ax} {y+ph+18} {ex} {ey-20} {ex} {ey}'
            else:
                ex = cx + (ax-cx)*.24
                ey = cy + 56
                path = f'M{ex} {ey} C{ex} {ey+20} {ax} {y-18} {ax} {y}'
            b += f'<path d="{path}" fill="none" stroke="{accent}" stroke-opacity=".42" stroke-width="1.2" class="edge-flow"/>'
            b += f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="3" fill="{accent}" class="beacon"/>'
        b += f'<circle cx="{cx}" cy="{cy}" r="63" fill="{BG}" stroke="{LINE}" stroke-width="8"/>'
        b += f'<circle cx="{cx}" cy="{cy}" r="63" fill="none" stroke="{RED}" stroke-width="2" stroke-dasharray="90 306" transform="rotate(-90 {cx} {cy})"/>'
        b += f'<circle cx="{cx}" cy="{cy}" r="48" fill="none" stroke="{LINE}" stroke-dasharray="2 6"/>'
        b += f'<circle cx="{cx}" cy="{cy}" r="33" fill="#10070b" stroke="{RED}"/>'
        b += text("YOR", cx, cy-1, 17, PAPER, "mono", text_anchor="middle")
        b += text("06 SYSTEMS", cx, cy+17, 8.5, RED, "mono", text_anchor="middle")
        for i, project_id in enumerate(ORDER):
            project = projects[project_id]
            accent = WORLD_TOKENS[project_id]["accent"]
            col, row = i % 3, i // 3
            x, y = xs[col], top_y if row == 0 else bottom_y
            b += f'<path d="M{x+10} {y}h{pw-10}l10 10v{ph-20}l-10 10H{x}v-{ph-10}Z" fill="#0d070a" stroke="{LINE}"/>'
            b += f'<path d="M{x} {y+11}v{ph-22}" stroke="{accent}" stroke-width="3"/>'
            b += text(f'SECTOR {i+1:02d} / {project["status"].upper()}', x+13, y+22, 8.7, accent, "mono")
            b += text(SHORT[project_id], x+13, y+47, 11.4, PAPER, "mono")
            b += glyph(kinds[project_id], x+pw-32, y+14, 17)
            for tick in range(6):
                tx = x+13+tick*9
                b += f'<rect x="{tx}" y="{y+59}" width="6" height="3" fill="{accent if tick == i else LINE}"/>'
        b += text("SYSTEM MAP / PROJECT LINKS AND DETAILS FOLLOW", 22, 394, 9, MUTED, "mono")
    names = "; ".join(f'{projects[key]["name"]} ({projects[key]["status"]})' for key in ORDER)
    return page("Six-sector systems command atlas", w, h, b,
                "Illustrative static systems map. " + names + ". Project links and details follow the map.", "systems-atlas")


def dossier(project, mobile=False):
    w = 360 if mobile else 720
    b = text(project["name"].upper(), 24, 35, 14 if mobile else 19, PAPER, "mono")
    b += text(project["status"].upper(), 24, 59, 11, RED, "mono")
    y = 96
    for label, content, kind in (
        ("THE IDEA", [project["summary"]], "mission"),
        ("WHAT'S BUILT", project["proof"], "proof"),
        ("TECHNOLOGY", [" / ".join(project["stack"])], "stack"),
    ):
        b += glyph(kind, 24, y-15, 19) + text(label, 55, y, 12, RED, "mono")
        y += 29
        for item in content:
            copy, end = lines(item, 24, y, w-48, 15 if mobile else 17)
            b += copy
            y = end + 10
        b += rule(24, y-4, w-48)
        y += 29
    b += text(project["period"], 24, y-2, 12, MUTED)
    return page(project["name"] + " — project details", w, y+20, b, " ".join(project["proof"]))


def field(profile, mobile=False):
    w = 360 if mobile else 720
    exp, edu = profile["experience"][0], profile["education"][0]
    b = ''
    y = 34
    for label, title, subtitle, description, kind in (
        (exp["period"].upper(), "BSNL", exp["role"], exp["summary"], "telecom"),
        (edu["period"].upper(), "KIIT", edu["degree"], " / ".join(edu["coursework"]), "education"),
    ):
        b += glyph(kind, w-50, y-17, 26) + text(label, 24, y, 11, RED, "mono")
        b += text(title, 24, y+42, 38, PAPER, "serif")
        sub, end = lines(subtitle, 24, y+70, w-48, 17, PAPER)
        detail, end = lines(description, 24, end+8, w-48, 15)
        b += sub + detail
        b += rule(24, end+3, w-48)
        y = end + 40
    return page("Experience and education", w, y-8, b, f'{exp["organization"]}. {edu["institution"]}. {edu["degree"]}.')


def skills(profile, mobile=False):
    w = 360 if mobile else 720
    y, b = 28, ''
    names = {"product": "Product & interface", "backend": "Backend & realtime", "ml": "Applied machine learning", "platform": "Platform & delivery", "expanding": "Currently exploring"}
    for key, label in names.items():
        b += glyph(key, 24, y-6, 23) + text(label, 61, y+12, 19, PAPER, "sans", font_weight="600")
        y += 45
        x = 24
        for item in profile["skills"][key]:
            chip_w = len(item)*7.25+22
            if x+chip_w > w-24:
                x = 24
                y += 38
            b += f'<rect x="{x}" y="{y-18}" width="{chip_w}" height="29" rx="5" fill="#16090e" stroke="{LINE}"/>'
            b += text(item, x+11, y+1, 12, MUTED, "mono")
            x += chip_w+8
        y += 39
        b += rule(24, y-3, w-48)
        y += 29
    return page("Technical range", w, y-8, b, "; ".join(f'{k}: {", ".join(v)}' for k,v in profile["skills"].items()))


def arsenal(profile, mobile=False):
    w, h = (360, 218) if mobile else (720, 190)
    art = raster(profile["visual_contract"]["delivery"]["supporting_art"]["atlas"])
    b = f'<image href="{art}" x="0" y="0" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice"/><rect width="{w}" height="{h}" fill="{BG}" opacity=".67"/>'
    b += text("IDEA → INTERFACE → SYSTEM", 24, 37, 11 if mobile else 13, RED, "mono")
    b += text("Across the stack.", 24, 92, 37 if mobile else 49, PAPER, "serif")
    copy,_=lines("From the first interaction to the services, data, and intelligence behind it.",24,130,w-48,16)
    return page("Across the stack",w,h,b+copy,"Illustrative systems architecture.")


def gateway(mobile=False):
    w=360 if mobile else 720
    b=glyph("code",25,27,33)+text("OPEN THE FIELD MANUAL",75,39,13 if mobile else 18,PAPER,"mono")
    b+=text("Process. Principles. Off the clock.",75,62,12,MUTED)
    b+=text("+",w-25,46,25,RED,"mono",text_anchor="end")
    return page("Open the field manual",w,89,b,"Expand the native disclosure to explore working principles and the human side.")


def dossier_control(mobile=False):
    w=360 if mobile else 720
    b=glyph("file",18,16,20)+text("EXPLORE THE PROJECT",51,29,12,PAPER,"mono")
    if not mobile:
        b+=text("IDEA / PROOF / TECHNOLOGY / LINKS",295,29,10,MUTED,"mono")
    b+=text("+",w-22,30,20,RED,"mono",text_anchor="end")
    return page("Explore the project",w,50,b,"Expand project details and source links.","control")


def protocol(kind, profile, mobile=False):
    w=360 if mobile else 720
    records={
        "engineer":("HOW I BUILD", "Clarity before complexity.", ["Understand the constraint.", "Build the smallest complete path.", "Test the behavior, then refine the experience."]),
        "product":("WHAT I CARE ABOUT", "Make the difficult feel simple.", ["Give every interaction a clear purpose.", "Make loading, errors, and recovery part of the design.", "Let evidence set the pace for the next iteration."]),
        "human":("OFF THE CLOCK", "Grind. Build. Repeat.", ["Competitive games. Patient practice. A long view.", "The same curiosity carries from the server to the next build.", "Find me on Steam."]),
        "achievements":("BEYOND THE CODE", "Experience compounds.", profile["achievements"]),
    }
    label,title,items=records[kind]
    b=text(label,24,32,11,RED,"mono")
    head,end=lines(title,24,78,w-48,32,PAPER,36,"serif")
    b+=head
    y=end+19
    for i,item in enumerate(items):
        b+=text(f'{i+1:02d}',24,y,12,RED,"mono")
        copy,end=lines(item,61,y,w-85,16)
        b+=copy+rule(61,end+3,w-85)
        y=end+35
    return page(title,w,y-5,b)


def finale(profile,mobile=False):
    w,h=(360,300) if mobile else (720,278)
    art=raster(profile["visual_contract"]["delivery"]["supporting_art"]["channel"])
    b=f'<image href="{art}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice"/><rect width="{w}" height="{h}" fill="{BG}" opacity=".6"/>'
    b+=text("OPEN CHANNEL / NEXT OPERATION",24,35,10.5 if mobile else 12,RED,"mono")
    b+=text("Good ideas deserve",24,94,33 if mobile else 48,PAPER,"serif")
    b+=text("to become real.",24,135 if mobile else 147,33 if mobile else 48,PAPER,"serif")
    b+=text(profile["availability"]["status"].upper()+" / REMOTE",24,170 if mobile else 178,9.5 if mobile else 10,RED,"mono")
    cx,cy=(310,207) if mobile else (630,119)
    radius=24 if mobile else 42
    b+=f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{BG}" stroke="{RED}" stroke-width="1.5"/><circle cx="{cx}" cy="{cy}" r="{radius-10}" fill="none" stroke="{LINE}" stroke-dasharray="2 5"/>'
    b+=glyph("arrow",cx-12,cy-12,24)
    b+=rule(24,h-58,w-48)+text(profile["contact"]["email"],24,h-28,13 if mobile else 16,PAPER,"mono")
    return page("Start a conversation with Ayush Roy",w,h,b,profile["availability"]["status"])


def build_surfaces(profile):
    manifest={"signal-strip.svg":signal(), "signal-strip-mobile.svg":signal(True), "dossier-toggle.svg":dossier_control(),"dossier-toggle-mobile.svg":dossier_control(True),
              "systems-atlas.svg":system_atlas(profile), "systems-atlas-mobile.svg":system_atlas(profile, True)}
    for target,label in (("projects","PROJECTS"),("experience","BACKGROUND"),("activity","ACTIVITY"),("contact","CONTACT")):
        manifest[f'jump-{target}.svg']=button(label,"Jump to section","arrow")
    for key,(label,sub,kind) in NAV.items():
        manifest[f'nav-{key}.svg']=button(label,sub,kind)
    for i,project_id in enumerate(ORDER):
        manifest[f'project-index-{project_id}.svg']=button(SHORT[project_id],f'0{i+1} / Explore project',"realtime" if project_id=="helios" else "arrow")
    for item in profile["proof"]:
        manifest[f'proof-{item["id"]}.svg']=proof_card(item)
    for mobile in (False,True):
        suffix="-mobile" if mobile else ""
        for target,index,title,sub in SECTIONS:
            manifest[f'section-{target}{suffix}.svg']=section(index,title,sub,mobile)
        for name,render in (("identity-console",identity),("field-notes",field),("skills-matrix",skills),("arsenal",arsenal),("finale",finale)):
            manifest[f'{name}{suffix}.svg']=render(profile,mobile)
        manifest[f'operator-gateway{suffix}.svg']=gateway(mobile)
        for kind in ("engineer","product","human","achievements"):
            name="achievement-rack" if kind=="achievements" else f'protocol-{kind}'
            manifest[f'{name}{suffix}.svg']=protocol(kind,profile,mobile)
        for project in profile["projects"]:
            manifest[f'project-summary-{project["id"]}{suffix}.svg']=summary(project,mobile)
            manifest[f'project-dossier-{project["id"]}{suffix}.svg']=dossier(project,mobile)
    return manifest


def record(overview, language_rows, updated_at, mobile=False):
    w=360 if mobile else 720
    b=text("PUBLIC GITHUB RECORD",24,33,12,RED,"mono")
    cw=(w-48)/3
    for i,(key,label) in enumerate((("public_repos","REPOSITORIES"),("stars","STARS"),("followers","FOLLOWERS"))):
        x=24+cw*i
        value="—" if overview.get("_sample") else f'{overview[key]:,}'
        b+=text(value,x,94,44 if mobile else 58,PAPER,"serif")
        b+=text(label,x,119,9 if mobile else 12,MUTED,"mono")
    b+=rule(24,143,w-48)+text("LANGUAGES / PUBLIC CODE",24,177,12,RED,"mono")
    y=213
    if not language_rows:
        b+=text("Language data unavailable",24,y,16,MUTED)
        y+=38
    for name,_,pct in language_rows:
        b+=text(name,24,y,15,PAPER)+text(f'{pct:.1f}%',w-24,y,13,MUTED,"mono",text_anchor="end")
        b+=f'<rect x="24" y="{y+10}" width="{w-48}" height="5" rx="2.5" fill="{LINE}"/><rect x="24" y="{y+10}" width="{(w-48)*pct/100:.2f}" height="5" rx="2.5" fill="{RED}"/>'
        y+=48
    note,end=lines("Share of code bytes across public, non-fork repositories.",24,y,w-48,12)
    b+=note+rule(24,end+4,w-48)
    b+=text("SAMPLE / NO LIVE DATA" if overview.get("_sample") else "UPDATED / "+updated_at,24,end+29,10.5,MUTED,"mono")
    return page("Public GitHub record",w,end+52,b,"Timestamped GitHub API snapshot. Language proportions measure code bytes, not skill proficiency.")


def calendar(days, metrics, mobile=False, sample=False):
    if not days:
        raise ValueError("contribution calendar requires at least one day")
    days=sorted(days,key=lambda item:item["date"])
    w=360 if mobile else 720
    b=text("365 DAYS / CONTRIBUTIONS",24,33,12,RED,"mono")
    b+=text(f'{metrics["total"]:,}',24,91,60,PAPER,"serif")
    b+=text("CONTRIBUTIONS",24,116,11,MUTED,"mono")
    start,end=days[0]["date"],days[-1]["date"]
    b+=text(start.strftime('%d %b %Y')+" – "+end.strftime('%d %b %Y'),24,144,11,MUTED,"mono")
    # All 365 daily counts remain present on phones, split into two strips.
    first_sunday=start.toordinal()-(start.weekday()+1)%7
    weeks=(end.toordinal()-first_sunday)//7+1
    cols=(weeks+1)//2 if mobile else weeks
    pitch=(w-48)/cols
    cell=max(2,pitch-3)
    grid_y=176
    colors=("#14090c","#471221","#8f0014","#d30b24",RED)
    for day in days:
        week,dow=divmod(day["date"].toordinal()-first_sunday,7)
        row, col=divmod(week,cols)
        x=24+col*pitch
        y=grid_y+row*(7*pitch+32)+dow*pitch
        b+=f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell:.2f}" height="{cell:.2f}" rx="2" fill="{colors[max(0,min(4,int(day["level"]))) ]}" data-date="{day["date"].isoformat()}" data-count="{day["count"]}"><title>{day["date"].isoformat()}: {day["count"]} contributions</title></rect>'
    y=grid_y+(2 if mobile else 1)*(7*pitch+32)
    b+=text("LESS",24,y,10,MUTED,"mono")
    for i,color in enumerate(colors):
        b+=f'<rect x="{68+i*15}" y="{y-10}" width="10" height="10" rx="2" fill="{color}"/>'
    b+=text("MORE",150,y,10,MUTED,"mono")
    y+=31
    b+=rule(24,y,w-48)
    cw=(w-48)/3
    for i,(key,label) in enumerate((("active","ACTIVE DAYS"),("longest","BEST STREAK"),("peak","PEAK DAY"))):
        x=24+i*cw
        b+=text(str(metrics[key]),x,y+43,35,PAPER,"serif")+text(label,x,y+65,9 if mobile else 12,MUTED,"mono")
    b+=text("SAMPLE DATA" if sample else "SOURCE / GITHUB CONTRIBUTION CALENDAR",24,y+97,9 if mobile else 11,MUTED,"mono")
    return page("365-day GitHub contributions",w,y+119,b,f'{metrics["total"]} contributions across {metrics["active"]} active days. Period {start} to {end}.')
