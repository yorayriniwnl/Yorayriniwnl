#!/usr/bin/env python3
"""Generate the public README visual system from the verified profile data.

Identity, palette, project copy, and artwork paths come from data/profile.json.
Never hand-edit files under generated/. Positions are seeded so repeated runs
remain deterministic, and stale generated SVGs are removed automatically.
"""
import base64
import hashlib
import math
import os
import random
import re
import sys
import textwrap
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from profile_data import load_design_tokens, load_profile


ROOT = SCRIPT_DIR.parent
HERE = str(SCRIPT_DIR)
OUT_DIR = ROOT / "generated"
ASSET_DIR = ROOT / "assets"
PROFILE = load_profile()
TOKENS = load_design_tokens()
IDENTITY = PROFILE["identity"]
VISUAL_CONTRACT = PROFILE["visual_contract"]
WORLD_TOKENS = TOKENS["worlds"]
SUPPORTING_ART = VISUAL_CONTRACT["delivery"]["supporting_art"]
FLAGSHIP_ART = VISUAL_CONTRACT["delivery"]["flagship_art"]
PALETTE = {
    "void": TOKENS["color"]["void"],
    "panel": TOKENS["color"]["panel"],
    "crimson": TOKENS["color"]["crimson"],
    "deep_crimson": TOKENS["color"]["deepCrimson"],
    "signal": TOKENS["color"]["signal"],
    "paper": TOKENS["color"]["paper"],
    "muted": TOKENS["color"]["muted"],
}

CONFIG = {
    "name": IDENTITY["name"],
    "role": f'{IDENTITY["role"].upper()}  ·  {IDENTITY["specialty"].upper()}',
    "width": 1500,
    "height": 300,
    # Steam-profile palette: a pure-black canvas, translucent black panels,
    # and a saturated scarlet header gradient used by the live profile's
    # showcase bars.
    "bg_stops": [
        (0, PALETTE["void"]), (18, "#050101"), (42, "#1f0404"),
        (64, PALETTE["deep_crimson"]), (82, "#180303"), (100, PALETTE["void"]),
    ],
    "primary": PALETTE["crimson"],
    "secondary": TOKENS["color"]["secondaryCrimson"],
    "sparkle": PALETTE["signal"],
    "muted": PALETTE["muted"],
    "shimmer": TOKENS["color"]["shimmer"],
    "name_color": PALETTE["paper"],
    "seed": 42,
    "star_counts": {"far": 34, "mid": 24, "near": 13},
    "sparkle_count": 6,
    "tagline": {
        "width": 760,
        "height": 34,
        "type_ms_per_char": 42,
        "delete_ms_per_char": 20,
        "hold_ms": 1500,
        "gap_ms": 200,
        # (text, measured px width in DM Mono 500 @ 14px/0.5 letter-spacing —
        # measured in an actual browser against the real embedded font by
        # scripts/measure_tagline.py; re-run it if any line's text changes.
        # Re-measured in Pass 4 against Chrome 131.0.6778.204 — see
        # CHANGELOG for why the old numbers were short.)
        "lines": [
            ("Building the software layer for the physical world.", 453.9),
            ("Geospatial \u00b7 Realtime \u00b7 Computer Vision \u00b7 Systems Engineering", 542.9),
            ("TypeScript + React for product, Python + ML for the intelligence layer.", 534.0),
            ("The domain changes; the standard doesn't.", 364.9),
        ],
    },
    "wave_header_stops": [(0, PALETTE["void"]), (60, PALETTE["deep_crimson"]), (100, TOKENS["gradient"]["header"][2])],
    "wave_footer_stops": [(0, TOKENS["gradient"]["footer"][0]), (60, PALETTE["deep_crimson"]), (100, PALETTE["void"])],
    # (output filename, glyph, config color key) — one small seal per work-
    # section project, in the same primary/secondary alternation the
    # badges under each project already use.
    "seals": [
        ("seal-portfolio", "\u2726", "primary"),
        ("seal-helios", "\u25c8", "secondary"),
        ("seal-zenith", "\u2600", "primary"),
        ("seal-ai-vs-real", "\u25cd", "secondary"),
        ("seal-talks", "\u2b21", "primary"),
    ],
}

# The name/role/rule block's footprint, in canvas coordinates. Background
# motifs (nebula, kintsugi, constellation) are kept clear of this — verified
# contrast for the text shouldn't have to be re-earned every time a new
# layer is added behind it. Stars are exempt: they render *behind* the
# opaque text glyphs in paint order, so overlap there is invisible, not risky.
TEXT_ZONE = {"x0": 330, "x1": 1170, "y0": 92, "y1": 228}

# The hero and flagship project covers have their own art direction and are
# intentionally left alone. Every other public visual is a supporting
# interface surface, so it receives the same cinematic atlas treatment at
# manifest-build time. Keeping this list explicit makes the privacy/artwork
# boundary auditable and prevents a future generator change from accidentally
# touching the approved profile image.
ATLAS_TREATMENT_REVISION = "atlas-v5"
ATLAS_TREATMENT_EXCLUDED = frozenset({
    "hero.svg",
    "project-portfolio-v2.svg",
    "project-portfolio-mobile-v2.svg",
    "project-helios.svg",
    "project-zenith.svg",
    "project-vision.svg",
    "project-token-usage.svg",
    "project-talks.svg",
})


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _svg_viewbox(svg):
    match = re.search(r'<svg\b[^>]*\bviewBox="([^"]+)"', svg)
    if not match:
        raise ValueError("SVG is missing a numeric viewBox")
    values = [float(value) for value in re.split(r"[\s,]+", match.group(1).strip())]
    if len(values) != 4 or values[2] <= 0 or values[3] <= 0:
        raise ValueError(f"invalid SVG viewBox: {match.group(1)}")
    return values


def _atlas_overlay(filename, svg):
    """Add a restrained, deterministic visual chassis to supporting SVGs.

    The base assets own their copy and primary illustration. This overlay is
    deliberately a transparent, pointer-free layer: it adds depth rails,
    edge brackets, a small orbital instrument, an instrument sweep, signal
    ticks, and a second-order radar pulse while leaving authored content and
    screen-reader title/description intact.
    """
    _, _, width, height = _svg_viewbox(svg)
    digest = hashlib.sha256(filename.encode("utf-8")).hexdigest()
    prefix = f"atlas{digest[:10]}"
    seed = int(digest[10:18], 16)

    short_edge = min(width, height)
    inset = max(4.0, min(18.0, short_edge * 0.075))
    bracket = max(7.0, min(30.0, short_edge * 0.24))
    stroke = max(0.7, min(1.5, short_edge / 220.0))
    radius = max(7.0, min(54.0, short_edge * 0.22))
    cx = width - inset - radius - (seed % max(6, int(short_edge * 0.12)))
    cy = inset + radius + ((seed >> 5) % max(4, int(short_edge * 0.12)))
    cx = max(inset + radius, min(width - inset - radius, cx))
    cy = max(inset + radius, min(height - inset - radius, cy))
    orbit_ry = max(3.0, radius * 0.36)
    grid = max(12, int(round(short_edge / 7)))
    scan_width = max(18.0, min(88.0, width * 0.08))
    scan_duration = 8.0 + (seed % 40) / 10.0
    scan_begin = -((seed >> 9) % 80) / 10.0
    signal_y = max(inset + 2, height - inset * 0.72)
    signal_x = inset + bracket * 1.7
    signal_w = max(26.0, width - signal_x - inset - bracket * 0.4)
    trace_points = []
    trace_count = 5 if width < 500 else 8
    for index in range(trace_count):
        x = signal_x + signal_w * index / (trace_count - 1)
        wobble = ((seed >> (index * 3)) & 7) - 3
        y = signal_y - wobble * max(0.7, short_edge / 150.0)
        trace_points.append(f"{x:.1f},{y:.1f}")
    trace = " ".join(trace_points)
    orbital_dots = []
    for index in range(3):
        angle = (seed % 360) * math.pi / 180 + index * math.tau / 3
        dot_x = cx + math.cos(angle) * radius
        dot_y = cy + math.sin(angle) * orbit_ry
        dot_r = max(1.3, min(3.2, short_edge / 48.0))
        orbital_dots.append(
            f'<circle cx="{dot_x:.1f}" cy="{dot_y:.1f}" r="{dot_r:.1f}" '
            f'fill="#ff8a7f" opacity="{0.36 + index * 0.12:.2f}"/>'
        )

    safe_width = max(1.0, width - inset * 2)
    safe_height = max(1.0, height - inset * 2)
    return f'''<defs>
<radialGradient id="{prefix}Glow" cx="50%" cy="50%" r="50%">
<stop offset="0" stop-color="#e84b4b" stop-opacity=".24"/>
<stop offset=".55" stop-color="#671515" stop-opacity=".08"/>
<stop offset="1" stop-color="#000" stop-opacity="0"/>
</radialGradient>
<linearGradient id="{prefix}Sweep" gradientUnits="userSpaceOnUse" x1="-{scan_width:.1f}" x2="0">
<stop offset="0" stop-color="#ff8a7f" stop-opacity="0"/>
<stop offset=".5" stop-color="#ff8a7f" stop-opacity=".24"/>
<stop offset="1" stop-color="#e84b4b" stop-opacity="0"/>
</linearGradient>
<linearGradient id="{prefix}Rail" gradientUnits="userSpaceOnUse" x1="0" x2="{width:.1f}">
<stop offset="0" stop-color="#ff8a7f" stop-opacity="0"/>
<stop offset=".2" stop-color="#ff8a7f" stop-opacity=".54"/>
<stop offset=".5" stop-color="#e84b4b" stop-opacity=".18"/>
<stop offset=".84" stop-color="#ff8a7f" stop-opacity=".54"/>
<stop offset="1" stop-color="#ff8a7f" stop-opacity="0"/>
</linearGradient>
<pattern id="{prefix}Grid" width="{grid}" height="{grid}" patternUnits="userSpaceOnUse">
<path d="M{grid} 0H0V{grid}" fill="none" stroke="#e84b4b" stroke-width=".45" opacity=".07"/>
</pattern>
<style>
.{prefix}-scan {{ animation: {prefix}-scan {scan_duration:.1f}s linear infinite; animation-delay: {scan_begin:.1f}s; }}
.{prefix}-orbit {{ transform-box: fill-box; transform-origin: center; animation: {prefix}-orbit {22 + seed % 18}s linear infinite; }}
.{prefix}-pulse {{ transform-box: fill-box; transform-origin: center; animation: {prefix}-pulse 4.8s ease-out infinite; animation-delay: -{(seed % 48) / 10:.1f}s; }}
.{prefix}-spark {{ animation: {prefix}-spark 2.6s ease-in-out infinite; animation-delay: -{(seed % 26) / 10:.1f}s; }}
@keyframes {prefix}-scan {{ from {{ transform: translateX(0); }} to {{ transform: translateX({width + scan_width * 2:.1f}px); }} }}
@keyframes {prefix}-orbit {{ to {{ transform: rotate(360deg); }} }}
@keyframes {prefix}-pulse {{ 0% {{ opacity: 0; transform: scale(.72); }} 28% {{ opacity: .6; }} 100% {{ opacity: 0; transform: scale(1.34); }} }}
@keyframes {prefix}-spark {{ 0%, 100% {{ opacity: .18; }} 50% {{ opacity: .92; }} }}
@media (prefers-reduced-motion: reduce) {{ .{prefix}-scan, .{prefix}-orbit, .{prefix}-pulse, .{prefix}-spark {{ animation: none !important; }} }}
</style>
</defs>
<g id="atlas-treatment" data-visual-treatment="{ATLAS_TREATMENT_REVISION}" data-atlas-tier="cinematic" aria-hidden="true" pointer-events="none">
<rect x="{inset:.1f}" y="{inset:.1f}" width="{safe_width:.1f}" height="{safe_height:.1f}" rx="{max(2.0, min(10.0, inset)):.1f}"
 fill="url(#{prefix}Grid)" opacity=".52"/>
<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{radius * 1.8:.1f}" ry="{radius * .9:.1f}"
 fill="url(#{prefix}Glow)" opacity=".42"/>
<ellipse class="{prefix}-pulse" cx="{cx:.1f}" cy="{cy:.1f}" rx="{radius * .8:.1f}" ry="{orbit_ry * 1.9:.1f}"
 fill="none" stroke="#ff8a7f" stroke-width="{max(.7, stroke * .8):.2f}" stroke-dasharray="2 9" opacity=".58"/>
<rect class="{prefix}-scan" x="-{scan_width:.1f}" y="{inset:.1f}" width="{scan_width:.1f}" height="{safe_height:.1f}"
 fill="url(#{prefix}Sweep)" opacity=".45"/>
<path d="M{inset:.1f} {height - inset * 1.55:.1f}H{width - inset:.1f}" fill="none" stroke="url(#{prefix}Rail)" stroke-width="{max(.7, stroke * .7):.2f}" opacity=".72"/>
<path d="M{width - inset * 1.55:.1f} {inset:.1f}V{height - inset:.1f}" fill="none" stroke="url(#{prefix}Rail)" stroke-width="{max(.7, stroke * .7):.2f}" opacity=".45"/>
{''.join(f'<path d="M{width - inset * 1.55 - 3:.1f} {inset + index * max(8, (height - inset * 2) / 5):.1f}h6" stroke="#ff8a7f" stroke-width="{max(.55, stroke * .55):.2f}" opacity=".35"/>' for index in range(6))}
<path d="M{inset:.1f} {inset + bracket:.1f}V{inset:.1f}H{inset + bracket:.1f}
 M{width - inset - bracket:.1f} {inset:.1f}H{width - inset:.1f}V{inset + bracket:.1f}
 M{inset:.1f} {height - inset - bracket:.1f}V{height - inset:.1f}H{inset + bracket:.1f}
 M{width - inset - bracket:.1f} {height - inset:.1f}H{width - inset:.1f}V{height - inset - bracket:.1f}"
 fill="none" stroke="#ff8a7f" stroke-width="{stroke:.2f}" opacity=".38"/>
<ellipse class="{prefix}-orbit" cx="{cx:.1f}" cy="{cy:.1f}" rx="{radius:.1f}" ry="{orbit_ry:.1f}"
 fill="none" stroke="#ff8a7f" stroke-width="{stroke:.2f}" stroke-dasharray="3 7" opacity=".54"/>
<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{radius * .66:.1f}" ry="{orbit_ry * .66:.1f}"
 fill="none" stroke="#e84b4b" stroke-width="{max(.5, stroke * .65):.2f}" stroke-dasharray="1 8" opacity=".36"/>
{''.join(orbital_dots)}
<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{max(1.8, radius * .08):.1f}" fill="#ff8a7f" opacity=".72"/>
<polyline points="{trace}" fill="none" stroke="#e84b4b" stroke-width="{max(.7, stroke * .8):.2f}" opacity=".36" stroke-linecap="round" stroke-linejoin="round"/>
<circle class="{prefix}-spark" cx="{signal_x + signal_w * .58:.1f}" cy="{signal_y:.1f}" r="{max(1.2, short_edge / 80):.1f}" fill="#ff8a7f" opacity=".64"/>
</g>'''


def apply_red_theme(svg):
    """Normalize legacy hand-authored accents to the canonical red system.

    Most supporting visuals predate the token file and contain inline colors.
    Keeping this last-mile normalization makes the design tokens authoritative
    without rewriting hundreds of intentionally data-rich SVG templates.
    Embedded raster data is base64, so these substitutions cannot alter the
    approved hero or project artwork bytes.
    """
    replacements = {
        "#e84b4b": PALETTE["crimson"],
        "#b92b2b": TOKENS["color"]["secondaryCrimson"],
        "#ff8a7f": PALETTE["signal"],
        "#f5eaea": PALETTE["paper"],
        "#671515": PALETTE["deep_crimson"],
        "#8c1616": TOKENS["gradient"]["showcase"][1],
        "#2a0505": TOKENS["gradient"]["showcase"][2],
        "#321018": WORLD_TOKENS["portfolio"]["line"],
        "#57222c": WORLD_TOKENS["portfolio"]["line"],
        "#190c11": WORLD_TOKENS["portfolio"]["canvas"],
        "#b73d48": TOKENS["color"]["secondaryCrimson"],
        "#a55e6b": TOKENS["color"]["secondaryCrimson"],
        "#ad5865": TOKENS["color"]["secondaryCrimson"],
        "#9c7680": PALETTE["muted"],
        "#ffe5de": PALETTE["paper"],
        "#fff0e8": PALETTE["paper"],
        "#fff2f0": PALETTE["paper"],
        "#c4c4c4": PALETTE["muted"],
    }
    for old, new in replacements.items():
        svg = svg.replace(old, new)
    return svg


def apply_atlas_treatment(manifest):
    treated = {}
    for filename, svg in manifest.items():
        if filename in ATLAS_TREATMENT_EXCLUDED:
            treated[filename] = apply_red_theme(svg)
            continue
        close = svg.rfind("</svg>")
        if close < 0:
            raise ValueError(f"cannot treat malformed SVG: {filename}")
        treated[filename] = apply_red_theme(
            f"{svg[:close]}{_atlas_overlay(filename, svg)}{svg[close:]}"
        )
    return treated


def wrap_lines(text, width):
    """Wrap profile copy predictably for deterministic SVG text layouts."""
    return textwrap.wrap(
        text,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    )


def b64_font(filename):
    with open(os.path.join(HERE, "fonts", filename), "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def asset_data_uri(filename, mime_type=None):
    """Embed a project-owned raster inside an SVG so GitHub never has to
    resolve a nested remote image request. The generated SVGs stay fully
    self-contained and continue to animate when rendered through raw GitHub."""
    asset_path = ASSET_DIR / Path(filename).name
    if mime_type is None:
        mime_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }.get(asset_path.suffix.lower())
    if mime_type is None:
        raise ValueError(f"unsupported embedded asset type: {asset_path.suffix}")
    with asset_path.open("rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def in_zone(x, y, pad=0):
    z = TEXT_ZONE
    return (z["x0"] - pad) <= x <= (z["x1"] + pad) and (z["y0"] - pad) <= y <= (z["y1"] + pad)


# ---------------------------------------------------------------- starfield

def gen_star_layer(rng, count, r_range, op_range, dur_range, color, w, h):
    els = []
    made, tries = 0, 0
    while made < count and tries < count * 40:
        tries += 1
        x = rng.uniform(12, w - 12)
        y = rng.uniform(8, h - 8)
        if in_zone(x, y):
            continue
        r = rng.uniform(*r_range)
        op = rng.uniform(*op_range)
        dur = rng.uniform(*dur_range)
        delay = rng.uniform(0, dur)
        els.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{color}">'
            f'<animate attributeName="opacity" values="{op*0.16:.2f};{op:.2f};{op*0.16:.2f}" '
            f'dur="{dur:.2f}s" begin="-{delay:.2f}s" repeatCount="indefinite"/></circle>'
        )
        made += 1
    return "".join(els)


def sparkle_local_path(size):
    k = size * 0.18
    return (
        f'M0 {-size:.1f} Q{k:.1f} {-k:.1f} {size:.1f} 0 '
        f'Q{k:.1f} {k:.1f} 0 {size:.1f} '
        f'Q{-k:.1f} {k:.1f} {-size:.1f} 0 '
        f'Q{-k:.1f} {-k:.1f} 0 {-size:.1f} Z'
    )


def gen_sparkles(rng, count, color, w, h):
    els = []
    made, tries = 0, 0
    while made < count and tries < count * 50:
        tries += 1
        x = rng.uniform(30, w - 30)
        y = rng.uniform(20, h - 20)
        if in_zone(x, y, pad=26):
            continue
        size = rng.uniform(3.4, 6.2)
        dur = rng.uniform(3.2, 5.6)
        delay = rng.uniform(0, dur)
        d = sparkle_local_path(size)
        els.append(
            f'<g transform="translate({x:.1f},{y:.1f})">'
            f'<path d="{d}" fill="{color}" opacity="0">'
            f'<animate attributeName="opacity" keyTimes="0;0.14;0.5;0.62;1" '
            f'values="0;0.85;0.15;0.85;0" dur="{dur:.2f}s" begin="-{delay:.2f}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="scale" '
            f'keyTimes="0;0.14;0.5;0.62;1" values="0.4;1.15;0.85;1.05;0.4" '
            f'dur="{dur:.2f}s" begin="-{delay:.2f}s" repeatCount="indefinite"/>'
            f'</path></g>'
        )
        made += 1
    return "".join(els)


# -------------------------------------------------------------------- comet

def gen_comet(x1, y1, x2, y2, dur, begin, color):
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    tail = 68
    tx, ty = -ux * tail, -uy * tail
    gid = f"cometTrail{abs(hash((x1, y1, x2, y2))) % 10000}"
    defs = (
        f'<linearGradient id="{gid}" x1="{tx:.1f}" y1="{ty:.1f}" x2="0" y2="0" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0.95"/></linearGradient>'
    )
    body = (
        f'<g opacity="0">'
        f'<animate attributeName="opacity" keyTimes="0;0.02;0.1;0.16;1" values="0;1;1;0;0" '
        f'dur="{dur:.2f}s" begin="{begin:.2f}s" repeatCount="indefinite"/>'
        f'<animateMotion keyTimes="0;0.13;1" keyPoints="0;1;1" calcMode="linear" '
        f'path="M{x1:.0f},{y1:.0f} L{x2:.0f},{y2:.0f}" '
        f'dur="{dur:.2f}s" begin="{begin:.2f}s" repeatCount="indefinite"/>'
        f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="0" y2="0" stroke="url(#{gid})" '
        f'stroke-width="1.5" stroke-linecap="round"/>'
        f'<circle cx="0" cy="0" r="2" fill="{color}"/>'
        f'</g>'
    )
    return defs, body


# --------------------------------------------------------------------- grain

def grain_filter(fid, seed):
    """A fine, low-frequency-free noise texture — the "grain textures" this
    project's own established visual language calls for but never actually
    had. feTurbulence + a color matrix that collapses the noise to a
    neutral, alpha-only signal (never colored static); applied as a single
    full-canvas rect at very low opacity by the caller, over everything
    else including text, the way real film grain sits over a whole frame
    rather than just the background."""
    return (
        f'<filter id="{fid}" x="-5%" y="-5%" width="110%" height="110%">'
        f'<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" '
        f'seed="{seed}" stitchTiles="stitch" result="n"/>'
        f'<feColorMatrix in="n" type="matrix" '
        f'values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0.5 0.5 0.5 0 0"/>'
        f'</filter>'
    )


# -------------------------------------------------------------------- embers

def gen_embers(rng, count, colors, w, h, y_lo_frac=0.5):
    """Small glowing points that drift upward and fade — embers off a fire
    rather than a starfield. Only makes sense against the red palette;
    would have read as noise against the old purple void. Lives in the
    same paint-order group as the star layers (behind the opaque text),
    so a spawn point under TEXT_ZONE is fine, not checked against it."""
    els = []
    made, tries = 0, 0
    while made < count and tries < count * 40:
        tries += 1
        x = rng.uniform(16, w - 16)
        y0 = rng.uniform(h * y_lo_frac, h + 14)
        rise = rng.uniform(60, 150) if h > 60 else rng.uniform(18, 34)
        sway = rng.uniform(-16, 16)
        r = rng.uniform(0.9, 2.1)
        color = colors[made % len(colors)]
        dur = rng.uniform(4.5, 8.0)
        delay = rng.uniform(0, dur)
        els.append(
            f'<circle r="{r:.2f}" fill="{color}">'
            f'<animate attributeName="opacity" keyTimes="0;0.1;0.7;1" values="0;0.9;0.35;0" '
            f'dur="{dur:.2f}s" begin="-{delay:.2f}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="{x:.1f},{y0:.1f}; {x+sway:.1f},{y0-rise:.1f}" '
            f'dur="{dur:.2f}s" begin="-{delay:.2f}s" repeatCount="indefinite"/>'
            f'</circle>'
        )
        made += 1
    return "".join(els)


# ---------------------------------------------------------------- decoration

def gen_nebula(cfg):
    blobs = [
        (230, 55, 250, 165, cfg["secondary"], 0.15, 9.0),
        (1280, 245, 290, 180, cfg["primary"], 0.12, 12.5),
        (760, 30, 330, 130, "#6b1420", 0.20, 16.0),  # deep wine, red-family twin of the old #5b1f7a violet
    ]
    defs, uses = [], []
    for i, (cx, cy, rx, ry, color, op, dur) in enumerate(blobs):
        gid = f"neb{i}"
        defs.append(
            f'<radialGradient id="{gid}" cx="50%" cy="50%" r="50%">'
            f'<stop offset="0%" stop-color="{color}" stop-opacity="{op}"/>'
            f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/></radialGradient>'
        )
        # Slow breathing — opacity and radius both drift, out of phase across
        # the three blobs (9/12.5/16s) so they never pulse in visible unison.
        uses.append(
            f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#{gid})" '
            f'filter="url(#softBlur)" opacity="0.85">'
            f'<animate attributeName="opacity" values="0.7;1;0.7" dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="rx" values="{rx*0.94:.0f};{rx*1.06:.0f};{rx*0.94:.0f}" dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="ry" values="{ry*0.94:.0f};{ry*1.06:.0f};{ry*0.94:.0f}" dur="{dur}s" repeatCount="indefinite"/>'
            f'</ellipse>'
        )
    return "".join(defs), "".join(uses)


def gen_kintsugi(color):
    def crack(points, op, width=1.3):
        d = f"M{points[0][0]},{points[0][1]} " + " ".join(
            f"L{x},{y}" for x, y in points[1:]
        )
        nodes = "".join(
            f'<circle cx="{x}" cy="{y}" r="2" fill="{color}" opacity="{op+0.16:.2f}"/>'
            for x, y in points[1:-1]
        )
        return f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="none" opacity="{op:.2f}" stroke-linecap="round" stroke-linejoin="round"/>{nodes}'

    crack_a = crack([(16, 300), (68, 253), (56, 208), (104, 172)], 0.20)
    crack_b = crack([(1484, 0), (1428, 34), (1452, 68), (1396, 92)], 0.18)
    return crack_a + crack_b


def gen_constellation(color):
    left = [(90, 68), (172, 128), (108, 208)]
    right = [(1252, 54), (1362, 92), (1400, 188), (1298, 234)]
    lines = [
        (left[0], left[1]), (left[1], left[2]), (left[2], left[0]),
        (right[0], right[1]), (right[1], right[2]),
        (right[2], right[3]), (right[3], right[0]), (right[1], right[3]),
    ]
    parts = []
    for (x1, y1), (x2, y2) in lines:
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="0.6"/>')
    for x, y in left + right:
        parts.append(f'<circle cx="{x}" cy="{y}" r="1.7" fill="{color}"/>')
    inner = "".join(parts)
    return (
        f'<g opacity="0.16">{inner}'
        f'<animate attributeName="opacity" values="0.08;0.22;0.08" dur="7s" repeatCount="indefinite"/>'
        f'</g>'
    )


def gen_corner_brackets(color, w, h):
    L, inset = 22, 14
    corners = [
        (inset, inset, 1, 1, 0.0), (w - inset, inset, -1, 1, -2.1),
        (inset, h - inset, 1, -1, -4.2), (w - inset, h - inset, -1, -1, -6.3),
    ]
    parts = []
    for x, y, ax, ay, phase in corners:
        parts.append(
            f'<path d="M{x},{y+ay*L} L{x},{y} L{x+ax*L},{y}" '
            f'stroke="{color}" stroke-width="1.1" fill="none" opacity="0.5" stroke-linecap="round">'
            f'<animate attributeName="opacity" values="0.32;0.6;0.32" dur="8.4s" '
            f'begin="{phase}s" repeatCount="indefinite"/>'
            f'</path>'
        )
    return "".join(parts)


def gen_divider_ornament(cx, y, color, half_width, dot_gap):
    """Rule line + flanking accents + center diamond, shared by the hero's
    name-underline, wave-final's closing rule, and the standalone divider
    files. Self-contained gradient defs (own id, not a shared "rule" the
    caller has to remember to define) — the previous version relied on
    the caller providing `id="rule"`, which hero.svg and the standalone
    dividers did but wave-final.svg never did, so its connecting hairline
    has been invisible since Pass 3. Fixed by no longer depending on it."""
    uid = f"{int(cx)}_{int(y)}_{half_width}"
    w0 = cx - half_width
    band = min(200, half_width * 0.8)
    sparkle_defs = []
    for i, (sx, phase) in enumerate([(cx - dot_gap, 0.0), (cx + dot_gap, 2.3)]):
        sparkle_defs.append(
            f'<path d="M{sx},{y-3.4} L{sx+1.0},{y-1.0} L{sx+3.4},{y} L{sx+1.0},{y+1.0} '
            f'L{sx},{y+3.4} L{sx-1.0},{y+1.0} L{sx-3.4},{y} L{sx-1.0},{y-1.0} Z" '
            f'fill="{color}" opacity="0.4">'
            f'<animate attributeName="opacity" values="0.28;0.85;0.28" dur="4.6s" '
            f'begin="-{phase}s" repeatCount="indefinite"/>'
            f'</path>'
        )
    return (
        f'<g>'
        f'<defs>'
        f'<linearGradient id="rule{uid}" x1="0%" y1="0%" x2="100%" y2="0%">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0"/>'
        f'<stop offset="50%" stop-color="{color}" stop-opacity="0.65"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f'</linearGradient>'
        f'<linearGradient id="shine{uid}" gradientUnits="userSpaceOnUse" '
        f'x1="{w0-band:.0f}" y1="0" x2="{w0:.0f}" y2="0">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0"/>'
        f'<stop offset="50%" stop-color="#fff2f0" stop-opacity="0.9"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/>'
        f'<animate attributeName="x1" values="{w0-band:.0f};{cx+half_width:.0f}" dur="7s" repeatCount="indefinite"/>'
        f'<animate attributeName="x2" values="{w0:.0f};{cx+half_width+band:.0f}" dur="7s" repeatCount="indefinite"/>'
        f'</linearGradient>'
        f'</defs>'
        f'<rect x="{w0}" y="{y}" width="{half_width*2}" height="1" fill="url(#rule{uid})"/>'
        f'<rect x="{w0}" y="{y-0.75}" width="{half_width*2}" height="1.5" fill="url(#shine{uid})"/>'
        f'{"".join(sparkle_defs)}'
        f'<rect x="{cx-7}" y="{y-7}" width="14" height="14" fill="{color}" opacity="0.16" '
        f'transform="rotate(45 {cx} {y})">'
        f'<animate attributeName="opacity" values="0.08;0.26;0.08" dur="3.4s" repeatCount="indefinite"/>'
        f'</rect>'
        f'<rect x="{cx-4}" y="{y-4}" width="8" height="8" fill="{color}" '
        f'transform="rotate(45 {cx} {y})" opacity="0.75">'
        f'<animate attributeName="opacity" values="0.5;0.95;0.5" dur="3.4s" repeatCount="indefinite"/>'
        f'</rect></g>'
    )


# --------------------------------------------------------------------- hero

def build_hero_svg(cfg):
    W, H = cfg["width"], cfg["height"]
    cormorant = b64_font("cormorant-garamond-600.woff2")
    dmmono = b64_font("dm-mono-500.woff2")
    rng = random.Random(cfg["seed"])

    stops = "".join(f'<stop offset="{p}%" stop-color="{c}"/>' for p, c in cfg["bg_stops"])

    neb_defs, neb_uses = gen_nebula(cfg)

    far = gen_star_layer(rng, cfg["star_counts"]["far"], (0.4, 0.8), (0.30, 0.48), (3.0, 6.0), cfg["muted"], W, H)
    mid = gen_star_layer(rng, cfg["star_counts"]["mid"], (0.7, 1.3), (0.45, 0.72), (2.4, 4.4), cfg["sparkle"], W, H)
    near = gen_star_layer(rng, cfg["star_counts"]["near"], (1.1, 1.8), (0.72, 0.95), (1.8, 3.2), "#ffffff", W, H)
    sparkles = gen_sparkles(rng, cfg["sparkle_count"], cfg["primary"], W, H)
    embers = gen_embers(rng, 16, [cfg["primary"], cfg["secondary"], cfg["sparkle"]], W, H, y_lo_frac=0.55)

    comet_defs = []
    comet_bodies = []
    for (x1, y1, x2, y2, dur, begin, color) in [
        (40, 55, 580, 128, 11.0, 0.6, "#fff0e8"),
        (1462, 252, 928, 188, 14.0, 6.2, "#ffcfd6"),
        (200, 268, 720, 40, 16.5, 10.4, cfg["sparkle"]),
    ]:
        d, b = gen_comet(x1, y1, x2, y2, dur, begin, color)
        comet_defs.append(d)
        comet_bodies.append(b)

    kintsugi = gen_kintsugi(cfg["primary"])
    constellation = gen_constellation(cfg["primary"])
    brackets = gen_corner_brackets(cfg["primary"], W, H)
    ornament = gen_divider_ornament(W / 2, 176, cfg["primary"], 280, 42)

    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
<style>
@font-face {{ font-family: 'Cormorant Garamond'; font-weight: 600; src: url(data:font/woff2;base64,{cormorant}) format('woff2'); }}
@font-face {{ font-family: 'DM Mono'; font-weight: 500; src: url(data:font/woff2;base64,{dmmono}) format('woff2'); }}
.name {{ font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 96px; letter-spacing: 4px; }}
.role {{ font-family: 'DM Mono', monospace; font-weight: 500; font-size: 19px; fill: {cfg["muted"]}; letter-spacing: 3px; }}
</style>
<linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="0%">{stops}</linearGradient>
<radialGradient id="textWell" cx="50%" cy="50%" r="50%">
<stop offset="0%" stop-color="#000000" stop-opacity="0.42"/>
<stop offset="60%" stop-color="#000000" stop-opacity="0.20"/>
<stop offset="100%" stop-color="#000000" stop-opacity="0"/>
</radialGradient>
<radialGradient id="vignette" cx="50%" cy="50%" r="72%">
<stop offset="55%" stop-color="#000000" stop-opacity="0"/>
<stop offset="100%" stop-color="#000000" stop-opacity="0.4"/>
</radialGradient>
<linearGradient id="shimmerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="{cfg["shimmer"]}" stop-opacity="0"/>
<stop offset="0%" stop-color="{cfg["shimmer"]}" stop-opacity="0.9">
<animate attributeName="offset" keyTimes="0;0.001;0.32;1" values="0%;0%;100%;100%" dur="6s" begin="1s" repeatCount="indefinite"/>
</stop>
<stop offset="100%" stop-color="{cfg["shimmer"]}" stop-opacity="0"/>
</linearGradient>
<filter id="softBlur" x="-40%" y="-40%" width="180%" height="180%">
<feGaussianBlur stdDeviation="34"/>
</filter>
<filter id="nameGlow" x="-25%" y="-120%" width="150%" height="340%">
<feGaussianBlur stdDeviation="6"/>
</filter>
{grain_filter("heroGrain", cfg["seed"])}
{neb_defs}
{"".join(comet_defs)}
</defs>
<rect width="{W}" height="{H}" fill="url(#bg)"/>
{neb_uses}
<ellipse cx="{W/2}" cy="168" rx="490" ry="132" fill="url(#textWell)"/>
<rect width="{W}" height="{H}" fill="url(#vignette)"/>
{kintsugi}
{constellation}
{brackets}
{far}
{mid}
{near}
{sparkles}
{embers}
{"".join(comet_bodies)}
{ornament}
<text x="50%" y="150" text-anchor="middle" class="name" fill="{cfg["primary"]}" filter="url(#nameGlow)" opacity="0.68">{esc(cfg["name"])}</text>
<text x="50%" y="150" text-anchor="middle" class="name" fill="{cfg["name_color"]}">{esc(cfg["name"])}</text>
<text x="50%" y="150" text-anchor="middle" class="name" fill="url(#shimmerGrad)">{esc(cfg["name"])}</text>
<text x="50%" y="206" text-anchor="middle" class="role">{esc(cfg["role"])}</text>
<rect width="{W}" height="{H}" filter="url(#heroGrain)" opacity="0.05"/>
</svg>'''


# ------------------------------------------------------------- wave banners

def wave_layer_path(w, h, base_y, amplitude, humps, crest_up, phase_offset=0.0):
    """A smooth multi-hump wave built from cubic beziers, filled solid
    either down to the bottom edge (crest_up=True, for a header banner
    whose wave sits near the top) or up to the top edge (crest_up=False,
    for a footer banner whose wave sits near the bottom)."""
    seg = w / humps
    d = f"M{-seg*0.5:.1f},{base_y:.1f}"
    for i in range(-1, humps + 1):
        x0 = i * seg
        x2 = x0 + seg
        up = ((i + (1 if phase_offset else 0)) % 2 == 0)
        dy = -amplitude if up else amplitude
        y_ctrl = base_y + dy
        d += f" C{x0+seg*0.25:.1f},{y_ctrl:.1f} {x0+seg*0.75:.1f},{y_ctrl:.1f} {x2:.1f},{base_y:.1f}"
    if crest_up:
        d += f" L{w+seg},{h} L{-seg},{h} Z"
    else:
        d += f" L{w+seg},0 L{-seg},0 Z"
    return d


def wave_crest_only(w, base_y, amplitude, humps, crest_up, phase_offset=0.0):
    """Same curve as wave_layer_path's top edge, without the fill-closing
    path — used to stroke just the crest line, not the filled body."""
    seg = w / humps
    d = f"M{-seg*0.5:.1f},{base_y:.1f}"
    for i in range(-1, humps + 1):
        x0 = i * seg
        x2 = x0 + seg
        up = ((i + (1 if phase_offset else 0)) % 2 == 0)
        dy = -amplitude if up else amplitude
        y_ctrl = base_y + dy
        d += f" C{x0+seg*0.25:.1f},{y_ctrl:.1f} {x0+seg*0.75:.1f},{y_ctrl:.1f} {x2:.1f},{base_y:.1f}"
    return d


def build_wave_banner_svg(w, h, stops, crest_up, star_count, accent, seed):
    """A compact section-transition banner: 2 layered wave bands in the
    page gradient plus a light scattering of static twinkle stars, so the
    banners read as thin slices of the same night sky as the hero rather
    than an unrelated decorative element.

    The fill alone is too close in luminance to GitHub's own dark-mode
    background to read as a distinct shape at only 40px tall — confirmed
    by rendering it and comparing against a real dark page background, not
    assumed — so the crest line itself is traced in a fading accent-color
    stroke, the same rim-light trick as the hero's divider rule, to give
    the wave a visible edge regardless of how the fill blends into the page."""
    rng = random.Random(seed)
    stop_str = "".join(f'<stop offset="{p}%" stop-color="{c}"/>' for p, c in stops)
    base_y = h * (0.58 if crest_up else 0.42)
    back = wave_layer_path(w, h, base_y, h * 0.30, 3, crest_up, phase_offset=0)
    front_base_y = base_y + (7 if crest_up else -7)
    front = wave_layer_path(w, h, front_base_y, h * 0.20, 4, crest_up, phase_offset=1)
    front_edge = wave_crest_only(w, front_base_y, h * 0.20, 4, crest_up, phase_offset=1)

    stars = []
    for _ in range(star_count):
        x = rng.uniform(10, w - 10)
        y = rng.uniform(4, h - 4)
        r = rng.uniform(0.5, 1.3)
        op = rng.uniform(0.3, 0.75)
        dur = rng.uniform(2.6, 5.0)
        delay = rng.uniform(0, dur)
        stars.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{accent}">'
            f'<animate attributeName="opacity" values="{op*0.2:.2f};{op:.2f};{op*0.2:.2f}" '
            f'dur="{dur:.2f}s" begin="-{delay:.2f}s" repeatCount="indefinite"/></circle>'
        )

    return f'''<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
<defs>
<linearGradient id="waveBg" x1="0%" y1="0%" x2="100%" y2="0%">{stop_str}</linearGradient>
<linearGradient id="waveEdge" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="{accent}" stop-opacity="0"/>
<stop offset="50%" stop-color="{accent}" stop-opacity="0.55"/>
<stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
</linearGradient>
{grain_filter("waveGrain", seed)}
</defs>
<path d="{back}" fill="url(#waveBg)" opacity="0.6"/>
<path d="{front}" fill="url(#waveBg)"/>
<path d="{front_edge}" fill="none" stroke="url(#waveEdge)" stroke-width="1"/>
{"".join(stars)}
<rect width="{w}" height="{h}" filter="url(#waveGrain)" opacity="0.05"/>
</svg>'''


def build_wave_final_svg(cfg):
    """The page's closing bookend (replaces the venom footer) — richer than
    the thin transition banners: three horizon layers, a denser twinkling
    field, and a thin center ornament echoing the hero's divider rule, so
    the page closes on the same visual language it opened with."""
    W, H = 1500, 160
    primary, secondary = cfg["primary"], cfg["secondary"]
    stops = cfg["bg_stops"]
    stop_str = "".join(f'<stop offset="{p}%" stop-color="{c}"/>' for p, c in stops)
    rng = random.Random(cfg["seed"] + 7)

    layers = []
    specs = [(0.30, H * 0.82, 4, 0.35), (0.20, H * 0.64, 5, 0.6), (0.12, H * 0.46, 6, 1.0)]
    for amp_frac, base_y, humps, op in specs:
        path = wave_layer_path(W, H, base_y, H * amp_frac, humps, False, phase_offset=0)
        layers.append(f'<path d="{path}" fill="url(#waveBgFinal)" opacity="{op:.2f}"/>')
    top_amp, top_base_y, top_humps, _ = specs[-1]
    front_edge = wave_crest_only(W, top_base_y, H * top_amp, top_humps, False, phase_offset=0)

    stars = []
    for _ in range(26):
        x = rng.uniform(10, W - 10)
        y = rng.uniform(4, H * 0.40)
        r = rng.uniform(0.5, 1.5)
        op = rng.uniform(0.35, 0.8)
        dur = rng.uniform(2.4, 5.2)
        delay = rng.uniform(0, dur)
        stars.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="{primary}">'
            f'<animate attributeName="opacity" values="{op*0.18:.2f};{op:.2f};{op*0.18:.2f}" '
            f'dur="{dur:.2f}s" begin="-{delay:.2f}s" repeatCount="indefinite"/></circle>'
        )

    ornament = gen_divider_ornament(W / 2, H * 0.20, primary, 220, 36)
    embers = gen_embers(rng, 10, [primary, secondary, cfg["sparkle"]], W, H, y_lo_frac=0.6)

    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
<linearGradient id="waveBgFinal" x1="0%" y1="0%" x2="100%" y2="0%">{stop_str}</linearGradient>
<linearGradient id="waveEdgeFinal" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="{primary}" stop-opacity="0"/>
<stop offset="50%" stop-color="{primary}" stop-opacity="0.5"/>
<stop offset="100%" stop-color="{primary}" stop-opacity="0"/>
</linearGradient>
{grain_filter("waveFinalGrain", cfg["seed"])}
</defs>
<rect width="{W}" height="{H}" fill="{cfg["bg_stops"][0][1]}"/>
{"".join(stars)}
{"".join(layers)}
<path d="{front_edge}" fill="none" stroke="url(#waveEdgeFinal)" stroke-width="1.2"/>
{embers}
{ornament}
<rect width="{W}" height="{H}" filter="url(#waveFinalGrain)" opacity="0.05"/>
</svg>'''


# --------------------------------------------------------------------- seals

def build_seal_svg(glyph, color, seed):
    """A small emblem for a work-section project title — corner brackets
    (reusing the exact hero/stats bracket generator, just on a 64px
    canvas), a pulsing ring, and the project's own existing glyph, glowing.
    The work section was plain text/badges across every pass through
    Pass 5; this is its first generated visual."""
    W = H = 64
    cx = cy = 32
    ring_r = 21
    rng = random.Random(seed)
    ticks = []
    for i in range(14):
        ang = (i / 14) * 2 * math.pi + rng.uniform(-0.05, 0.05)
        x1, y1 = cx + math.cos(ang) * (ring_r - 2), cy + math.sin(ang) * (ring_r - 2)
        x2, y2 = cx + math.cos(ang) * (ring_r + 2), cy + math.sin(ang) * (ring_r + 2)
        ticks.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                      f'stroke="{color}" stroke-width="0.8" opacity="0.3"/>')
    brackets = gen_corner_brackets(color, W, H)
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
<filter id="sealGlow" x="-60%" y="-60%" width="220%" height="220%">
<feGaussianBlur stdDeviation="2.6"/>
</filter>
<radialGradient id="sealBg" cx="50%" cy="50%" r="50%">
<stop offset="0%" stop-color="{color}" stop-opacity="0.18"/>
<stop offset="100%" stop-color="{color}" stop-opacity="0"/>
</radialGradient>
</defs>
<circle cx="{cx}" cy="{cy}" r="27" fill="url(#sealBg)"/>
{brackets}
<circle cx="{cx}" cy="{cy}" r="{ring_r}" fill="none" stroke="{color}" stroke-width="1" opacity="0.35">
<animate attributeName="opacity" values="0.22;0.5;0.22" dur="5s" repeatCount="indefinite"/>
</circle>
{"".join(ticks)}
<text x="{cx}" y="{cy+8}" text-anchor="middle" font-family="'Segoe UI Symbol',sans-serif" '''\
           f'''font-size="24" fill="{color}" filter="url(#sealGlow)" opacity="0.65">{glyph}</text>
<text x="{cx}" y="{cy+8}" text-anchor="middle" font-family="'Segoe UI Symbol',sans-serif" '''\
           f'''font-size="24" fill="{color}">{glyph}</text>
</svg>'''


# ----------------------------------------------------------------- dividers

def build_divider_svg(color):
    W, H, cy = 1400, 24, 12
    ornament = gen_divider_ornament(W / 2, cy, color, (W - 120) / 2, 40)
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
{ornament}
</svg>'''


# ------------------------------------------------------------- panel headers

def build_panel_header_svg(title, subtitle, cfg):
    """A Steam-profile-style showcase header on a pure-black canvas."""
    W, H = 1500, 56
    primary = cfg["primary"]
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
<linearGradient id="panelBg" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="#671515"/><stop offset="90%" stop-color="#8c1616"/><stop offset="100%" stop-color="#2a0505"/>
</linearGradient>
<linearGradient id="panelEdge" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="{primary}" stop-opacity="0.9"/><stop offset="72%" stop-color="{primary}" stop-opacity="0.24"/><stop offset="100%" stop-color="{primary}" stop-opacity="0"/>
</linearGradient>
<linearGradient id="panelSweep" gradientUnits="userSpaceOnUse" x1="-260" y1="0" x2="0" y2="0">
<stop offset="0%" stop-color="#ffffff" stop-opacity="0"/><stop offset="50%" stop-color="#ffffff" stop-opacity="0.16"/><stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
<animate attributeName="x1" values="-260;1500" dur="8s" repeatCount="indefinite"/>
<animate attributeName="x2" values="0;1760" dur="8s" repeatCount="indefinite"/>
</linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="#000000"/>
<rect x="14" y="7" width="1472" height="42" rx="5" fill="#000000" opacity="0.78"/>
<rect x="18" y="9" width="1464" height="38" rx="4" fill="url(#panelBg)" opacity="0.94"/>
<rect x="18" y="9" width="5" height="38" rx="2" fill="{primary}"/>
<rect x="18" y="9" width="1464" height="38" rx="4" fill="url(#panelSweep)"/>
<rect x="18" y="46" width="1464" height="1" fill="url(#panelEdge)"/>
<text x="44" y="34" fill="#ffffff" font-family="'Segoe UI',Arial,sans-serif" font-size="17" font-weight="300" letter-spacing="3">{esc(title)}</text>
<text x="1456" y="33" text-anchor="end" fill="#c4c4c4" font-family="'Segoe UI',Arial,sans-serif" font-size="12" font-weight="400" letter-spacing="2">{esc(subtitle)}</text>
</svg>'''


# ------------------------------------------------------------------ tagline

def build_tagline_svg(cfg):
    """A self-hosted typewriter effect matching readme-typing-svg's look:
    each line clip-reveals left-to-right, holds, deletes, then the next
    line begins. Widths are pre-measured in an actual browser against the
    real embedded font (scripts/measure_tagline.py) rather than guessed
    from monospace-advance math, so the clip edge lines up with the glyphs
    exactly instead of clipping mid-character."""
    W, H = cfg["tagline"]["width"], cfg["tagline"]["height"]
    cx = W / 2
    type_ms = cfg["tagline"]["type_ms_per_char"]
    delete_ms = cfg["tagline"]["delete_ms_per_char"]
    hold_ms = cfg["tagline"]["hold_ms"]
    gap_ms = cfg["tagline"]["gap_ms"]
    dmmono = b64_font("dm-mono-500.woff2")

    segments = []
    t = 0.0
    for text, w in cfg["tagline"]["lines"]:
        left = cx - w / 2
        type_dur = len(text) * type_ms
        delete_dur = len(text) * delete_ms
        seg = {
            "text": text, "w": w, "left": left, "t_start": t,
            "t_type_end": t + type_dur,
            "t_hold_end": t + type_dur + hold_ms,
            "t_delete_end": t + type_dur + hold_ms + delete_dur,
        }
        t = seg["t_delete_end"] + gap_ms
        segments.append(seg)
    total = t

    y_text = H / 2 + 5
    y_clip_top = H / 2 - 12
    clip_h = 24

    clip_defs, texts = [], []
    for i, seg in enumerate(segments):
        kt = [0, seg["t_start"] / total, seg["t_type_end"] / total,
              seg["t_hold_end"] / total, seg["t_delete_end"] / total, 1]
        vals = [0, 0, seg["w"], seg["w"], 0, 0]
        kt_str = ";".join(f"{k:.5f}" for k in kt)
        vals_str = ";".join(f"{v:.2f}" for v in vals)
        clip_defs.append(
            f'<clipPath id="tclip{i}"><rect x="{seg["left"]:.2f}" y="{y_clip_top:.1f}" '
            f'width="0" height="{clip_h}">'
            f'<animate attributeName="width" keyTimes="{kt_str}" values="{vals_str}" '
            f'dur="{total/1000:.3f}s" repeatCount="indefinite"/></rect></clipPath>'
        )
        texts.append(
            f'<text x="{seg["left"]:.2f}" y="{y_text:.1f}" clip-path="url(#tclip{i})" '
            f'font-family="DM Mono" font-weight="500" font-size="14" letter-spacing="0.5" '
            f'fill="{cfg["muted"]}">{esc(seg["text"])}</text>'
        )

    cur_kt, cur_vals = [], []
    for i, seg in enumerate(segments):
        cur_kt += [seg["t_start"] / total, seg["t_type_end"] / total,
                   seg["t_hold_end"] / total, seg["t_delete_end"] / total]
        cur_vals += [seg["left"], seg["left"] + seg["w"], seg["left"] + seg["w"], seg["left"]]
        next_start = segments[i + 1]["t_start"] if i + 1 < len(segments) else total
        cur_kt.append(next_start / total)
        cur_vals.append(seg["left"])
    cur_kt_str = ";".join(f"{k:.5f}" for k in cur_kt)
    cur_vals_str = ";".join(f"{v:.2f}" for v in cur_vals)

    cursor = (
        f'<g>'
        f'<rect y="{y_clip_top+1:.1f}" width="4" height="{clip_h-2}" fill="{cfg["primary"]}" '
        f'opacity="0.35" filter="url(#cursorGlow)">'
        f'<animate attributeName="x" keyTimes="{cur_kt_str}" values="{cur_vals_str}" '
        f'dur="{total/1000:.3f}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" keyTimes="0;0.12;0.3;0.46;0.62;0.7;1" '
        f'values="0.35;0.28;0.35;0.08;0;0;0.35" dur="1.1s" repeatCount="indefinite"/>'
        f'</rect>'
        f'<rect y="{y_clip_top+2:.1f}" width="1.6" height="{clip_h-4}" fill="{cfg["primary"]}">'
        f'<animate attributeName="x" keyTimes="{cur_kt_str}" values="{cur_vals_str}" '
        f'dur="{total/1000:.3f}s" repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" keyTimes="0;0.12;0.3;0.46;0.62;0.7;1" '
        f'values="1;0.88;1;0.25;0;0;1" dur="1.1s" repeatCount="indefinite"/>'
        f'</rect>'
        f'</g>'
    )

    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
<style>
@font-face {{ font-family: 'DM Mono'; font-weight: 500; src: url(data:font/woff2;base64,{dmmono}) format('woff2'); }}
</style>
<filter id="cursorGlow" x="-300%" y="-100%" width="700%" height="300%">
<feGaussianBlur stdDeviation="2.4"/>
</filter>
{grain_filter("taglineGrain", cfg["seed"])}
{"".join(clip_defs)}
</defs>
{"".join(texts)}
{cursor}
<rect width="{W}" height="{H}" filter="url(#taglineGrain)" opacity="0.04"/>
</svg>'''


# ======================================================= cinematic experience

def mono_font_defs():
    """Embed only DM Mono for compact controls and information panels."""
    dmmono = b64_font("dm-mono-500.woff2")
    return (
        "<style>"
        f"@font-face {{ font-family:'DM Mono'; font-weight:500; "
        f"src:url(data:font/woff2;base64,{dmmono}) format('woff2'); }}"
        ".mono{font-family:'DM Mono','Courier New',monospace;font-weight:500}"
        "</style>"
    )


def experience_font_defs():
    cormorant = b64_font("cormorant-garamond-600.woff2")
    dmmono = b64_font("dm-mono-500.woff2")
    return (
        "<style>"
        f"@font-face {{ font-family:'Cormorant Garamond'; font-weight:600; "
        f"src:url(data:font/woff2;base64,{cormorant}) format('woff2'); }}"
        f"@font-face {{ font-family:'DM Mono'; font-weight:500; "
        f"src:url(data:font/woff2;base64,{dmmono}) format('woff2'); }}"
        ".serif{font-family:'Cormorant Garamond',Georgia,serif;font-weight:600}"
        ".mono{font-family:'DM Mono','Courier New',monospace;font-weight:500}"
        "</style>"
    )


def kinetic_glyph_svg(kind, x, y, scale=1.0, delay=0.0):
    """Render a compact animated pictogram before dense information.

    The glyphs deliberately use geometry instead of Unicode symbols so they
    stay consistent across GitHub renderers, operating systems, and fallback
    fonts. Every icon shares the same 64 px visual grammar and can be scaled
    into proof cards, dossier labels, timelines, or loadout rows.
    """
    accent = "#e84b4b"
    signal = "#ff8a7f"
    paper = "#f5eaea"
    muted = "#8d7777"
    begin = f"-{delay:.2f}s"

    if kind == "apps":
        marks = []
        for index, (gx, gy) in enumerate(((19, 19), (34, 19), (19, 34), (34, 34))):
            marks.append(
                f'<rect x="{gx}" y="{gy}" width="11" height="11" rx="2" '
                f'fill="{accent}" opacity=".32"><animate attributeName="opacity" '
                f'values=".25;1;.25" dur="2s" begin="-{index * .24:.2f}s" '
                f'repeatCount="indefinite"/></rect>'
            )
        icon = "".join(marks)
    elif kind == "tests":
        icon = f'''
<circle cx="32" cy="32" r="16" fill="none" stroke="{accent}" stroke-width="2"/>
<path d="M23 32l6 6 13-15" fill="none" stroke="{paper}" stroke-width="3"
 stroke-linecap="round" stroke-linejoin="round"/>
<path d="M18 20a20 20 0 0 1 27-1" fill="none" stroke="{signal}" stroke-width="2"
 stroke-linecap="round"><animate attributeName="stroke-dasharray" values="2 60;34 60;2 60"
 dur="2.8s" begin="{begin}" repeatCount="indefinite"/></path>'''
    elif kind == "accuracy":
        icon = f'''
<path d="M16 42a18 18 0 0 1 32 0" fill="none" stroke="{accent}" stroke-width="4"
 stroke-linecap="round"/>
<path d="M20 42a14 14 0 0 1 24 0" fill="none" stroke="{muted}" stroke-width="1.5"/>
<line x1="32" y1="42" x2="32" y2="24" stroke="{paper}" stroke-width="2.5"
 stroke-linecap="round"><animateTransform attributeName="transform" type="rotate"
 values="-48 32 42;43 32 42;-48 32 42" dur="3.2s" begin="{begin}"
 repeatCount="indefinite"/></line><circle cx="32" cy="42" r="4" fill="{signal}"/>'''
    elif kind == "prototypes":
        icon = f'''
<path d="M32 14c8 6 12 14 12 23l-12 9-12-9c0-9 4-17 12-23Z" fill="none"
 stroke="{accent}" stroke-width="2"/><circle cx="32" cy="29" r="4" fill="{paper}"/>
<path d="M25 44l-4 8M32 47v9M39 44l4 8" stroke="{signal}" stroke-width="2"
 stroke-linecap="round"><animate attributeName="opacity" values=".2;1;.2" dur="1.1s"
 begin="{begin}" repeatCount="indefinite"/></path>'''
    elif kind in {"mission", "target"}:
        icon = f'''
<circle cx="32" cy="32" r="16" fill="none" stroke="{accent}" stroke-width="2"/>
<circle cx="32" cy="32" r="6" fill="none" stroke="{signal}" stroke-width="2">
<animate attributeName="r" values="4;11;4" dur="2.4s" begin="{begin}" repeatCount="indefinite"/>
<animate attributeName="opacity" values="1;.25;1" dur="2.4s" begin="{begin}" repeatCount="indefinite"/>
</circle><path d="M32 10v10M32 44v10M10 32h10M44 32h10" stroke="{muted}"/>'''
    elif kind in {"proof", "shield"}:
        icon = f'''
<path d="M32 13l16 6v11c0 11-6 18-16 22-10-4-16-11-16-22V19l16-6Z" fill="none"
 stroke="{accent}" stroke-width="2"/><path d="M24 32l6 6 11-13" fill="none" stroke="{paper}"
 stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="32" cy="32" r="22" fill="none" stroke="{signal}" opacity=".35"
 stroke-dasharray="4 8"><animateTransform attributeName="transform" type="rotate"
 from="0 32 32" to="360 32 32" dur="8s" begin="{begin}" repeatCount="indefinite"/></circle>'''
    elif kind in {"stack", "layers"}:
        icon = f'''
<path d="M14 24l18-10 18 10-18 10-18-10Z" fill="none" stroke="{paper}" stroke-width="2"/>
<path d="M14 33l18 10 18-10M14 42l18 10 18-10" fill="none" stroke="{accent}"
 stroke-width="2" stroke-linejoin="round"><animate attributeName="opacity" values=".35;1;.35"
 dur="2.4s" begin="{begin}" repeatCount="indefinite"/></path>'''
    elif kind == "telecom":
        icon = f'''
<path d="M32 20v30M24 50h16M27 50l5-22 5 22" fill="none" stroke="{paper}" stroke-width="2"/>
<circle cx="32" cy="19" r="3" fill="{signal}"/>
<path d="M22 15a14 14 0 0 0 0 9M42 15a14 14 0 0 1 0 9M15 10a23 23 0 0 0 0 19M49 10a23 23 0 0 1 0 19"
 fill="none" stroke="{accent}" stroke-width="2" stroke-linecap="round">
<animate attributeName="opacity" values=".25;1;.25" dur="1.8s" begin="{begin}" repeatCount="indefinite"/>
</path>'''
    elif kind == "education":
        icon = f'''
<path d="M14 23l18-9 18 9-18 9-18-9Z" fill="none" stroke="{paper}" stroke-width="2"/>
<path d="M21 28v11c7 6 15 6 22 0V28M50 24v17" fill="none" stroke="{accent}" stroke-width="2"/>
<circle cx="50" cy="44" r="3" fill="{signal}"><animate attributeName="opacity"
 values=".25;1;.25" dur="1.6s" begin="{begin}" repeatCount="indefinite"/></circle>'''
    elif kind == "product":
        icon = f'''
<rect x="14" y="16" width="36" height="32" rx="3" fill="none" stroke="{paper}" stroke-width="2"/>
<path d="M14 24h36" stroke="{accent}" stroke-width="2"/><circle cx="19" cy="20" r="2" fill="{signal}"/>
<rect x="19" y="30" width="11" height="12" rx="2" fill="{accent}" opacity=".6"/>
<path d="M35 31h10M35 37h8M35 43h6" stroke="{muted}" stroke-width="2" stroke-linecap="round"/>'''
    elif kind == "backend":
        icon = f'''
<rect x="15" y="15" width="34" height="10" rx="3" fill="none" stroke="{paper}" stroke-width="2"/>
<rect x="15" y="28" width="34" height="10" rx="3" fill="none" stroke="{accent}" stroke-width="2"/>
<rect x="15" y="41" width="34" height="10" rx="3" fill="none" stroke="{paper}" stroke-width="2"/>
<g fill="{signal}"><circle cx="21" cy="20" r="2"/><circle cx="21" cy="33" r="2"/>
<circle cx="21" cy="46" r="2"><animate attributeName="opacity" values=".2;1;.2" dur="1.2s"
 begin="{begin}" repeatCount="indefinite"/></circle></g>'''
    elif kind == "ml":
        icon = f'''
<path d="M18 22l14 10 14-14M18 42l14-10 14 12" fill="none" stroke="{accent}" stroke-width="1.8"
 stroke-dasharray="4 4"><animate attributeName="stroke-dashoffset" values="0;-24" dur="3s"
 begin="{begin}" repeatCount="indefinite"/></path>
<g fill="{paper}"><circle cx="18" cy="22" r="5"/><circle cx="18" cy="42" r="5"/>
<circle cx="32" cy="32" r="6" fill="{signal}"/><circle cx="46" cy="18" r="5"/><circle cx="46" cy="44" r="5"/></g>'''
    elif kind == "platform":
        icon = f'''
<path d="M32 13l18 10v20L32 53 14 43V23l18-10Z" fill="none" stroke="{accent}" stroke-width="2"/>
<path d="M14 23l18 10 18-10M32 33v20" fill="none" stroke="{paper}" stroke-width="2"/>
<path d="M21 27l18-10" stroke="{signal}" stroke-width="2"><animate attributeName="opacity"
 values=".25;1;.25" dur="2s" begin="{begin}" repeatCount="indefinite"/></path>'''
    elif kind == "expanding":
        icon = f'''
<path d="M32 13v38M13 32h38M19 19l26 26M45 19L19 45" stroke="{accent}" stroke-width="2"
 stroke-linecap="round"/><circle cx="32" cy="32" r="7" fill="{signal}"/>
<circle cx="32" cy="32" r="10" fill="none" stroke="{paper}" opacity=".7">
<animate attributeName="r" values="8;25;8" dur="2.8s" begin="{begin}" repeatCount="indefinite"/>
<animate attributeName="opacity" values=".8;0;.8" dur="2.8s" begin="{begin}" repeatCount="indefinite"/>
</circle>'''
    elif kind == "gpu":
        coords = [(20 + col * 12, 20 + row * 12) for row in range(3) for col in range(3)]
        icon = "".join(
            f'<circle cx="{gx}" cy="{gy}" r="3" fill="{signal}" opacity=".35">'
            f'<animate attributeName="r" values="2;5;2" dur="2.2s" '
            f'begin="-{index * .13:.2f}s" repeatCount="indefinite"/></circle>'
            for index, (gx, gy) in enumerate(coords)
        )
        icon += f'<rect x="14" y="14" width="36" height="36" rx="4" fill="none" stroke="{accent}"/>'
    elif kind == "realtime":
        icon = f'''
<path d="M12 34h8l5-13 8 25 7-18 5 6h8" fill="none" stroke="{accent}" stroke-width="2.4"
 stroke-linecap="round" stroke-linejoin="round"/>
<circle r="4" fill="{signal}"><animateMotion path="M12 34h8l5-13 8 25 7-18 5 6h8"
 dur="2.6s" begin="{begin}" repeatCount="indefinite"/></circle>'''
    elif kind == "vision":
        icon = f'''
<path d="M11 32s8-14 21-14 21 14 21 14-8 14-21 14S11 32 11 32Z" fill="none"
 stroke="{accent}" stroke-width="2"/><circle cx="32" cy="32" r="9" fill="none" stroke="{paper}" stroke-width="2"/>
<circle cx="32" cy="32" r="3" fill="{signal}"/>
<line x1="15" y1="24" x2="49" y2="24" stroke="{signal}" opacity=".5">
<animate attributeName="y1" values="22;42;22" dur="2.4s" begin="{begin}" repeatCount="indefinite"/>
<animate attributeName="y2" values="22;42;22" dur="2.4s" begin="{begin}" repeatCount="indefinite"/>
</line>'''
    else:
        icon = f'<circle cx="32" cy="32" r="12" fill="none" stroke="{accent}" stroke-width="2"/><circle cx="32" cy="32" r="4" fill="{signal}"/>'

    return f'''
<g data-kinetic-glyph="{esc(kind)}" transform="translate({x},{y}) scale({scale})">
<rect x="1" y="1" width="62" height="62" rx="11" fill="#070101" stroke="#3d0b0b"/>
<path d="M8 17V8h9M47 8h9v9M8 47v9h9M47 56h9v-9" fill="none" stroke="{accent}"
 stroke-width="1.3" opacity=".7"/>
<circle cx="32" cy="32" r="26" fill="none" stroke="{accent}" opacity=".18" stroke-dasharray="2 7">
<animateTransform attributeName="transform" type="rotate" from="0 32 32" to="360 32 32"
 dur="11s" begin="{begin}" repeatCount="indefinite"/>
</circle>
{icon}
</g>'''


def build_cinematic_hero_svg(cfg):
    """A self-contained title sequence: original raster key art plus a
    GitHub-safe animated HUD, scan pass, signal traces, and identity lockup."""
    W, H = 1500, 620
    art = asset_data_uri(VISUAL_CONTRACT["optimized_hero"])
    fonts = experience_font_defs()
    rng = random.Random(cfg["seed"] + 900)

    embers = []
    for i in range(28):
        x = rng.uniform(20, W - 20)
        y = rng.uniform(H * 0.45, H + 30)
        rise = rng.uniform(70, 220)
        drift = rng.uniform(-28, 28)
        dur = rng.uniform(4.5, 10.5)
        delay = rng.uniform(0, dur)
        embers.append(
            f'<circle r="{rng.uniform(0.8, 2.1):.2f}" fill="{cfg["sparkle"]}">'
            f'<animate attributeName="opacity" values="0;0.8;0.25;0" '
            f'keyTimes="0;.12;.72;1" dur="{dur:.2f}s" begin="-{delay:.2f}s" '
            f'repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="{x:.1f},{y:.1f};{x+drift:.1f},{y-rise:.1f}" '
            f'dur="{dur:.2f}s" begin="-{delay:.2f}s" repeatCount="indefinite"/>'
            "</circle>"
        )

    telemetry = []
    for i, width in enumerate((420, 350, 280)):
        y = 72 + i * 18
        telemetry.append(
            f'<path d="M70 {y} H{70+width}" stroke="#e84b4b" stroke-width="1" '
            f'opacity="{0.34-i*0.07:.2f}" stroke-dasharray="5 12">'
            f'<animate attributeName="stroke-dashoffset" values="0;-68" '
            f'dur="{4.0+i*1.4:.1f}s" repeatCount="indefinite"/></path>'
        )

    chips = [
        (74, "PRODUCT", "REACT + NEXT"),
        (250, "APPLIED", "PYTHON + ML"),
        (482, "NEXT", "GENAI + AWS"),
    ]
    chip_svg = []
    for x, label, value in chips:
        width = 160 if x == 74 else 216 if x == 250 else 220
        chip_svg.append(
            f'<g transform="translate({x},520)">'
            f'<rect width="{width}" height="48" rx="3" fill="#050505" '
            f'stroke="#671515" stroke-width="1"/>'
            f'<rect width="4" height="48" rx="2" fill="#e84b4b"/>'
            f'<text x="18" y="18" class="mono" font-size="10" fill="#8d7777" '
            f'letter-spacing="2">{label}</text>'
            f'<text x="18" y="36" class="mono" font-size="14" fill="#f5eaea" '
            f'letter-spacing="1">{value}</text></g>'
        )

    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{fonts}
<clipPath id="heroClip"><rect x="10" y="10" width="1480" height="600" rx="8"/></clipPath>
<linearGradient id="heroShade" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="#000" stop-opacity=".98"/>
<stop offset="37%" stop-color="#000" stop-opacity=".88"/>
<stop offset="61%" stop-color="#000" stop-opacity=".18"/>
<stop offset="100%" stop-color="#000" stop-opacity=".05"/>
</linearGradient>
<linearGradient id="heroBottom" x1="0%" y1="0%" x2="0%" y2="100%">
<stop offset="46%" stop-color="#000" stop-opacity="0"/>
<stop offset="100%" stop-color="#000" stop-opacity=".9"/>
</linearGradient>
<linearGradient id="scan" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="#e84b4b" stop-opacity="0"/>
<stop offset="50%" stop-color="#ff8a7f" stop-opacity=".34"/>
<stop offset="100%" stop-color="#e84b4b" stop-opacity="0"/>
</linearGradient>
<pattern id="scanlines" width="8" height="8" patternUnits="userSpaceOnUse">
<rect width="8" height="1" fill="#fff" opacity=".025"/>
</pattern>
<pattern id="microgrid" width="32" height="32" patternUnits="userSpaceOnUse">
<path d="M32 0H0V32" fill="none" stroke="#e84b4b" stroke-width=".45" opacity=".08"/>
</pattern>
<filter id="heroGlow" x="-40%" y="-80%" width="180%" height="260%">
<feGaussianBlur stdDeviation="7"/>
</filter>
<filter id="softHero" x="-30%" y="-30%" width="160%" height="160%">
<feGaussianBlur stdDeviation="18"/>
</filter>
{grain_filter("experienceGrain", cfg["seed"] + 900)}
</defs>
<rect width="{W}" height="{H}" rx="10" fill="#000"/>
<g clip-path="url(#heroClip)">
<image href="{art}" x="4" y="4" width="1492" height="612" preserveAspectRatio="xMidYMid slice">
<animate attributeName="x" values="4;-8;4" dur="26s" repeatCount="indefinite"/>
<animate attributeName="y" values="4;-3;4" dur="26s" repeatCount="indefinite"/>
<animate attributeName="width" values="1492;1516;1492" dur="26s" repeatCount="indefinite"/>
<animate attributeName="height" values="612;626;612" dur="26s" repeatCount="indefinite"/>
</image>
<rect x="10" y="10" width="1480" height="600" fill="url(#heroShade)"/>
<rect x="10" y="10" width="1480" height="600" fill="url(#heroBottom)"/>
<rect x="10" y="10" width="1480" height="600" fill="url(#microgrid)"/>
<rect x="10" y="10" width="1480" height="600" fill="url(#scanlines)"/>
<rect x="-220" y="10" width="180" height="600" fill="url(#scan)" opacity=".72">
<animate attributeName="x" values="-220;1540" dur="8s" repeatCount="indefinite"/>
</rect>
<ellipse cx="1120" cy="220" rx="250" ry="250" fill="none" stroke="#e84b4b"
 stroke-width="1" opacity=".16" stroke-dasharray="12 20">
<animateTransform attributeName="transform" type="rotate" from="0 1120 220"
 to="360 1120 220" dur="38s" repeatCount="indefinite"/>
</ellipse>
<ellipse cx="1120" cy="220" rx="276" ry="276" fill="none" stroke="#ff8a7f"
 stroke-width=".7" opacity=".1" stroke-dasharray="2 16">
<animateTransform attributeName="transform" type="rotate" from="360 1120 220"
 to="0 1120 220" dur="28s" repeatCount="indefinite"/>
</ellipse>
{"".join(embers)}
</g>
<rect x="10" y="10" width="1480" height="600" rx="8" fill="none" stroke="#3b0b0b"/>
<rect x="22" y="22" width="1456" height="576" rx="5" fill="none" stroke="#e84b4b"
 stroke-width=".7" opacity=".18" stroke-dasharray="44 14"/>
{"".join(telemetry)}
<circle cx="74" cy="38" r="4" fill="#e84b4b">
<animate attributeName="opacity" values=".3;1;.3" dur="1.6s" repeatCount="indefinite"/>
</circle>
<text x="90" y="43" class="mono" font-size="11" fill="#c4c4c4" letter-spacing="2.6">
AYR // OPERATOR ONLINE
</text>
<text x="1426" y="43" text-anchor="end" class="mono" font-size="10" fill="#8d7777"
 letter-spacing="2">INDIA · UTC+05:30 · BUILD 2026</text>
<text x="72" y="154" class="mono" font-size="12" fill="#e84b4b" letter-spacing="4">
{esc(cfg["role"])}
</text>
<text x="68" y="270" class="serif" font-size="116" fill="#e84b4b" opacity=".55"
 filter="url(#heroGlow)">AYUSH</text>
<text x="68" y="270" class="serif" font-size="116" fill="#f8eeee" letter-spacing="4">AYUSH</text>
<text x="68" y="370" class="serif" font-size="116" fill="#f8eeee" letter-spacing="4">ROY</text>
<g opacity=".48" transform="translate(3,0)">
<text x="68" y="370" class="serif" font-size="116" fill="#e84b4b" letter-spacing="4">
ROY
<animate attributeName="opacity" values="0;0;.52;0;0" keyTimes="0;.71;.715;.73;1"
 dur="6.4s" repeatCount="indefinite"/>
</text>
</g>
<rect x="72" y="400" width="524" height="2" fill="#671515"/>
<rect x="72" y="400" width="120" height="2" fill="#ff8a7f">
<animate attributeName="x" values="72;476;72" dur="5s" repeatCount="indefinite"/>
</rect>
<text x="72" y="440" class="mono" font-size="18" fill="#d6c8c8" letter-spacing="1.4">
BUILDING THE SOFTWARE LAYER
</text>
<text x="72" y="470" class="mono" font-size="18" fill="#d6c8c8" letter-spacing="1.4">
FOR THE PHYSICAL WORLD.
</text>
{"".join(chip_svg)}
<g transform="translate(1392,545)">
<circle r="34" fill="#000" opacity=".65" stroke="#e84b4b" stroke-width="1"/>
<circle r="24" fill="none" stroke="#e84b4b" stroke-width="1" stroke-dasharray="4 8">
<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="7s"
 repeatCount="indefinite"/>
</circle>
<circle r="4" fill="#ff8a7f">
<animate attributeName="r" values="3;6;3" dur="2s" repeatCount="indefinite"/>
</circle>
</g>
<rect width="{W}" height="{H}" filter="url(#experienceGrain)" opacity=".035"/>
</svg>'''


def build_nav_button_svg(label, code, glyph, cfg, seed):
    W, H = 350, 72
    rng = random.Random(seed)
    ticks = "".join(
        f'<rect x="{18+i*17}" y="60" width="{rng.randint(5,13)}" height="1" '
        f'fill="#e84b4b" opacity="{rng.uniform(.18,.65):.2f}"/>'
        for i in range(18)
    )
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<title>{esc(label)} — {esc(code)}</title>
<defs>
{mono_font_defs()}
<linearGradient id="navBg" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" stop-color="#050505"/><stop offset="72%" stop-color="#130303"/>
<stop offset="100%" stop-color="#300707"/>
</linearGradient>
<linearGradient id="navSweep" gradientUnits="userSpaceOnUse" x1="-120" x2="0">
<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff"
 stop-opacity=".14"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
<animate attributeName="x1" values="-120;350" dur="6s" repeatCount="indefinite"/>
<animate attributeName="x2" values="0;470" dur="6s" repeatCount="indefinite"/>
</linearGradient>
</defs>
<rect x="1" y="1" width="348" height="70" rx="4" fill="url(#navBg)" stroke="#671515"/>
<rect x="1" y="1" width="5" height="70" rx="2" fill="#e84b4b"/>
<rect x="1" y="1" width="348" height="70" rx="4" fill="url(#navSweep)"/>
<text x="24" y="44" class="mono" font-size="25" fill="#e84b4b">{esc(glyph)}</text>
<text x="68" y="31" class="mono" font-size="13" fill="#f5eaea" letter-spacing="2">{esc(label)}</text>
<text x="68" y="49" class="mono" font-size="9" fill="#8d7777" letter-spacing="2">{esc(code)}</text>
<text x="326" y="40" text-anchor="end" class="mono" font-size="19" fill="#e84b4b">→</text>
{ticks}
</svg>'''


def build_signal_strip_svg(cfg):
    W, H = 1500, 52
    phrase = "GEOSPATIAL  ·  REALTIME  ·  COMPUTER VISION  ·  SYSTEMS  ·  3D  ·  APPLIED AI  ·  "
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<title>Live capability signal</title>
<defs>
{mono_font_defs()}
<linearGradient id="signalFade" x1="0%" x2="100%">
<stop offset="0%" stop-color="#000"/><stop offset="8%" stop-color="#000" stop-opacity="0"/>
<stop offset="92%" stop-color="#000" stop-opacity="0"/><stop offset="100%" stop-color="#000"/>
</linearGradient>
<clipPath id="signalClip"><rect x="170" y="0" width="1330" height="52"/></clipPath>
</defs>
<rect width="{W}" height="{H}" fill="#030303"/>
<rect width="{W}" height="1" fill="#671515"/>
<rect y="51" width="{W}" height="1" fill="#2a0505"/>
<rect x="18" y="12" width="132" height="28" rx="3" fill="#671515"/>
<circle cx="34" cy="26" r="4" fill="#ff8a7f">
<animate attributeName="opacity" values=".2;1;.2" dur="1.3s" repeatCount="indefinite"/>
</circle>
<text x="48" y="30" class="mono" font-size="10" fill="#fff" letter-spacing="2">LIVE SIGNAL</text>
<g clip-path="url(#signalClip)">
<text y="32" class="mono" font-size="13" fill="#bcaeae" letter-spacing="3">
<tspan x="170">{phrase}{phrase}</tspan>
<animateTransform attributeName="transform" type="translate" values="0 0;-1120 0"
 dur="18s" repeatCount="indefinite"/>
</text>
</g>
<rect x="150" width="1350" height="52" fill="url(#signalFade)" pointer-events="none"/>
</svg>'''


def build_section_header_svg(index, title, subtitle, cfg):
    W, H = 1500, 96
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<title>Section {esc(index)} — {esc(title)}</title>
<defs>
{mono_font_defs()}
<linearGradient id="sectionRail" x1="0%" x2="100%">
<stop offset="0%" stop-color="#e84b4b"/><stop offset="58%" stop-color="#671515"/>
<stop offset="100%" stop-color="#000" stop-opacity="0"/>
</linearGradient>
<linearGradient id="sectionSweep" gradientUnits="userSpaceOnUse" x1="-180" x2="0">
<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff"
 stop-opacity=".22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
<animate attributeName="x1" values="-180;1500" dur="8s" repeatCount="indefinite"/>
<animate attributeName="x2" values="0;1680" dur="8s" repeatCount="indefinite"/>
</linearGradient>
</defs>
<rect width="{W}" height="{H}" fill="#000"/>
<text x="20" y="78" font-family="Georgia,serif" font-weight="700" font-size="86" fill="#671515" opacity=".34">{esc(index)}</text>
<rect x="112" y="16" width="1370" height="64" rx="4" fill="#080202" stroke="#310808"/>
<rect x="112" y="16" width="8" height="64" rx="2" fill="#e84b4b"/>
<rect x="120" y="16" width="1362" height="64" fill="url(#sectionSweep)"/>
<text x="148" y="49" class="mono" font-size="18" fill="#f5eaea" letter-spacing="4">{esc(title)}</text>
<text x="148" y="67" class="mono" font-size="9" fill="#9b8585" letter-spacing="2.2">{esc(subtitle)}</text>
<rect x="112" y="79" width="1370" height="1" fill="url(#sectionRail)"/>
<circle cx="1442" cy="48" r="15" fill="none" stroke="#e84b4b" opacity=".42"
 stroke-dasharray="3 6">
<animateTransform attributeName="transform" type="rotate" from="0 1442 48"
 to="360 1442 48" dur="6s" repeatCount="indefinite"/>
</circle>
<circle cx="1442" cy="48" r="3" fill="#ff8a7f">
<animate attributeName="opacity" values=".2;1;.2" dur="1.4s" repeatCount="indefinite"/>
</circle>
</svg>'''


def build_proof_card_svg(item, index, cfg):
    """A compact metric card that remains readable beside the nav controls."""
    W, H = 350, 138
    glyph = kinetic_glyph_svg(item["id"], 22, 36, .64, index * .31)
    detail_lines = wrap_lines(item["detail"].upper(), 43)[:2]
    detail_svg = "".join(
        f'<tspan x="24" dy="{0 if line_index == 0 else 15}">{esc(line)}</tspan>'
        for line_index, line in enumerate(detail_lines)
    )
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<title>{esc(item["value"])} {esc(item["label"])}</title>
<desc>{esc(item["detail"])}</desc>
<defs>
{mono_font_defs()}
<linearGradient id="proofBg" x1="0%" x2="100%">
<stop offset="0" stop-color="#030303"/><stop offset="72%" stop-color="#110202"/>
<stop offset="1" stop-color="#2b0606"/>
</linearGradient>
<linearGradient id="proofSweep" gradientUnits="userSpaceOnUse" x1="-120" x2="0">
<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#ff8a7f" stop-opacity=".16"/>
<stop offset="1" stop-color="#fff" stop-opacity="0"/>
<animate attributeName="x1" values="-120;350" dur="7s" begin="-{index * .7:.1f}s" repeatCount="indefinite"/>
<animate attributeName="x2" values="0;470" dur="7s" begin="-{index * .7:.1f}s" repeatCount="indefinite"/>
</linearGradient>
</defs>
<rect x="1" y="1" width="348" height="136" rx="5" fill="url(#proofBg)" stroke="#4b0e0e"/>
<rect x="1" y="1" width="5" height="136" rx="2" fill="#e84b4b"/>
<rect x="1" y="1" width="348" height="136" rx="5" fill="url(#proofSweep)"/>
<text x="24" y="26" class="mono" font-size="9" fill="#8d7777" letter-spacing="2">VERIFIED // {index + 1:02d}</text>
{glyph}
<text x="82" y="67" class="mono" font-size="32" fill="#f5eaea">{esc(item["value"])}</text>
<text x="166" y="62" class="mono" font-size="10" fill="#e84b4b" letter-spacing="1.4">{esc(item["label"])}</text>
<rect x="24" y="82" width="302" height="1" fill="#310808"/>
<text x="24" y="105" class="mono" font-size="8" fill="#a99494" letter-spacing=".6">{detail_svg}</text>
<circle cx="324" cy="22" r="4" fill="#ff8a7f">
<animate attributeName="opacity" values=".2;1;.2" dur="{1.2 + index * .18:.2f}s" repeatCount="indefinite"/>
</circle>
</svg>'''


def build_project_dossier_svg(project, cfg):
    """Render all project copy as one cinematic, data-complete dossier."""
    W, H = 720, 380
    code = f'SYS-{project["order"]:02d}'
    summary_lines = wrap_lines(project["summary"], 72)[:3]
    summary_svg = "".join(
        f'<tspan x="30" dy="{0 if index == 0 else 23}">{esc(line)}</tspan>'
        for index, line in enumerate(summary_lines)
    )
    proof_svg = "".join(
        f'<g transform="translate(30,{218 + index * 27})">'
        f'<circle cx="5" cy="-5" r="4" fill="#e84b4b"><animate attributeName="opacity" '
        f'values=".25;1;.25" dur="{1.2 + index * .23:.2f}s" repeatCount="indefinite"/></circle>'
        f'<text x="20" class="mono" font-size="15" fill="#d7caca">{esc(item)}</text></g>'
        for index, item in enumerate(project["proof"])
    )
    stack_lines = wrap_lines(" · ".join(project["stack"]), 88)[:2]
    stack_svg = "".join(
        f'<tspan x="30" dy="{0 if index == 0 else 18}">{esc(line)}</tspan>'
        for index, line in enumerate(stack_lines)
    )
    mission_glyph = kinetic_glyph_svg("mission", 28, 94, .34, project["order"] * .17)
    proof_glyph = kinetic_glyph_svg("proof", 28, 177, .34, project["order"] * .23)
    stack_glyph = kinetic_glyph_svg("stack", 28, 307, .34, project["order"] * .29)
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<title>{esc(code)} — {esc(project["name"])}</title>
<desc>{esc(project["summary"])} Proof: {esc("; ".join(project["proof"]))}. Stack: {esc("; ".join(project["stack"]))}.</desc>
<defs>
{mono_font_defs()}
<linearGradient id="dossierBg" x1="0%" x2="100%">
<stop offset="0" stop-color="#020202"/><stop offset="62%" stop-color="#090101"/>
<stop offset="100%" stop-color="#240505"/>
</linearGradient>
<linearGradient id="dossierSweep" gradientUnits="userSpaceOnUse" x1="-180" x2="0">
<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#ff8a7f" stop-opacity=".11"/>
<stop offset="1" stop-color="#fff" stop-opacity="0"/>
<animate attributeName="x1" values="-180;720" dur="9s" repeatCount="indefinite"/>
<animate attributeName="x2" values="0;900" dur="9s" repeatCount="indefinite"/>
</linearGradient>
<pattern id="dossierGrid" width="24" height="24" patternUnits="userSpaceOnUse">
<path d="M24 0H0V24" fill="none" stroke="#671515" stroke-width=".4" opacity=".09"/>
</pattern>
</defs>
<rect x="1" y="1" width="718" height="378" rx="7" fill="url(#dossierBg)" stroke="#4b0e0e"/>
<rect x="1" y="1" width="718" height="378" rx="7" fill="url(#dossierGrid)"/>
<rect x="1" y="1" width="718" height="378" rx="7" fill="url(#dossierSweep)"/>
<rect x="20" y="18" width="6" height="58" rx="2" fill="#e84b4b"/>
<text x="42" y="38" class="mono" font-size="10" fill="#8d7777" letter-spacing="2.2">{esc(code)} // {esc(project["codename"])}</text>
<text x="42" y="68" class="mono" font-size="25" fill="#f5eaea" letter-spacing=".8">{esc(project["name"].upper())}</text>
<text x="690" y="37" text-anchor="end" class="mono" font-size="10" fill="#e84b4b" letter-spacing="1.4">{esc(project["status"].upper())}</text>
<text x="690" y="59" text-anchor="end" class="mono" font-size="10" fill="#a99494">{esc(project["period"].upper())}</text>
<path d="M20 88H700" stroke="#310808"/>
{mission_glyph}
<text x="58" y="111" class="mono" font-size="9" fill="#e84b4b" letter-spacing="2">MISSION</text>
<text x="30" y="137" class="mono" font-size="16" fill="#d7caca">{summary_svg}</text>
{proof_glyph}
<text x="58" y="194" class="mono" font-size="9" fill="#e84b4b" letter-spacing="2">VERIFIED PROOF</text>
{proof_svg}
<path d="M20 301H700" stroke="#310808"/>
{stack_glyph}
<text x="58" y="324" class="mono" font-size="9" fill="#e84b4b" letter-spacing="2">STACK / LOADOUT</text>
<text x="30" y="350" class="mono" font-size="12" fill="#a99494">{stack_svg}</text>
<text x="690" y="355" text-anchor="end" class="mono" font-size="10" fill="#e84b4b">OPEN SIGNAL ↗</text>
</svg>'''


def build_project_summary_svg(project, cfg):
    """Render the visible project metadata as a themed system readout.

    GitHub's README renderer does not inherit a page-level stylesheet, so
    ordinary HTML tables become visually disconnected from the crimson atlas.
    This compact plate keeps the cover clean while making the metadata part of
    the same authored visual language.
    """
    kind = project["id"]
    world_key = "token-usage" if kind == "token-usage" else kind
    world = WORLD_TOKENS.get(world_key, WORLD_TOKENS["portfolio"])
    W, H = 720, 260
    code = f'SYS-{project["order"]:02d}'
    title_id = f"{kind}SummaryTitle"
    desc_id = f"{kind}SummaryDescription"
    summary_lines = wrap_lines(project["summary"], 86)[:3]
    summary_svg = "".join(
        f'<tspan x="90" dy="{0 if index == 0 else 17}">{esc(line)}</tspan>'
        for index, line in enumerate(summary_lines)
    )
    stack_lines = wrap_lines(" · ".join(project["stack"]).upper(), 47)[:2]
    stack_svg = "".join(
        f'<tspan x="30" dy="{0 if index == 0 else 15}">{esc(line)}</tspan>'
        for index, line in enumerate(stack_lines)
    )
    proof_lines = wrap_lines(" · ".join(project["proof"]), 43)[:3]
    proof_svg = "".join(
        f'<tspan x="390" dy="{0 if index == 0 else 15}">{esc(line)}</tspan>'
        for index, line in enumerate(proof_lines)
    )
    glyph_kind = {
        "portfolio": "product",
        "vision": "vision",
        "zenith": "target",
        "helios": "realtime",
        "token-usage": "layers",
        "talks": "realtime",
    }.get(kind, "mission")
    summary_glyph = kinetic_glyph_svg(glyph_kind, 20, 84, .58, project["order"] * .17)
    status = esc(project["status"].upper())
    period = esc(project["period"].upper())
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{title_id} {desc_id}" data-visual-layer="project-summary">
<title id="{title_id}">{esc(code)} — {esc(project["name"])}</title>
<desc id="{desc_id}">{esc(project["summary"])} Stack: {esc("; ".join(project["stack"]))}. Proof: {esc("; ".join(project["proof"]))}.</desc>
<defs>
{mono_font_defs()}
<linearGradient id="{kind}SummaryBg" x1="0%" x2="100%">
 <stop offset="0" stop-color="{world["canvas"]}"/><stop offset=".63" stop-color="{world["surface"]}"/><stop offset="1" stop-color="{world["glow"]}" stop-opacity=".55"/>
</linearGradient>
<linearGradient id="{kind}SummaryRail" x1="0%" x2="100%">
 <stop offset="0" stop-color="{world["accent"]}" stop-opacity="0"/><stop offset=".22" stop-color="{world["accent"]}" stop-opacity=".78"/><stop offset=".52" stop-color="{world["accent_soft"]}" stop-opacity=".2"/><stop offset=".82" stop-color="{world["accent"]}" stop-opacity=".78"/><stop offset="1" stop-color="{world["accent"]}" stop-opacity="0"/>
</linearGradient>
<pattern id="{kind}SummaryGrid" width="24" height="24" patternUnits="userSpaceOnUse">
 <path d="M24 0H0V24" fill="none" stroke="{world["accent_soft"]}" stroke-width=".45" opacity=".09"/>
</pattern>
<style>
 .{kind}-summary-sweep {{ animation: {kind}-summary-sweep 8s linear infinite; }}
 .{kind}-summary-pulse {{ animation: {kind}-summary-pulse 2.4s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
 @keyframes {kind}-summary-sweep {{ from {{ transform: translateX(-180px); }} to {{ transform: translateX(900px); }} }}
 @keyframes {kind}-summary-pulse {{ 0%, 100% {{ opacity: .28; transform: scale(.72); }} 50% {{ opacity: .92; transform: scale(1.18); }} }}
 @media (prefers-reduced-motion: reduce) {{ .{kind}-summary-sweep, .{kind}-summary-pulse {{ animation: none !important; }} }}
</style>
</defs>
<rect x="1" y="1" width="718" height="258" rx="8" fill="url(#{kind}SummaryBg)" stroke="{world["line"]}"/>
<rect x="1" y="1" width="718" height="258" rx="8" fill="url(#{kind}SummaryGrid)"/>
<rect class="{kind}-summary-sweep" x="-180" y="1" width="180" height="258" fill="url(#{kind}SummaryRail)" opacity=".22"/>
<rect x="1" y="1" width="6" height="258" rx="2" fill="{world["accent"]}"/>
<path d="M22 20V10H32M688 10h10v10M22 240v10h10M688 250h10v-10" fill="none" stroke="{world["accent_soft"]}" stroke-width="1" opacity=".7"/>
<text x="38" y="29" class="mono" font-size="9" fill="{world["accent"]}" letter-spacing="2.1">{esc(code)} // {esc(project["codename"].upper())}</text>
<rect x="548" y="14" width="140" height="23" rx="11.5" fill="{world["accent"]}" opacity=".14" stroke="{world["accent"]}"/>
<text x="618" y="29" text-anchor="middle" class="mono" font-size="8" fill="{world["ink"]}" letter-spacing="1.1">{status}</text>
<text x="688" y="54" text-anchor="end" class="mono" font-size="8" fill="{world["muted"]}" letter-spacing="1.1">{period}</text>
<text x="38" y="68" class="mono" font-size="22" fill="{world["ink"]}" letter-spacing=".7">{esc(project["name"].upper())}</text>
<path d="M22 80H698" stroke="{world["line"]}"/>
{summary_glyph}
<text x="90" y="101" class="mono" font-size="8" fill="{world["accent"]}" letter-spacing="1.8">MISSION / SYSTEM INTENT</text>
<text x="90" y="121" class="mono" font-size="12" fill="{world["ink"]}">{summary_svg}</text>
<path d="M22 158H698" stroke="{world["line"]}"/>
<text x="30" y="178" class="mono" font-size="8" fill="{world["accent"]}" letter-spacing="1.8">STACK / LOADOUT</text>
<text x="390" y="178" class="mono" font-size="8" fill="{world["accent"]}" letter-spacing="1.8">PROOF / SIGNAL</text>
<text x="30" y="197" class="mono" font-size="9" fill="{world["muted"]}">{stack_svg}</text>
<text x="390" y="197" class="mono" font-size="9" fill="{world["muted"]}">{proof_svg}</text>
<circle class="{kind}-summary-pulse" cx="682" cy="231" r="4" fill="{world["accent_soft"]}"/>
<path d="M30 239H350M390 239H650" stroke="url(#{kind}SummaryRail)"/>
<text x="30" y="249" class="mono" font-size="7" fill="{world["muted"]}" letter-spacing="1.1">DETAILS BELOW / DOSSIER AVAILABLE</text>
<text x="688" y="249" text-anchor="end" class="mono" font-size="7" fill="{world["accent_soft"]}" letter-spacing="1.1">OPEN SIGNAL ↗</text>
</svg>'''


def build_field_notes_svg(cfg):
    """Render verified experience and education as a two-record trajectory."""
    W, H = 720, 500
    experience = PROFILE["experience"][0]
    education = PROFILE["education"][0]
    experience_summary = wrap_lines(experience["summary"], 67)[:3]
    experience_svg = "".join(
        f'<tspan x="34" dy="{0 if index == 0 else 22}">{esc(line)}</tspan>'
        for index, line in enumerate(experience_summary)
    )
    degree_lines = wrap_lines(education["degree"], 49)[:2]
    degree_svg = "".join(
        f'<tspan x="100" dy="{0 if index == 0 else 24}">{esc(line)}</tspan>'
        for index, line in enumerate(degree_lines)
    )
    coursework = " · ".join(education["coursework"])
    coursework_lines = wrap_lines(coursework, 79)[:2]
    coursework_svg = "".join(
        f'<tspan x="34" dy="{0 if index == 0 else 18}">{esc(line)}</tspan>'
        for index, line in enumerate(coursework_lines)
    )
    experience_glyph = kinetic_glyph_svg("telecom", 22, 42, .86, .2)
    education_glyph = kinetic_glyph_svg("education", 22, 42, .86, .7)
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<title>Field notes — experience and education</title>
<desc>{esc(experience["role"])} at {esc(experience["organization"])}. {esc(education["degree"])} at {esc(education["institution"])}.</desc>
<defs>
{mono_font_defs()}
<linearGradient id="fieldBg" x1="0%" x2="100%"><stop offset="0" stop-color="#020202"/><stop offset="1" stop-color="#190303"/></linearGradient>
<pattern id="fieldGrid" width="26" height="26" patternUnits="userSpaceOnUse"><path d="M26 0H0V26" fill="none" stroke="#671515" stroke-width=".4" opacity=".09"/></pattern>
<linearGradient id="fieldSweep" gradientUnits="userSpaceOnUse" x1="-160" x2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#ff8a7f" stop-opacity=".1"/><stop offset="1" stop-color="#fff" stop-opacity="0"/><animate attributeName="x1" values="-160;720" dur="10s" repeatCount="indefinite"/><animate attributeName="x2" values="0;880" dur="10s" repeatCount="indefinite"/></linearGradient>
</defs>
<rect x="1" y="1" width="718" height="498" rx="7" fill="url(#fieldBg)" stroke="#4b0e0e"/>
<rect x="1" y="1" width="718" height="498" rx="7" fill="url(#fieldGrid)"/>
<rect x="1" y="1" width="718" height="498" rx="7" fill="url(#fieldSweep)"/>
<text x="24" y="36" class="mono" font-size="10" fill="#e84b4b" letter-spacing="2.5">VERIFIED TRAJECTORY // 02 RECORDS</text>
<text x="696" y="36" text-anchor="end" class="mono" font-size="9" fill="#8d7777">FIELD LOG / PUBLIC</text>
<g transform="translate(18,56)">
<rect width="684" height="196" rx="5" fill="#050101" stroke="#3d0b0b"/>
<rect width="6" height="196" rx="2" fill="#e84b4b"/>
<text x="22" y="31" class="mono" font-size="9" fill="#8d7777" letter-spacing="2">EXP-01 // {esc(experience["period"].upper())}</text>
{experience_glyph}
<text x="100" y="65" class="mono" font-size="22" fill="#f5eaea">{esc(experience["role"].upper())}</text>
<text x="100" y="91" class="mono" font-size="13" fill="#e84b4b">{esc(experience["organization"].upper())}</text>
<text x="100" y="119" class="mono" font-size="10" fill="#8d7777">{esc(experience["location"].upper())}</text>
<path d="M22 132H660" stroke="#310808"/>
<text x="34" y="156" class="mono" font-size="14" fill="#cfc1c1">{experience_svg}</text>
</g>
<g transform="translate(18,266)">
<rect width="684" height="214" rx="5" fill="#050101" stroke="#3d0b0b"/>
<rect width="6" height="214" rx="2" fill="#671515"/>
<text x="22" y="31" class="mono" font-size="9" fill="#8d7777" letter-spacing="2">EDU-01 // {esc(education["period"].upper())}</text>
{education_glyph}
<text x="100" y="63" class="mono" font-size="19" fill="#f5eaea">{degree_svg}</text>
<text x="100" y="116" class="mono" font-size="13" fill="#e84b4b">{esc(education["institution"].upper())}</text>
<text x="100" y="141" class="mono" font-size="10" fill="#8d7777">{esc(education["location"].upper())}</text>
<path d="M22 154H660" stroke="#310808"/>
<text x="34" y="178" class="mono" font-size="11" fill="#b7a6a6">{coursework_svg}</text>
</g>
</svg>'''


def build_skills_matrix_svg(cfg):
    """Render the complete canonical skill inventory without Markdown prose."""
    W = 720
    rows = (
        ("01", "PRODUCT", PROFILE["skills"]["product"], "product"),
        ("02", "BACKEND", PROFILE["skills"]["backend"], "backend"),
        ("03", "APPLIED ML", PROFILE["skills"]["ml"], "ml"),
        ("04", "PLATFORM", PROFILE["skills"]["platform"], "platform"),
        ("05", "EXPANDING", PROFILE["skills"]["expanding"], "expanding"),
    )
    row_height = 108
    H = 70 + len(rows) * row_height
    row_svg = []
    for index, (code, label, values, icon_kind) in enumerate(rows):
        y = 58 + index * row_height
        value_lines = wrap_lines(" · ".join(values), 56)[:3]
        values_svg = "".join(
            f'<tspan x="190" dy="{0 if line_index == 0 else 21}">{esc(line)}</tspan>'
            for line_index, line in enumerate(value_lines)
        )
        glyph = kinetic_glyph_svg(icon_kind, 18, 15, .65, index * .24)
        row_svg.append(f'''
<g transform="translate(18,{y})">
<rect width="684" height="94" rx="5" fill="#050101" stroke="#3d0b0b"/>
<rect width="5" height="94" rx="2" fill="{"#e84b4b" if index in (0, 4) else "#671515"}"/>
{glyph}
<text x="70" y="28" class="mono" font-size="9" fill="#8d7777" letter-spacing="2">LOADOUT // {code}</text>
<text x="70" y="60" class="mono" font-size="15" fill="#e84b4b" letter-spacing="1.2">{esc(label)}</text>
<path d="M168 15V79" stroke="#310808"/>
<text x="190" y="34" class="mono" font-size="13" fill="#d7caca">{values_svg}</text>
<circle cx="658" cy="20" r="4" fill="#ff8a7f"><animate attributeName="opacity" values=".2;1;.2" dur="{1.2 + index * .17:.2f}s" repeatCount="indefinite"/></circle>
</g>''')
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<title>Complete technical loadout</title>
<desc>Product, backend, applied machine learning, platform, and currently expanding skills.</desc>
<defs>
{mono_font_defs()}
<linearGradient id="skillsBg" x1="0%" x2="100%"><stop offset="0" stop-color="#020202"/><stop offset="1" stop-color="#160303"/></linearGradient>
<pattern id="skillsGrid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="#671515" stroke-width=".4" opacity=".08"/></pattern>
</defs>
<rect x="1" y="1" width="718" height="{H-2}" rx="7" fill="url(#skillsBg)" stroke="#310808"/>
<rect x="1" y="1" width="718" height="{H-2}" rx="7" fill="url(#skillsGrid)"/>
<text x="24" y="37" class="mono" font-size="10" fill="#e84b4b" letter-spacing="2.5">COMPLETE LOADOUT // TOOLS FOLLOW THE SYSTEM</text>
<text x="696" y="37" text-anchor="end" class="mono" font-size="9" fill="#8d7777">05 CHANNELS / LIVE</text>
{"".join(row_svg)}
</svg>'''


def build_identity_console_svg(cfg):
    W, H = 1500, 360
    nodes = [
        (760, 92, "GEOSPATIAL"), (985, 132, "REALTIME"),
        (930, 274, "VISION"), (680, 252, "SYSTEMS"),
    ]
    links = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2), (1, 3)]
    link_svg = []
    for i, (a, b) in enumerate(links):
        x1, y1, _ = nodes[a]
        x2, y2, _ = nodes[b]
        link_svg.append(
            f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#671515" stroke-width="1.2" '
            f'opacity=".55" stroke-dasharray="5 10">'
            f'<animate attributeName="stroke-dashoffset" values="0;-60" dur="{4+i*.7:.1f}s" '
            f'repeatCount="indefinite"/></path>'
        )
    node_svg = []
    for i, (x, y, label) in enumerate(nodes):
        node_svg.append(
            f'<g><circle cx="{x}" cy="{y}" r="28" fill="#080202" stroke="#e84b4b" '
            f'stroke-width="1"/><circle cx="{x}" cy="{y}" r="20" fill="none" '
            f'stroke="#e84b4b" opacity=".45" stroke-dasharray="3 5">'
            f'<animateTransform attributeName="transform" type="rotate" from="0 {x} {y}" '
            f'to="360 {x} {y}" dur="{8+i*2}s" repeatCount="indefinite"/></circle>'
            f'<circle cx="{x}" cy="{y}" r="4" fill="#ff8a7f">'
            f'<animate attributeName="r" values="3;6;3" dur="{1.8+i*.3}s" '
            f'repeatCount="indefinite"/></circle>'
            f'<text x="{x}" y="{y+48}" text-anchor="middle" class="mono" font-size="9" '
            f'fill="#c4c4c4" letter-spacing="1.5">{label}</text></g>'
        )

    manifest_entries = (
        ("gpu", "4,000 GPU particle interfaces."),
        ("realtime", "Real-time energy monitoring."),
        ("vision", "SVM + texture computer vision."),
        ("telecom", "BSNL telecom systems grounding."),
    )
    manifest_svg = "".join(
        f'<g>{kinetic_glyph_svg(kind, 34, 170 + index * 25, .32, index * .21)}'
        f'<text x="66" y="188" dy="{index * 25}" class="mono" font-size="13" '
        f'fill="#a99494">{esc(label)}</text></g>'
        for index, (kind, label) in enumerate(manifest_entries)
    )

    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<title>Ayush Roy operator manifest</title>
<desc>Full-stack developer and applied machine learning builder in Bhubaneswar, open to software engineering internships.</desc>
<defs>
{experience_font_defs()}
<pattern id="consoleGrid" width="28" height="28" patternUnits="userSpaceOnUse">
<path d="M28 0H0V28" fill="none" stroke="#671515" stroke-width=".5" opacity=".12"/>
</pattern>
<radialGradient id="coreGlow">
<stop offset="0" stop-color="#e84b4b" stop-opacity=".25"/>
<stop offset="1" stop-color="#e84b4b" stop-opacity="0"/>
</radialGradient>
</defs>
<rect x="1" y="1" width="1498" height="358" rx="7" fill="#030303" stroke="#2d0808"/>
<rect x="1" y="1" width="1498" height="358" rx="7" fill="url(#consoleGrid)"/>
<image href="{asset_data_uri(SUPPORTING_ART["identity"])}" x="548" y="18" width="554" height="324" preserveAspectRatio="xMidYMid slice" opacity=".22"/>
<rect x="548" y="18" width="554" height="324" rx="5" fill="#030303" opacity=".38"/>
<path d="M560 20V340M1080 20V340" stroke="#310808"/>
<text x="34" y="48" class="mono" font-size="10" fill="#e84b4b" letter-spacing="3">
OPERATOR MANIFEST
</text>
<text x="34" y="93" class="serif" font-size="35" fill="#f5eaea">I build systems where</text>
<text x="34" y="132" class="serif" font-size="35" fill="#f5eaea">software meets reality.</text>
<rect x="34" y="154" width="440" height="1" fill="#671515"/>
{manifest_svg}
<text x="34" y="319" class="mono" font-size="10" fill="#e84b4b" letter-spacing="2">
THE DOMAIN CHANGES. THE STANDARD DOESN'T.
</text>
<circle cx="835" cy="180" r="165" fill="url(#coreGlow)"/>
{"".join(link_svg)}
{"".join(node_svg)}
<g>
<circle cx="835" cy="180" r="50" fill="#050101" stroke="#e84b4b" stroke-width="1.4"/>
<circle cx="835" cy="180" r="38" fill="none" stroke="#ff8a7f" opacity=".35"
 stroke-dasharray="6 9">
<animateTransform attributeName="transform" type="rotate" from="0 835 180"
 to="-360 835 180" dur="10s" repeatCount="indefinite"/>
</circle>
<text x="835" y="176" text-anchor="middle" class="mono" font-size="11" fill="#f5eaea"
 letter-spacing="2">AYR</text>
<text x="835" y="194" text-anchor="middle" class="mono" font-size="8" fill="#e84b4b"
 letter-spacing="1">CORE</text>
</g>
<text x="1118" y="48" class="mono" font-size="10" fill="#e84b4b" letter-spacing="3">
CURRENT STATE
</text>
<text x="1118" y="93" class="mono" font-size="13" fill="#8d7777">ROLE</text>
<text x="1118" y="116" class="mono" font-size="17" fill="#f5eaea">FULL-STACK / ML</text>
<text x="1118" y="158" class="mono" font-size="13" fill="#8d7777">LOCATION</text>
<text x="1118" y="181" class="mono" font-size="17" fill="#f5eaea">BHUBANESWAR · INDIA</text>
<text x="1118" y="223" class="mono" font-size="13" fill="#8d7777">SIGNAL</text>
<text x="1118" y="246" class="mono" font-size="17" fill="#f5eaea">OPEN TO INTERNSHIPS</text>
<rect x="1118" y="274" width="310" height="42" rx="3" fill="#130303" stroke="#671515"/>
<circle cx="1140" cy="295" r="5" fill="#e84b4b">
<animate attributeName="opacity" values=".2;1;.2" dur="1.2s" repeatCount="indefinite"/>
</circle>
<text x="1156" y="300" class="mono" font-size="11" fill="#d7caca" letter-spacing="1.5">
BUILDING / LEARNING / SHIPPING
</text>
</svg>'''


def build_operator_gateway_svg(cfg):
    """A full-width `<summary>` surface for the profile's optional deep layer.

    GitHub strips JavaScript but preserves native details/summary controls and
    SMIL inside SVG images, so the entire gateway remains interactive there.
    """
    W, H = 1500, 196
    chevrons = "".join(
        f'<path d="M{x} 82l18 16-18 16" fill="none" stroke="#e84b4b" '
        f'stroke-width="2" opacity="{.22 + i * .08:.2f}">'
        f'<animate attributeName="opacity" values=".12;.9;.12" dur="2.4s" '
        f'begin="-{i * .22:.2f}s" repeatCount="indefinite"/></path>'
        for i, x in enumerate(range(1000, 1136, 34))
    )
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<linearGradient id="gatewayBg" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0" stop-color="#020202"/><stop offset=".5" stop-color="#100202"/>
<stop offset="1" stop-color="#020202"/>
</linearGradient>
<linearGradient id="gatewayRail" x1="0%" x2="100%">
<stop offset="0" stop-color="#000" stop-opacity="0"/><stop offset=".18" stop-color="#671515"/>
<stop offset=".5" stop-color="#ff8a7f"/><stop offset=".82" stop-color="#671515"/>
<stop offset="1" stop-color="#000" stop-opacity="0"/>
</linearGradient>
<linearGradient id="gatewaySweep" gradientUnits="userSpaceOnUse" x1="-260" x2="0">
<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#ff8a7f"
 stop-opacity=".2"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
<animate attributeName="x1" values="-260;1500" dur="7s" repeatCount="indefinite"/>
<animate attributeName="x2" values="0;1760" dur="7s" repeatCount="indefinite"/>
</linearGradient>
<pattern id="gatewayGrid" width="26" height="26" patternUnits="userSpaceOnUse">
<path d="M26 0H0V26" fill="none" stroke="#e84b4b" stroke-width=".45" opacity=".1"/>
</pattern>
<filter id="gatewayGlow" x="-40%" y="-80%" width="180%" height="260%">
<feGaussianBlur stdDeviation="8"/>
</filter>
</defs>
<rect x="1" y="1" width="1498" height="194" rx="7" fill="url(#gatewayBg)" stroke="#4b0e0e"/>
<rect x="1" y="1" width="1498" height="194" rx="7" fill="url(#gatewayGrid)"/>
<rect x="1" y="1" width="1498" height="194" rx="7" fill="url(#gatewaySweep)"/>
<path d="M20 22H214L238 46H1262L1286 22H1480" fill="none" stroke="#671515"/>
<path d="M20 174H214L238 150H1262L1286 174H1480" fill="none" stroke="#671515"/>
<rect x="258" y="30" width="984" height="136" rx="4" fill="#030303" opacity=".72" stroke="#310808"/>
<rect x="258" y="30" width="6" height="136" rx="3" fill="#e84b4b"/>
<rect x="258" y="30" width="984" height="1.5" fill="url(#gatewayRail)"/>
<rect x="258" y="164" width="984" height="1.5" fill="url(#gatewayRail)"/>
<text x="42" y="55" class="mono" font-size="9" fill="#8d7777" letter-spacing="2.5">LAYER // 00</text>
<text x="42" y="86" class="mono" font-size="13" fill="#e84b4b" letter-spacing="2">RESTRICTED</text>
<text x="42" y="110" class="mono" font-size="13" fill="#e84b4b" letter-spacing="2">SIGNAL</text>
<circle cx="44" cy="143" r="5" fill="#e84b4b">
<animate attributeName="opacity" values=".2;1;.2" dur="1.1s" repeatCount="indefinite"/>
</circle>
<text x="60" y="147" class="mono" font-size="9" fill="#a99494" letter-spacing="1.4">READY TO BREACH</text>
<text x="750" y="83" text-anchor="middle" class="serif" font-size="45" fill="#e84b4b"
 opacity=".38" filter="url(#gatewayGlow)">INITIATE OPERATOR MODE</text>
<text x="750" y="83" text-anchor="middle" class="serif" font-size="45" fill="#f5eaea"
 letter-spacing="2">INITIATE OPERATOR MODE</text>
<text x="750" y="116" text-anchor="middle" class="mono" font-size="11" fill="#c4b4b4"
 letter-spacing="2.4">ACTIVATE ACCESS CONTROL ABOVE · CHOOSE A PROTOCOL · DECODE THE BUILD</text>
<rect x="570" y="134" width="360" height="2" fill="#310808"/>
<rect x="570" y="134" width="86" height="2" fill="#ff8a7f">
<animate attributeName="x" values="570;844;570" dur="3.8s" repeatCount="indefinite"/>
</rect>
{chevrons}
<g transform="translate(1378,98)">
<circle r="58" fill="#050101" stroke="#671515"/>
<circle r="46" fill="none" stroke="#e84b4b" opacity=".58" stroke-dasharray="8 12">
<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="9s" repeatCount="indefinite"/>
</circle>
<circle r="32" fill="none" stroke="#ff8a7f" opacity=".38" stroke-dasharray="3 7">
<animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="5s" repeatCount="indefinite"/>
</circle>
<path d="M-9 -5L0 5 14-12" fill="none" stroke="#f5eaea" stroke-width="3" stroke-linecap="round"/>
<text y="78" text-anchor="middle" class="mono" font-size="8" fill="#e84b4b" letter-spacing="2">ENTER</text>
</g>
</svg>'''


def build_achievement_rack_svg(cfg):
    W, H = 1500, 286
    accuracy = next(item for item in PROFILE["proof"] if item["id"] == "accuracy")
    accuracy_value = accuracy["value"]
    accuracy_progress = float(accuracy_value.rstrip("%")) / 100
    achievements = [
        ("GPU", "4,000", "PARTICLES", "ONE DRAW CALL", .92),
        ("QA", "24", "TESTS", "FIVE SUITES", .84),
        ("CV", accuracy_value, "ACCURACY", "CALIBRATED", accuracy_progress),
        ("XP", "125", "STEAM LEVEL", "LONG GAME", .88),
        ("OSS", "25+", "PUBLIC REPOS", "BUILD LOG", .74),
    ]
    cards = []
    circumference = 251.3
    for i, (code, value, label, note, progress) in enumerate(achievements):
        x = 24 + i * 291
        end_offset = circumference * (1 - progress)
        cards.append(f'''
<g transform="translate({x},72)">
<rect width="276" height="188" rx="6" fill="#050101" stroke="#3d0b0b"/>
<rect width="5" height="188" rx="2" fill="#671515"/>
<circle cx="63" cy="78" r="48" fill="#0b0202" stroke="#310808"/>
<circle cx="63" cy="78" r="40" fill="none" stroke="#260606" stroke-width="5"/>
<circle cx="63" cy="78" r="40" fill="none" stroke="#e84b4b" stroke-width="5"
 stroke-linecap="round" stroke-dasharray="{circumference:.1f}" stroke-dashoffset="{circumference:.1f}"
 transform="rotate(-90 63 78)">
<animate attributeName="stroke-dashoffset" values="{circumference:.1f};{end_offset:.1f}"
 dur="{1.5 + i * .18:.2f}s" begin="{i * .12:.2f}s" fill="freeze"/>
</circle>
<circle cx="63" cy="78" r="4" fill="#ff8a7f">
<animate attributeName="opacity" values=".25;1;.25" dur="{1.3 + i * .17:.2f}s" repeatCount="indefinite"/>
</circle>
<text x="63" y="83" text-anchor="middle" class="mono" font-size="12" fill="#f5eaea" letter-spacing="1">{code}</text>
<text x="132" y="72" class="serif" font-size="37" fill="#f5eaea">{value}</text>
<text x="132" y="96" class="mono" font-size="9" fill="#e84b4b" letter-spacing="1.8">{label}</text>
<path d="M22 142H254" stroke="#310808"/>
<text x="22" y="166" class="mono" font-size="9" fill="#8d7777" letter-spacing="1.8">{note}</text>
<rect x="226" y="154" width="28" height="3" fill="#671515"/>
<rect x="226" y="154" width="9" height="3" fill="#ff8a7f">
<animate attributeName="x" values="226;245;226" dur="2.6s" begin="-{i * .31:.2f}s" repeatCount="indefinite"/>
</rect>
</g>''')
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<linearGradient id="rackBg" x1="0%" x2="100%">
<stop offset="0" stop-color="#020202"/><stop offset=".5" stop-color="#0d0202"/><stop offset="1" stop-color="#020202"/>
</linearGradient>
<pattern id="rackGrid" width="32" height="32" patternUnits="userSpaceOnUse">
<path d="M32 0H0V32" fill="none" stroke="#671515" stroke-width=".4" opacity=".08"/>
</pattern>
</defs>
<rect x="1" y="1" width="1498" height="284" rx="7" fill="url(#rackBg)" stroke="#310808"/>
<rect x="1" y="1" width="1498" height="284" rx="7" fill="url(#rackGrid)"/>
<text x="24" y="38" class="mono" font-size="11" fill="#e84b4b" letter-spacing="3">PROOF OF WORK // ACHIEVEMENTS UNLOCKED</text>
<text x="1476" y="38" text-anchor="end" class="mono" font-size="9" fill="#806d6d" letter-spacing="2">SIGNAL VERIFIED · 05 RECORDS</text>
<path d="M24 52H1476" stroke="#310808"/>
{"".join(cards)}
</svg>'''


def build_protocol_engineer_svg(cfg):
    W, H = 1500, 338
    stages = [
        ("01", "REALITY", "OBSERVE CONSTRAINTS"),
        ("02", "MODEL", "REMOVE AMBIGUITY"),
        ("03", "SYSTEM", "ENCODE BEHAVIOR"),
        ("04", "INTERFACE", "MAKE IT LEGIBLE"),
        ("05", "FEEDBACK", "CLOSE THE LOOP"),
    ]
    stage_svg = []
    for i, (code, title, subtitle) in enumerate(stages):
        x = 38 + i * 291
        stage_svg.append(f'''
<g transform="translate({x},104)">
<rect width="252" height="128" rx="5" fill="#050101" stroke="#3d0b0b"/>
<rect width="252" height="5" rx="2" fill="{"#e84b4b" if i in (0, 4) else "#671515"}"/>
<text x="18" y="35" class="mono" font-size="9" fill="#8d7777" letter-spacing="2">NODE // {code}</text>
<text x="18" y="75" class="serif" font-size="29" fill="#f5eaea">{title}</text>
<text x="18" y="102" class="mono" font-size="8" fill="#e84b4b" letter-spacing="1.3">{subtitle}</text>
<circle cx="232" cy="22" r="5" fill="#e84b4b">
<animate attributeName="opacity" values=".2;1;.2" dur="{1.2 + i * .18:.2f}s" begin="-{i * .21:.2f}s" repeatCount="indefinite"/>
</circle>
</g>''')
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<linearGradient id="traceBg" x1="0%" x2="100%"><stop offset="0" stop-color="#020202"/><stop offset="1" stop-color="#100202"/></linearGradient>
<pattern id="traceGrid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#671515" stroke-width=".45" opacity=".09"/></pattern>
<filter id="traceGlow"><feGaussianBlur stdDeviation="5"/></filter>
</defs>
<rect x="1" y="1" width="1498" height="336" rx="7" fill="url(#traceBg)" stroke="#310808"/>
<rect x="1" y="1" width="1498" height="336" rx="7" fill="url(#traceGrid)"/>
<text x="38" y="44" class="mono" font-size="10" fill="#e84b4b" letter-spacing="3">PROTOCOL 01 // TRACE</text>
<text x="38" y="78" class="serif" font-size="31" fill="#f5eaea">Architecture starts at the constraint.</text>
<text x="1462" y="48" text-anchor="end" class="mono" font-size="9" fill="#8d7777" letter-spacing="2">INPUT: REALITY // OUTPUT: LEVERAGE</text>
<path d="M164 168H1336" stroke="#671515" stroke-width="2" stroke-dasharray="8 12">
<animate attributeName="stroke-dashoffset" values="0;-80" dur="5s" repeatCount="indefinite"/>
</path>
<circle r="8" fill="#ff8a7f" filter="url(#traceGlow)" opacity=".8">
<animateMotion path="M164 168H1336" dur="5s" repeatCount="indefinite"/>
</circle>
<circle r="4" fill="#fff"><animateMotion path="M164 168H1336" dur="5s" repeatCount="indefinite"/></circle>
{"".join(stage_svg)}
<text x="38" y="307" class="mono" font-size="10" fill="#9b8585" letter-spacing="2">THE DOMAIN CHANGES · THE STANDARD DOESN'T · OBSERVABILITY IS PART OF THE PRODUCT</text>
</svg>'''


def build_protocol_product_svg(cfg):
    W, H = 1500, 360
    nodes = [
        (1035, 58, "OBSERVE"), (1222, 126, "MODEL"), (1212, 274, "BUILD"),
        (1035, 320, "MEASURE"), (846, 226, "REPEAT"),
    ]
    spokes = []
    node_svg = []
    for i, (x, y, label) in enumerate(nodes):
        spokes.append(f'<path d="M1035 190L{x} {y}" stroke="#671515" stroke-dasharray="4 9"/>')
        node_svg.append(f'''
<g>
<circle cx="{x}" cy="{y}" r="35" fill="#060101" stroke="#671515"/>
<circle cx="{x}" cy="{y}" r="27" fill="none" stroke="#e84b4b" opacity=".35" stroke-dasharray="3 6">
<animateTransform attributeName="transform" type="rotate" from="0 {x} {y}" to="360 {x} {y}" dur="{7 + i}s" repeatCount="indefinite"/>
</circle>
<text x="{x}" y="{y + 4}" text-anchor="middle" class="mono" font-size="8" fill="#f5eaea" letter-spacing="1">{label}</text>
</g>''')
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<linearGradient id="forgeBg" x1="0%" x2="100%"><stop offset="0" stop-color="#020202"/><stop offset=".6" stop-color="#080101"/><stop offset="1" stop-color="#1b0303"/></linearGradient>
<radialGradient id="forgeGlow"><stop offset="0" stop-color="#e84b4b" stop-opacity=".25"/><stop offset="1" stop-color="#e84b4b" stop-opacity="0"/></radialGradient>
<pattern id="forgeGrid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0H0V30" fill="none" stroke="#671515" stroke-width=".45" opacity=".09"/></pattern>
</defs>
<rect x="1" y="1" width="1498" height="358" rx="7" fill="url(#forgeBg)" stroke="#310808"/>
<rect x="1" y="1" width="1498" height="358" rx="7" fill="url(#forgeGrid)"/>
<text x="42" y="48" class="mono" font-size="10" fill="#e84b4b" letter-spacing="3">PROTOCOL 02 // FORGE</text>
<text x="42" y="112" class="serif" font-size="52" fill="#f5eaea">Make the difficult</text>
<text x="42" y="164" class="serif" font-size="52" fill="#f5eaea">feel inevitable.</text>
<rect x="42" y="190" width="480" height="1" fill="#671515"/>
<text x="42" y="226" class="mono" font-size="11" fill="#a99494" letter-spacing="1.2">
<tspan x="42" dy="0">SCOPE HARD · SHIP SMALL · MEASURE HONESTLY</tspan>
<tspan x="42" dy="25">KEEP THE INTERFACE SIMPLE AND THE SYSTEM EXPLICIT</tspan>
<tspan x="42" dy="25">EARN COMPLEXITY ONLY WHEN REALITY DEMANDS IT</tspan>
</text>
<text x="42" y="328" class="mono" font-size="9" fill="#e84b4b" letter-spacing="2">PRODUCT DOCTRINE // BUILD → LEARN → COMPOUND</text>
<circle cx="1035" cy="190" r="178" fill="url(#forgeGlow)"/>
<circle cx="1035" cy="190" r="132" fill="none" stroke="#671515" stroke-dasharray="9 14">
<animateTransform attributeName="transform" type="rotate" from="0 1035 190" to="360 1035 190" dur="24s" repeatCount="indefinite"/>
</circle>
<circle cx="1035" cy="190" r="92" fill="none" stroke="#e84b4b" opacity=".3" stroke-dasharray="3 10">
<animateTransform attributeName="transform" type="rotate" from="360 1035 190" to="0 1035 190" dur="14s" repeatCount="indefinite"/>
</circle>
{"".join(spokes)}
{"".join(node_svg)}
<circle cx="1035" cy="190" r="66" fill="#050101" stroke="#e84b4b"/>
<circle cx="1035" cy="190" r="50" fill="none" stroke="#ff8a7f" opacity=".42" stroke-dasharray="5 8">
<animateTransform attributeName="transform" type="rotate" from="0 1035 190" to="-360 1035 190" dur="8s" repeatCount="indefinite"/>
</circle>
<text x="1035" y="185" text-anchor="middle" class="mono" font-size="11" fill="#f5eaea" letter-spacing="2">SHIP</text>
<text x="1035" y="205" text-anchor="middle" class="mono" font-size="9" fill="#e84b4b" letter-spacing="1">LEARN</text>
<text x="1452" y="334" text-anchor="end" class="mono" font-size="8" fill="#806d6d" letter-spacing="2">SYSTEM LOOP // CONTINUOUS</text>
</svg>'''


def build_protocol_human_svg(cfg):
    W, H = 1500, 350
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<linearGradient id="archiveBg" x1="0%" x2="100%"><stop offset="0" stop-color="#030303"/><stop offset=".55" stop-color="#100202"/><stop offset="1" stop-color="#030303"/></linearGradient>
<radialGradient id="levelGlow"><stop offset="0" stop-color="#e84b4b" stop-opacity=".32"/><stop offset="1" stop-color="#e84b4b" stop-opacity="0"/></radialGradient>
<pattern id="archiveGrid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="#671515" stroke-width=".45" opacity=".09"/></pattern>
<linearGradient id="archiveScan" gradientUnits="userSpaceOnUse" x1="-180" x2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#ff8a7f" stop-opacity=".12"/><stop offset="1" stop-color="#fff" stop-opacity="0"/><animate attributeName="x1" values="-180;1500" dur="10s" repeatCount="indefinite"/><animate attributeName="x2" values="0;1680" dur="10s" repeatCount="indefinite"/></linearGradient>
</defs>
<rect x="1" y="1" width="1498" height="348" rx="7" fill="url(#archiveBg)" stroke="#310808"/>
<rect x="1" y="1" width="1498" height="348" rx="7" fill="url(#archiveGrid)"/>
<rect x="1" y="1" width="1498" height="348" rx="7" fill="url(#archiveScan)"/>
<text x="36" y="42" class="mono" font-size="10" fill="#e84b4b" letter-spacing="3">PROTOCOL 03 // ARCHIVE</text>
<text x="1464" y="42" text-anchor="end" class="mono" font-size="9" fill="#8d7777" letter-spacing="2">STEAM DNA · HUMAN SIGNAL</text>
<circle cx="190" cy="185" r="148" fill="url(#levelGlow)"/>
<circle cx="190" cy="185" r="108" fill="#050101" stroke="#671515" stroke-width="2"/>
<circle cx="190" cy="185" r="90" fill="none" stroke="#e84b4b" stroke-width="2" stroke-dasharray="11 15">
<animateTransform attributeName="transform" type="rotate" from="0 190 185" to="360 190 185" dur="18s" repeatCount="indefinite"/>
</circle>
<circle cx="190" cy="185" r="74" fill="none" stroke="#ff8a7f" opacity=".45" stroke-dasharray="3 8">
<animateTransform attributeName="transform" type="rotate" from="360 190 185" to="0 190 185" dur="10s" repeatCount="indefinite"/>
</circle>
<text x="190" y="151" text-anchor="middle" class="mono" font-size="10" fill="#8d7777" letter-spacing="2">STEAM LEVEL</text>
<text x="190" y="211" text-anchor="middle" class="serif" font-size="70" fill="#f5eaea">125</text>
<text x="190" y="236" text-anchor="middle" class="mono" font-size="8" fill="#e84b4b" letter-spacing="2">THE LONG GAME</text>
<path d="M382 70V304" stroke="#310808"/>
<text x="426" y="126" class="serif" font-size="54" fill="#f5eaea" letter-spacing="2">GRIND. BUILD. REPEAT.</text>
<text x="426" y="163" class="mono" font-size="12" fill="#e84b4b" letter-spacing="3">NO NOISE · NO SHORTCUTS · STAY CURIOUS</text>
<rect x="426" y="188" width="620" height="1" fill="#671515"/>
<g class="mono" font-size="10" letter-spacing="1.4">
<rect x="426" y="218" width="190" height="54" rx="4" fill="#080202" stroke="#3d0b0b"/>
<text x="448" y="240" fill="#8d7777">SIGNAL // 01</text><text x="448" y="259" fill="#f5eaea">DIGITAL WORLDS</text>
<rect x="630" y="218" width="190" height="54" rx="4" fill="#080202" stroke="#3d0b0b"/>
<text x="652" y="240" fill="#8d7777">SIGNAL // 02</text><text x="652" y="259" fill="#f5eaea">HARD PROBLEMS</text>
<rect x="834" y="218" width="190" height="54" rx="4" fill="#080202" stroke="#3d0b0b"/>
<text x="856" y="240" fill="#8d7777">SIGNAL // 03</text><text x="856" y="259" fill="#f5eaea">OBSESSIVE CRAFT</text>
</g>
<g transform="translate(1120,82)">
<rect width="326" height="220" rx="6" fill="#050101" stroke="#671515"/>
<rect width="326" height="48" rx="6" fill="#671515"/>
<rect y="42" width="326" height="6" fill="#671515"/>
<circle cx="24" cy="24" r="5" fill="#ff8a7f"><animate attributeName="opacity" values=".2;1;.2" dur="1.3s" repeatCount="indefinite"/></circle>
<text x="42" y="29" class="mono" font-size="10" fill="#fff" letter-spacing="2">OPERATOR PROFILE</text>
<text x="24" y="84" class="mono" font-size="9" fill="#8d7777" letter-spacing="2">STATUS</text>
<text x="24" y="111" class="mono" font-size="17" fill="#f5eaea">ONLINE / BUILDING</text>
<text x="24" y="145" class="mono" font-size="9" fill="#8d7777" letter-spacing="2">PHILOSOPHY</text>
<text x="24" y="172" class="mono" font-size="13" fill="#f5eaea">PLAY THE LONG GAME.</text>
<rect x="24" y="190" width="278" height="1" fill="#310808"/>
<text x="24" y="211" class="mono" font-size="9" fill="#e84b4b" letter-spacing="1.8">OPEN STEAM PROFILE ↗</text>
</g>
</svg>'''


def sculpture_svg():
    """A deterministic folded light ribbon, drawn as a depth-sorted wire mesh."""
    strands = []
    for band in range(13):
        v = -1 + band / 6
        coords = []
        depth = 0
        for step in range(81):
            u = step / 80 * math.tau
            radius = 195 + v * 68 * math.cos(u / 2)
            x, y, z = radius * math.cos(u), radius * math.sin(u), v * 68 * math.sin(u / 2)
            xx = x * .92 + z * .39
            zz = -x * .39 + z * .92
            yy = y * .54 - zz * .84
            depth += y * .84 + zz * .54
            coords.append(f"{xx:.1f},{yy:.1f}")
        light = abs(v)
        color = "#ffe5de" if band in (0, 12) else ("#ff8a7f" if band % 3 == 0 else "#b73d48")
        strands.append((depth, f'<polyline points="{" ".join(coords)}" fill="none" stroke="{color}" '
                        f'stroke-width="{1.8 if band in (0, 12) else .85}" opacity="{.35 + light * .5:.2f}"/>'))
    ribs = []
    for step in range(0, 80, 4):
        u = step / 80 * math.tau
        coords = []
        for band in range(13):
            v = -1 + band / 6
            radius = 195 + v * 68 * math.cos(u / 2)
            x, y, z = radius * math.cos(u), radius * math.sin(u), v * 68 * math.sin(u / 2)
            coords.append(f"{x * .92 + z * .39:.1f},{y * .54 - (-x * .39 + z * .92) * .84:.1f}")
        ribs.append(f'<polyline points="{" ".join(coords)}" fill="none" stroke="#ff8a7f" stroke-width=".6" opacity=".3"/>')
    return "".join(svg for _, svg in sorted(strands)) + "".join(ribs)


def build_featured_project_svg(cfg, mobile=False):
    """Render the flagship artwork as a clean cover; HTML owns all details."""
    W, H = (720, 400) if mobile else (1500, 520)
    project = next(item for item in PROFILE["projects"] if item["id"] == "portfolio")
    cx, cy, scale = (360, 200, .72) if mobile else (1085, 252, 1.1)
    art_left = 0
    art_top = 0
    art_width = W
    art_height = H
    left = 24 if mobile else 64
    right = W - left
    orbit_width = 210 if mobile else 330
    orbit_height = 48 if mobile else 76
    proof_copy = " ".join(project["proof"])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
<title id="title">The product universe — {esc(project["name"])}</title>
<desc id="desc">Clean illustrative artwork for {esc(project["name"])}. {esc(project["summary"])} {esc(proof_copy)}</desc>
<defs>
<radialGradient id="ambient"><stop stop-color="#7b1528" stop-opacity=".48"/><stop offset="1" stop-color="#080508" stop-opacity="0"/></radialGradient>
<linearGradient id="edge"><stop stop-color="#ff8a7f"/><stop offset=".4" stop-color="#57222c"/><stop offset="1" stop-color="#190c11"/></linearGradient>
<pattern id="dust" width="38" height="38" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".6" fill="#ad5865" opacity=".15"/></pattern>
<linearGradient id="coverScrim" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#020202" stop-opacity=".56"/><stop offset=".48" stop-color="#020202" stop-opacity=".08"/><stop offset="1" stop-color="#020202" stop-opacity=".28"/></linearGradient>
<clipPath id="coverClip"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="10"/></clipPath>
<style>
.orbit-trace {{animation:trace 18s linear infinite;stroke-dasharray:18 520}}
.cover-sweep {{animation:cover-sweep 8s linear infinite;stroke-dasharray:22 700}}
.cover-pulse {{animation:cover-pulse 2.8s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}
@keyframes trace {{to{{stroke-dashoffset:-1076}}}}
@keyframes cover-sweep {{from{{stroke-dashoffset:760;opacity:.08}}45%{{opacity:.72}}to{{stroke-dashoffset:0;opacity:.08}}}}
@keyframes cover-pulse {{0%,100%{{opacity:.25;transform:scale(.82)}}50%{{opacity:.9;transform:scale(1.16)}}}}
@media (prefers-reduced-motion:reduce) {{.orbit-trace,.cover-sweep,.cover-pulse{{animation:none}}}}
</style>
</defs>
<g clip-path="url(#coverClip)">
<rect width="{W}" height="{H}" fill="#060507"/>
<image href="{asset_data_uri(FLAGSHIP_ART)}" x="{art_left}" y="{art_top}" width="{art_width}" height="{art_height}" preserveAspectRatio="xMidYMid slice"/>
<rect width="{W}" height="{H}" fill="url(#dust)" opacity=".32"/>
<ellipse cx="{cx}" cy="{cy}" rx="{345 * scale}" ry="{250 * scale}" fill="url(#ambient)"/>
<rect width="{W}" height="{H}" fill="url(#coverScrim)"/>
<g transform="translate({cx} {cy}) scale({scale})">
<ellipse cy="132" rx="{orbit_width}" ry="{orbit_height}" fill="none" stroke="#471822" opacity=".75"/>
<ellipse cy="132" rx="{orbit_width}" ry="{orbit_height}" fill="none" stroke="#e84b4b" stroke-width="1.4" class="orbit-trace"/>
<ellipse cy="132" rx="{orbit_width * .72}" ry="{orbit_height * .45}" fill="none" stroke="#ff8a7f" stroke-width=".8" stroke-dasharray="2 14" opacity=".52"/>
<path d="M-285 0h14M271 0h14M0 -206v14M0 192v14" stroke="#a55e6b" opacity=".55"/>
</g>
<g aria-hidden="true">
<path d="M{left} 18H{right}V{H - 18}H{left}Z" fill="none" stroke="#ff1f2d" stroke-width="1.2" stroke-dasharray="20 740" class="cover-sweep" opacity=".42"/>
<path d="M{left} 18h58M{left} 18v44M{right} 18h-58M{right} 18v44M{left} {H - 18}h58M{left} {H - 18}v-44M{right} {H - 18}h-58M{right} {H - 18}v-44" fill="none" stroke="#ff6670" stroke-width="1" opacity=".58"/>
<circle cx="{right - 28}" cy="{H - 34}" r="4" fill="#ff1f2d" class="cover-pulse"/>
<path d="M{left + 12} {H - 38}H{right - 52}" stroke="#8f0014" stroke-width="2" stroke-dasharray="3 16" class="cover-sweep" opacity=".82"/>
</g>
</g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="10" fill="none" stroke="#52212b"/>
</svg>'''


def build_jump_button_svg(label, index):
    """A compact, image-backed section link, with readable mobile typography."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="88" viewBox="0 0 320 88">
<title>Jump to {esc(label.lower())}</title>
<defs>{mono_font_defs()}
<linearGradient id="edge"><stop stop-color="#e84b4b"/><stop offset="1" stop-color="#321018"/></linearGradient>
<style>
.trace{{animation:sweep 7s ease-in-out infinite;animation-delay:-{index * 1.7}s}}
@keyframes sweep{{0%,100%{{opacity:.2}}50%{{opacity:.85}}}}
@media(prefers-reduced-motion:reduce){{.trace{{animation:none}}}}
</style>
</defs>
<rect x="1" y="1" width="318" height="86" rx="7" fill="#0b070a" stroke="#602330"/>
<path d="M16 1H304" stroke="url(#edge)" stroke-width="2" class="trace"/>
<path d="M22 32h18v22H22zM28 27h18v22" fill="none" stroke="#e84b4b" stroke-width="1.6"/>
<text x="60" y="51" class="mono" font-size="23" fill="#f5eaea">{esc(label)}</text>
<path d="M282 38l7 6-7 6" fill="none" stroke="#ff8a7f" stroke-width="1.6"/>
</svg>'''


def build_dossier_toggle_svg():
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="440" height="88" viewBox="0 0 440 88">
<title>Expand or collapse the project dossier</title>
<desc>Mission, supporting evidence, and technology stack. Activate this disclosure to read more.</desc>
<defs>{mono_font_defs()}</defs>
<rect x="1" y="1" width="438" height="86" rx="7" fill="#10090d" stroke="#6a2936"/>
<path d="M25 34l10 10-10 10M41 34l10 10-10 10" fill="none" stroke="#ff8a7f" stroke-width="2.5"/>
<text x="72" y="53" class="mono" font-size="25" fill="#f5eaea">OPEN DOSSIER</text>
<path d="M389 34v20M379 44h20" stroke="#ff8a7f" stroke-width="2.5"/>
</svg>'''


def project_motion_style(kind):
    """Return meaningful, stoppable motion for one visual world."""
    if kind == "helios":
        animation = f'''
.{kind}-trace {{ animation: {kind}-trace 5.5s ease-in-out infinite; }}
.{kind}-pulse {{ animation: {kind}-pulse 1.8s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
.{kind}-packet {{ animation: {kind}-packet 2.8s linear infinite; }}
.{kind}-energy-arc {{ animation: {kind}-energy-arc 6s linear infinite; }}
.{kind}-energy-core {{ animation: {kind}-energy-core 2.2s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
@keyframes {kind}-trace {{ 0%, 12% {{ stroke-dashoffset: 440; }} 64%, 100% {{ stroke-dashoffset: 0; }} }}
@keyframes {kind}-pulse {{ 0%, 100% {{ opacity: .35; transform: scale(.82); }} 50% {{ opacity: 1; transform: scale(1.18); }} }}
@keyframes {kind}-packet {{ to {{ stroke-dashoffset: -80; }} }}'''
    elif kind == "zenith":
        animation = f'''
.{kind}-sun {{ animation: {kind}-sun 6s ease-in-out infinite; }}
.{kind}-panels {{ animation: {kind}-panels 3.2s ease-in-out infinite; }}
.{kind}-flow {{ animation: {kind}-flow 3.4s linear infinite; }}
.{kind}-ray {{ animation: {kind}-ray 5s ease-in-out infinite; transform-box: fill-box; transform-origin: 590px 86px; }}
@keyframes {kind}-sun {{ 0%, 100% {{ opacity: .22; transform: translateX(-14px); }} 50% {{ opacity: .9; transform: translateX(20px); }} }}
@keyframes {kind}-panels {{ 0%, 100% {{ opacity: .48; }} 50% {{ opacity: 1; }} }}
@keyframes {kind}-flow {{ to {{ stroke-dashoffset: -70; }} }}
@keyframes {kind}-ray {{ 0%, 100% {{ opacity: .18; transform: scaleY(.76); }} 50% {{ opacity: .82; transform: scaleY(1.05); }} }}'''
    elif kind == "vision":
        animation = f'''
.{kind}-scan {{ animation: {kind}-scan 4.4s ease-in-out infinite; }}
.{kind}-confidence {{ animation: {kind}-confidence 3.6s ease-in-out infinite; transform-box: fill-box; transform-origin: left center; }}
.{kind}-reticle {{ animation: {kind}-reticle 8s linear infinite; transform-box: fill-box; transform-origin: center; }}
@keyframes {kind}-scan {{ 0%, 12% {{ transform: translateY(-52px); opacity: .12; }} 55%, 78% {{ transform: translateY(126px); opacity: .9; }} 100% {{ transform: translateY(126px); opacity: .12; }} }}
@keyframes {kind}-confidence {{ 0%, 100% {{ transform: scaleX(.66); opacity: .5; }} 52% {{ transform: scaleX(1); opacity: 1; }} }}
@keyframes {kind}-reticle {{ from {{ transform: rotate(0deg); opacity: .35; }} 50% {{ opacity: .82; }} to {{ transform: rotate(360deg); opacity: .35; }} }}'''
    elif kind == "token-usage":
        animation = f'''
.{kind}-signal {{ animation: {kind}-signal 3.8s linear infinite; }}
.{kind}-core {{ animation: {kind}-core 2.6s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
.{kind}-packet {{ animation: {kind}-packet 2.4s linear infinite; }}
.{kind}-lane {{ animation: {kind}-lane 3.2s linear infinite; }}
.{kind}-prism {{ animation: {kind}-prism 2.6s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
@keyframes {kind}-signal {{ to {{ stroke-dashoffset: -96; }} }}
@keyframes {kind}-core {{ 0%, 100% {{ opacity: .45; transform: scale(.88); }} 50% {{ opacity: 1; transform: scale(1.12); }} }}
@keyframes {kind}-packet {{ to {{ stroke-dashoffset: -84; }} }}
@keyframes {kind}-lane {{ to {{ stroke-dashoffset: -120; }} }}
@keyframes {kind}-prism {{ 0%, 100% {{ opacity: .35; transform: scale(.92); }} 50% {{ opacity: .9; transform: scale(1.06); }} }}'''
    else:
        animation = f'''
.{kind}-packet {{ animation: {kind}-packet 3.1s linear infinite; }}
.{kind}-typing {{ animation: {kind}-typing 1.2s ease-in-out infinite; }}
.{kind}-network-trace {{ animation: {kind}-network-trace 6s linear infinite; }}
.{kind}-network-pulse {{ animation: {kind}-network-pulse 2.4s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
@keyframes {kind}-packet {{ to {{ stroke-dashoffset: -90; }} }}
@keyframes {kind}-typing {{ 0%, 100% {{ opacity: .25; }} 50% {{ opacity: 1; }} }}
@keyframes {kind}-network-trace {{ to {{ stroke-dashoffset: -160; }} }}
@keyframes {kind}-network-pulse {{ 0%, 100% {{ opacity: .28; transform: scale(.78); }} 50% {{ opacity: .9; transform: scale(1.22); }} }}'''
    animation = f'''
.{kind}-frame-sweep {{ animation: {kind}-frame-sweep 7.5s linear infinite; }}
.{kind}-ambient-orbit {{ animation: {kind}-ambient-orbit 12s linear infinite; transform-box: fill-box; transform-origin: center; }}
.{kind}-ambient-pulse {{ animation: {kind}-ambient-pulse 2.8s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
@keyframes {kind}-frame-sweep {{ from {{ stroke-dashoffset: 760; opacity: .08; }} 45% {{ opacity: .72; }} to {{ stroke-dashoffset: 0; opacity: .08; }} }}
@keyframes {kind}-ambient-orbit {{ from {{ transform: rotate(0deg); opacity: .24; }} 50% {{ opacity: .62; }} to {{ transform: rotate(360deg); opacity: .24; }} }}
@keyframes {kind}-ambient-pulse {{ 0%, 100% {{ opacity: .24; transform: scale(.8); }} 50% {{ opacity: .9; transform: scale(1.2); }} }}
''' + animation
    return f'''<style>
{animation}
@media (prefers-reduced-motion: reduce) {{
  .{kind}-motion, .{kind}-motion * {{ animation: none !important; }}
}}
</style>'''


def _vision_texture_cells(x, y, cols=12, rows=10, size=10):
    cells = []
    for row in range(rows):
        for col in range(cols):
            level = (math.sin(col * .83 + row * .47) + math.cos(row * .61 - col * .29) + 2) / 4
            shade = int(40 + level * 170)
            color = f"#{shade:02x}{max(0, shade - 4):02x}{max(0, shade - 5):02x}"
            cells.append(
                f'<rect x="{x + col * size:.1f}" y="{y + row * size:.1f}" width="{size - .8:.1f}" '
                f'height="{size - .8:.1f}" fill="{color}"/>'
            )
    return "".join(cells)


def _vision_lbp(cx, cy, accent, accent_soft, surface_alt):
    marks = []
    for index in range(8):
        angle = index * math.tau / 8 - math.pi / 2
        outer_x = cx + math.cos(angle) * 45
        outer_y = cy + math.sin(angle) * 45
        marks.append(
            f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{outer_x:.1f}" y2="{outer_y:.1f}" '
            f'stroke="{accent_soft}" stroke-width="1"/><circle cx="{outer_x:.1f}" cy="{outer_y:.1f}" r="4" '
            f'fill="{accent if index in (1, 3, 6) else surface_alt}"/>'
        )
    return "".join(marks)


def _glcm_matrix(x, y, accent):
    cells = []
    values = ((1, 2, 4, 2, 1), (2, 5, 8, 4, 2), (1, 3, 7, 5, 1), (1, 2, 4, 6, 2), (0, 1, 2, 2, 3))
    for row, values_row in enumerate(values):
        for col, value in enumerate(values_row):
            opacity = .18 + value / 12
            cells.append(
                f'<rect x="{x + col * 14}" y="{y + row * 14}" width="12" height="12" '
                f'fill="{accent}" opacity="{opacity:.2f}"/>'
            )
    return "".join(cells)


def clean_project_overlay_svg(kind, world):
    """Add a restrained signature overlay so each clean cover has its own motion grammar."""
    accent = world["accent"]
    soft = world["accent_soft"]
    if kind == "helios":
        return f'''<g aria-hidden="true" opacity=".78">
<path d="M70 292 C170 224 236 270 318 204 S472 126 644 76" fill="none" stroke="{soft}" stroke-width="1.3" stroke-dasharray="12 22" class="{kind}-energy-arc"/>
<path d="M84 316 C190 250 262 302 350 226 S492 158 656 112" fill="none" stroke="{accent}" stroke-width=".7" stroke-dasharray="2 18" class="{kind}-energy-arc"/>
<circle cx="644" cy="76" r="10" fill="none" stroke="{accent}" opacity=".35"/><circle cx="644" cy="76" r="4" fill="{accent}" class="{kind}-energy-core"/>
</g>'''
    if kind == "zenith":
        rays = "".join(
            f'<path d="M590 86 L{x} {y}" stroke="{soft}" stroke-width=".9" stroke-dasharray="3 14" class="{kind}-ray"/>'
            for x, y in ((414, 318), (482, 342), (562, 348), (644, 326), (692, 286))
        )
        return f'''<g aria-hidden="true" opacity=".72">
<circle cx="590" cy="86" r="34" fill="none" stroke="{accent}" stroke-width="1" stroke-dasharray="2 10" class="{kind}-ray"/>
{rays}<path d="M414 318H692M446 296H670" stroke="{soft}" stroke-width=".6" opacity=".44"/>
</g>'''
    if kind == "vision":
        return f'''<g aria-hidden="true" opacity=".78">
<g class="{kind}-reticle"><circle cx="552" cy="168" r="47" fill="none" stroke="{soft}" stroke-width=".8" stroke-dasharray="2 9"/><circle cx="552" cy="168" r="28" fill="none" stroke="{accent}" stroke-width="1"/><path d="M552 112V224M496 168H608" stroke="{soft}" stroke-width=".6"/></g>
<path d="M330 120H676" stroke="{accent}" stroke-width="1.2" stroke-dasharray="6 18" class="{kind}-scan"/>
<path d="M410 276H650" stroke="{soft}" stroke-width=".7" stroke-dasharray="2 12"/>
</g>'''
    if kind == "token-usage":
        streams = "".join(
            f'<path d="M72 {y} C190 {y-30} 302 {y+26} 548 180" fill="none" stroke="{accent if index % 2 else soft}" stroke-width="{1.1 if index == 2 else .7}" stroke-dasharray="7 18" class="{kind}-lane"/>'
            for index, y in enumerate((92, 144, 204, 264, 312))
        )
        return f'''<g aria-hidden="true" opacity=".74">
{streams}<polygon points="548,154 575,169 575,199 548,214 521,199 521,169" fill="none" stroke="{accent}" stroke-width="1.2" class="{kind}-prism"/>
<circle cx="548" cy="184" r="8" fill="{accent}" opacity=".24" class="{kind}-prism"/><circle cx="548" cy="184" r="2.5" fill="{soft}"/>
</g>'''
    return f'''<g aria-hidden="true" opacity=".78">
<path d="M88 286 C174 246 238 150 344 188 S472 292 552 206 S612 126 680 96" fill="none" stroke="{soft}" stroke-width="1" stroke-dasharray="4 16" class="{kind}-network-trace"/>
<path d="M110 112 L264 264 L424 112 L612 292 M194 322 L360 168 L590 318" fill="none" stroke="{accent}" stroke-width=".65" stroke-dasharray="2 12" class="{kind}-network-trace"/>
<g fill="{accent}"><circle cx="110" cy="112" r="4" class="{kind}-network-pulse"/><circle cx="264" cy="264" r="3.5" class="{kind}-network-pulse"/><circle cx="424" cy="112" r="3.5" class="{kind}-network-pulse"/><circle cx="612" cy="292" r="4" class="{kind}-network-pulse"/></g>
</g>'''


def project_visual_svg(kind, cfg):
    world_key = "token-usage" if kind == "token-usage" else kind
    world = WORLD_TOKENS[world_key]
    art = asset_data_uri(
        VISUAL_CONTRACT["project_art"].get(kind, VISUAL_CONTRACT["project_art"]["talks"])
    )
    accent = world["accent"]
    accent_soft = world["accent_soft"]
    canvas = world["canvas"]
    surface = world["surface"]
    surface_alt = world["surface_alt"]
    ink = world["ink"]
    muted = world["muted"]
    line = world["line"]

    if kind == "helios":
        return f'''<g class="helios-motion">
<image href="{art}" x="28" y="86" width="664" height="290" preserveAspectRatio="xMidYMid slice" opacity=".86"/>
<rect x="28" y="86" width="664" height="290" fill="{canvas}" opacity=".22"/>
<rect x="28" y="90" width="274" height="286" rx="6" fill="{surface}" opacity=".68" stroke="{line}"/>
<text x="44" y="112" class="mono" font-size="9" fill="{accent}" letter-spacing="1.7">OPERATOR SURFACE / SYNTHETIC DEMO</text>
<rect x="44" y="127" width="242" height="61" rx="4" fill="{surface_alt}" stroke="{line}"/>
<text x="58" y="148" class="mono" font-size="12" fill="{ink}" letter-spacing="1">METER M-104</text>
<text x="58" y="172" class="mono" font-size="10" fill="{muted}">ZONE E  ·  SCORE <tspan fill="{accent}">0.82</tspan></text>
<text x="269" y="148" text-anchor="end" class="mono" font-size="8" fill="{accent_soft}" letter-spacing="1">DEMO</text>
<text x="44" y="211" class="mono" font-size="9" fill="{muted}" letter-spacing="1.5">RESPONSE PATH</text>
<path d="M52 229H278" stroke="{line}"/>
<g fill="{surface_alt}" stroke="{accent}" stroke-width="1">
 <circle cx="62" cy="229" r="5"/><circle cx="134" cy="229" r="5"/><circle cx="206" cy="229" r="5"/><circle cx="278" cy="229" r="5"/>
</g>
<path d="M67 229H129M139 229H201M211 229H273" stroke="{accent}" stroke-width="2" stroke-dasharray="4 7" class="helios-packet"/>
<g class="mono" font-size="8" fill="{muted}">
 <text x="62" y="249" text-anchor="middle">OPEN</text><text x="134" y="249" text-anchor="middle">ASSIGN</text><text x="206" y="249" text-anchor="middle">VERIFY</text><text x="278" y="249" text-anchor="middle">CLOSE</text>
</g>
<text x="44" y="286" class="mono" font-size="9" fill="{muted}" letter-spacing="1.5">EVENT CLASSES</text>
<g class="mono" font-size="10">
 <rect x="44" y="299" width="70" height="25" rx="12" fill="{accent}" opacity=".16"/><text x="79" y="316" text-anchor="middle" fill="{accent}">ANOMALY</text>
 <rect x="121" y="299" width="72" height="25" rx="12" fill="{accent_soft}" opacity=".13"/><text x="157" y="316" text-anchor="middle" fill="{accent_soft}">THRESHOLD</text>
 <rect x="200" y="299" width="86" height="25" rx="12" fill="{line}" opacity=".5"/><text x="243" y="316" text-anchor="middle" fill="{muted}">WEBSOCKET</text>
</g>
<rect x="336" y="101" width="340" height="275" rx="6" fill="{surface}" opacity=".48" stroke="{line}"/>
<text x="354" y="123" class="mono" font-size="10" fill="{ink}" letter-spacing="1.5">EVENT TOPOLOGY</text>
<text x="658" y="123" text-anchor="end" class="mono" font-size="8" fill="{accent}" letter-spacing="1">ALERT ROUTING</text>
<path d="M354 142H658M354 187H658M354 232H658" stroke="{line}" opacity=".65"/>
<path d="M354 210 L390 194 L426 201 L462 168 L498 182 L534 151 L570 162 L606 139 L646 150" fill="none" stroke="{accent}" stroke-width="2" stroke-linecap="round" stroke-dasharray="440" stroke-dashoffset="440" class="helios-trace"/>
<circle cx="606" cy="139" r="5" fill="{accent}" class="helios-pulse"/>
<text x="354" y="259" class="mono" font-size="8" fill="{muted}" letter-spacing="1.3">STREAM / CHANNEL-SPECIFIC EVENTS</text>
<g stroke="{accent_soft}" stroke-width="1.2" fill="{surface_alt}">
 <path d="M382 288L436 272L492 296L550 270L616 294" fill="none" opacity=".8"/>
 <circle cx="382" cy="288" r="7"/><circle cx="436" cy="272" r="7"/><circle cx="492" cy="296" r="7"/><circle cx="550" cy="270" r="7"/><circle cx="616" cy="294" r="7"/>
</g>
<text x="382" y="291" text-anchor="middle" class="mono" font-size="7" fill="{ink}">M</text><text x="436" y="275" text-anchor="middle" class="mono" font-size="7" fill="{ink}">A</text><text x="492" y="299" text-anchor="middle" class="mono" font-size="7" fill="{ink}">Z</text><text x="550" y="273" text-anchor="middle" class="mono" font-size="7" fill="{ink}">O</text><text x="616" y="297" text-anchor="middle" class="mono" font-size="7" fill="{ink}">R</text>
<text x="354" y="347" class="mono" font-size="9" fill="{accent}" letter-spacing="1.3">FASTAPI  ·  DOCKER  ·  WEBSOCKET  ·  ALERT ENGINE</text>
</g>'''

    if kind == "zenith":
        panel_cells = []
        for row in range(2):
            for col in range(4):
                x = 58 + col * 29 + row * 4
                y = 217 + row * 23
                panel_cells.append(f'<rect x="{x}" y="{y}" width="24" height="18" rx="2" fill="{accent_soft}" opacity=".82"/>')
        return f'''<g class="zenith-motion">
<rect x="28" y="86" width="664" height="290" rx="6" fill="{surface}" stroke="{line}"/>
<image href="{art}" x="28" y="86" width="664" height="290" preserveAspectRatio="xMidYMid slice" opacity=".94"/>
<rect x="28" y="86" width="664" height="290" fill="{surface}" opacity=".10"/>
<path d="M58 128 Q150 76 244 126" fill="none" stroke="{world["glow"]}" stroke-width="2" opacity=".45" class="zenith-sun"/>
<circle cx="58" cy="128" r="7" fill="{world["glow"]}" opacity=".65" class="zenith-sun"/>
<rect x="44" y="102" width="240" height="83" rx="5" fill="{surface}" opacity=".86" stroke="{line}"/>
<text x="58" y="123" class="mono" font-size="9" fill="{accent}" letter-spacing="1.6">DAYLIGHT FEASIBILITY</text>
<text x="58" y="148" class="mono" font-size="15" fill="{ink}" letter-spacing=".8">3D ROOF PLANNING</text>
<text x="58" y="169" class="mono" font-size="9" fill="{muted}">ARCHITECTURE → PV → DECISION</text>
<g class="zenith-panels" stroke="{accent}" stroke-width="1">
 <path d="M48 255L164 198L286 230L172 293Z" fill="{surface_alt}" opacity=".94"/>
 {"".join(panel_cells)}
 <path d="M48 255L172 293L286 230" fill="none" stroke="{accent}" opacity=".7"/>
</g>
<text x="58" y="318" class="mono" font-size="8" fill="{muted}" letter-spacing="1.3">ROOF PLANE / SAMPLE PLACEMENT GRID</text>
<rect x="342" y="103" width="334" height="96" rx="5" fill="{surface}" opacity=".84" stroke="{line}"/>
<text x="360" y="124" class="mono" font-size="9" fill="{accent}" letter-spacing="1.5">MODEL OUTPUT / USER INPUTS</text>
<text x="360" y="151" class="mono" font-size="15" fill="{ink}">ENERGY → CASH FLOW</text>
<text x="360" y="176" class="mono" font-size="10" fill="{muted}">IRR  ·  ROI  ·  PAYBACK  ·  SUBSIDY</text>
<path d="M360 219H658" stroke="{line}"/>
<g class="mono" font-size="9">
 <rect x="360" y="232" width="82" height="28" rx="14" fill="{accent_soft}" opacity=".16"/><text x="401" y="250" text-anchor="middle" fill="{accent_soft}">INPUTS</text>
 <path d="M446 246H484" stroke="{accent_soft}" stroke-width="2" stroke-dasharray="5 6" class="zenith-flow"/>
 <rect x="490" y="232" width="82" height="28" rx="14" fill="{accent}" opacity=".17"/><text x="531" y="250" text-anchor="middle" fill="{accent}">ENERGY</text>
 <path d="M576 246H614" stroke="{accent}" stroke-width="2" stroke-dasharray="5 6" class="zenith-flow"/>
 <rect x="620" y="232" width="38" height="28" rx="14" fill="{ink}" opacity=".1"/><text x="639" y="250" text-anchor="middle" fill="{ink}">₹</text>
</g>
<rect x="342" y="282" width="334" height="73" rx="5" fill="{surface}" opacity=".84" stroke="{line}"/>
<text x="360" y="304" class="mono" font-size="9" fill="{muted}" letter-spacing="1.5">DECISION SUPPORT / NOT A QUOTE</text>
<text x="360" y="330" class="mono" font-size="12" fill="{ink}">ROOF GEOMETRY  +  SIMULATION  +  FINANCE</text>
<text x="360" y="348" class="mono" font-size="8" fill="{accent_soft}" letter-spacing="1">REACT  ·  THREE.JS  ·  PYTHON  ·  FASTAPI</text>
</g>'''

    if kind == "vision":
        accuracy = next(item for item in PROFILE["proof"] if item["id"] == "accuracy")["value"]
        feature_bars = []
        for index, (label, amount) in enumerate((("LBP", .82), ("GLCM", .66), ("EDGE", .48), ("COLOR", .31))):
            y = 155 + index * 28
            feature_bars.append(
                f'<text x="474" y="{y}" class="mono" font-size="8" fill="{muted}">{label}</text>'
                f'<rect x="516" y="{y-8}" width="88" height="8" rx="4" fill="{surface_alt}"/>'
                f'<rect x="516" y="{y-8}" width="{88 * amount:.1f}" height="8" rx="4" fill="{accent}" class="vision-confidence"/>'
            )
        lbp = _vision_lbp(296, 205, accent, accent_soft, surface_alt)
        glcm = _glcm_matrix(356, 143, accent)
        texture = _vision_texture_cells(57, 143)
        return f'''<g class="vision-motion">
<rect x="28" y="86" width="664" height="290" rx="6" fill="{surface}" stroke="{line}"/>
<image href="{art}" x="28" y="86" width="664" height="290" preserveAspectRatio="xMidYMid slice" opacity=".82"/>
<rect x="28" y="86" width="664" height="290" fill="{surface}" opacity=".22"/>
<text x="44" y="109" class="mono" font-size="9" fill="{accent}" letter-spacing="1.7">FORENSIC WORKBENCH / LOCAL INFERENCE</text>
<rect x="44" y="124" width="146" height="204" rx="4" fill="{surface_alt}" opacity=".72" stroke="{line}"/>
<text x="57" y="139" class="mono" font-size="8" fill="{muted}" letter-spacing="1.2">TEXTURE PATCH</text>
<g>{texture}</g>
<rect x="57" y="256" width="120" height="55" rx="3" fill="{canvas}" opacity=".5" stroke="{line}"/>
<path d="M65 300H168M65 300V268" stroke="{muted}" opacity=".7"/>
<path d="M68 291L91 281L111 289L133 272L163 278" fill="none" stroke="{accent}" stroke-width="2"/>
<text x="57" y="324" class="mono" font-size="7" fill="{muted}">SAMPLE / ILLUMINANCE NORMALIZED</text>
<circle cx="296" cy="205" r="58" fill="{surface_alt}" stroke="{line}"/>
<circle cx="296" cy="205" r="45" fill="none" stroke="{accent_soft}" stroke-dasharray="2 7"/>
{lbp}
<circle cx="296" cy="205" r="10" fill="{accent}" opacity=".18"/><circle cx="296" cy="205" r="4" fill="{accent}"/>
<text x="296" y="285" text-anchor="middle" class="mono" font-size="11" fill="{ink}" letter-spacing="1.5">LBP</text>
<text x="296" y="301" text-anchor="middle" class="mono" font-size="8" fill="{muted}">LOCAL PATTERN</text>
<rect x="342" y="124" width="106" height="140" rx="4" fill="{surface_alt}" opacity=".68" stroke="{line}"/>
<text x="356" y="139" class="mono" font-size="8" fill="{muted}" letter-spacing="1">GLCM</text>
<g>{glcm}</g>
<text x="356" y="236" class="mono" font-size="8" fill="{muted}">CONTRAST</text><text x="356" y="250" class="mono" font-size="8" fill="{muted}">ENTROPY</text>
<rect x="462" y="124" width="154" height="140" rx="4" fill="{surface}" opacity=".64" stroke="{line}"/>
<text x="478" y="140" class="mono" font-size="8" fill="{accent}" letter-spacing="1">FEATURE VECTOR</text>
{"".join(feature_bars)}
<rect x="630" y="124" width="46" height="140" rx="4" fill="{canvas}" opacity=".64" stroke="{line}"/>
<text x="653" y="141" text-anchor="middle" class="mono" font-size="7" fill="{muted}">SVM</text>
<path d="M653 157V231" stroke="{line}" stroke-width="8" stroke-linecap="round"/><path d="M653 157V208" stroke="{accent}" stroke-width="8" stroke-linecap="round" class="vision-confidence"/>
<text x="653" y="246" text-anchor="middle" class="mono" font-size="8" fill="{ink}">CAL.</text>
<path d="M44 340H676" stroke="{line}"/>
<path d="M205 340H640" stroke="{accent}" stroke-width="2" stroke-dasharray="6 10" class="vision-scan"/>
<text x="44" y="359" class="mono" font-size="9" fill="{muted}" letter-spacing="1.2">INPUT  →  TEXTURE  →  FEATURES  →  CALIBRATED SVM</text>
<text x="676" y="359" text-anchor="end" class="mono" font-size="8" fill="{accent}">{esc(accuracy)} HELD-OUT TEST ACCURACY</text>
</g>'''

    if kind == "token-usage":
        providers = "CHATGPT  ·  CLAUDE  ·  GEMINI  ·  PERPLEXITY  ·  GROK"
        return f'''<g class="token-usage-motion">
<rect x="28" y="86" width="664" height="290" rx="6" fill="{surface}" stroke="{line}"/>
<image href="{art}" x="28" y="86" width="664" height="290" preserveAspectRatio="xMidYMid slice" opacity=".78"/>
<rect x="28" y="86" width="664" height="290" fill="{canvas}" opacity=".34"/>
<text x="44" y="109" class="mono" font-size="9" fill="{accent}" letter-spacing="1.7">LOCAL-FIRST EXTENSION / MANIFEST V3</text>
<rect x="44" y="124" width="260" height="223" rx="5" fill="{surface_alt}" opacity=".76" stroke="{line}"/>
<text x="60" y="146" class="mono" font-size="10" fill="{muted}" letter-spacing="1.35">MULTI-AI USAGE COCKPIT</text>
<text x="60" y="176" class="mono" font-size="17" fill="{ink}" letter-spacing=".5">CAPTURE → NORMALIZE</text>
<text x="60" y="199" class="mono" font-size="9" fill="{accent_soft}">ONE LOCAL SIGNAL / FIVE PROVIDERS</text>
<path d="M64 232H284" stroke="{line}"/>
<g fill="{surface}" stroke="{accent}" stroke-width="1.2">
 <circle cx="72" cy="232" r="6"/><circle cx="126" cy="232" r="6"/><circle cx="180" cy="232" r="6"/><circle cx="234" cy="232" r="6"/><circle cx="284" cy="232" r="6"/>
</g>
<path d="M78 232H120M132 232H174M186 232H228M240 232H278" stroke="{accent}" stroke-width="2" stroke-dasharray="4 8" class="token-usage-packet"/>
<g class="mono" font-size="8" fill="{muted}">
 <text x="72" y="252" text-anchor="middle">READ</text><text x="126" y="252" text-anchor="middle">MAP</text><text x="180" y="252" text-anchor="middle">COUNT</text><text x="234" y="252" text-anchor="middle">QUOTA</text><text x="284" y="252" text-anchor="middle">EXPORT</text>
</g>
<text x="60" y="287" class="mono" font-size="8" fill="{muted}" letter-spacing="1.2">PRIVACY BY DEFAULT</text>
<text x="60" y="309" class="mono" font-size="9" fill="{ink}">OPTIONAL SYNC  ·  CLEAR DATA  ·  LOCAL STATE</text>
<rect x="324" y="124" width="352" height="223" rx="5" fill="{surface}" opacity=".58" stroke="{line}"/>
<text x="342" y="146" class="mono" font-size="9" fill="{accent}" letter-spacing="1.4">PROVIDER SIGNAL BUS</text>
<text x="658" y="146" text-anchor="end" class="mono" font-size="8" fill="{accent_soft}">EXPERIMENTAL</text>
<path d="M342 162H658" stroke="{line}"/>
<text x="342" y="184" class="mono" font-size="9" fill="{muted}">{providers}</text>
<path d="M360 222 C414 184 468 260 522 220 S600 192 650 230" fill="none" stroke="{accent}" stroke-width="2" stroke-dasharray="7 9" class="token-usage-signal"/>
<circle cx="522" cy="220" r="9" fill="{accent}" opacity=".2" class="token-usage-core"/><circle cx="522" cy="220" r="3.5" fill="{ink}" class="token-usage-core"/>
<text x="342" y="278" class="mono" font-size="8" fill="{muted}" letter-spacing="1.1">DASHBOARD / QUEUE / QUOTA / SYNC</text>
<path d="M342 298H658" stroke="{line}"/>
<text x="342" y="320" class="mono" font-size="9" fill="{accent_soft}">LOCAL OBSERVABILITY FOR AI WORKFLOWS</text>
</g>'''

    return f'''<g class="talks-motion">
<rect x="28" y="86" width="664" height="290" rx="6" fill="{surface}" stroke="{line}"/>
<image href="{art}" x="28" y="86" width="664" height="290" preserveAspectRatio="xMidYMid slice" opacity=".82"/>
<rect x="28" y="86" width="664" height="290" fill="{canvas}" opacity=".20"/>
<text x="44" y="109" class="mono" font-size="9" fill="{accent}" letter-spacing="1.7">ROOM 01 / ILLUSTRATIVE DEMO STATE</text>
<rect x="44" y="124" width="184" height="223" rx="5" fill="{surface_alt}" opacity=".68" stroke="{line}"/>
<text x="60" y="146" class="mono" font-size="11" fill="{ink}" letter-spacing="1">#YOR BUILDERS</text>
<circle cx="64" cy="174" r="5" fill="{accent}"/><text x="78" y="178" class="mono" font-size="10" fill="{ink}">ALPHA</text><text x="207" y="178" text-anchor="end" class="mono" font-size="8" fill="{accent}">ONLINE</text>
<circle cx="64" cy="204" r="5" fill="{accent_soft}"/><text x="78" y="208" class="mono" font-size="10" fill="{ink}">BETA</text><text x="207" y="208" text-anchor="end" class="mono" font-size="8" fill="{muted}">AWAY</text>
<circle cx="64" cy="234" r="5" fill="{accent}"/><text x="78" y="238" class="mono" font-size="10" fill="{ink}">NODE 03</text><text x="207" y="238" text-anchor="end" class="mono" font-size="8" fill="{accent}">ONLINE</text>
<path d="M60 268H212M60 289H185" stroke="{line}"/><text x="60" y="316" class="mono" font-size="8" fill="{muted}" letter-spacing="1">PRESENCE  ·  AUTH  ·  ROOMS</text>
<rect x="250" y="124" width="426" height="223" rx="5" fill="{surface}" opacity=".58" stroke="{line}"/>
<text x="268" y="146" class="mono" font-size="9" fill="{muted}" letter-spacing="1.4">MESSAGE FLOW / SOCKET.IO</text>
<rect x="268" y="158" width="178" height="43" rx="14" fill="{surface_alt}"/><text x="284" y="184" class="mono" font-size="10" fill="{ink}">ship the hard thing.</text><text x="430" y="193" text-anchor="end" class="mono" font-size="8" fill="{muted}">READ ✓✓</text>
<rect x="460" y="211" width="198" height="43" rx="14" fill="{accent}" opacity=".16" stroke="{accent}"/><text x="476" y="237" class="mono" font-size="10" fill="{ink}">building it now →</text><text x="642" y="246" text-anchor="end" class="mono" font-size="8" fill="{accent}">SENT ✓</text>
<text x="268" y="282" class="mono" font-size="8" fill="{muted}" letter-spacing="1.2">BETA IS TYPING</text>
<g fill="{accent}" class="talks-typing"><circle cx="351" cy="279" r="3"/><circle cx="362" cy="279" r="3"/><circle cx="373" cy="279" r="3"/></g>
<path d="M268 316H658" stroke="{line}"/><path d="M268 316H658" stroke="{accent}" stroke-width="2" stroke-dasharray="4 12" class="talks-packet"/>
<circle cx="312" cy="316" r="4" fill="{accent}" class="talks-typing"/><circle cx="444" cy="316" r="4" fill="{accent_soft}" class="talks-typing"/><circle cx="584" cy="316" r="4" fill="{accent}" class="talks-typing"/>
<text x="268" y="337" class="mono" font-size="8" fill="{muted}">DELIVERY  →  PRESENCE  →  READ STATE</text>
</g>'''


def build_project_card_svg(project, cfg):
    """Render a clean, art-first project cover; HTML owns the project details."""
    kind = project["kind"]
    world_key = "token-usage" if kind == "token-usage" else kind
    world = WORLD_TOKENS.get(world_key, WORLD_TOKENS["portfolio"])
    world_label = "LOCAL-FIRST EXTENSION" if kind == "token-usage" else world["label"]
    W, H = 720, 360
    art = asset_data_uri(
        VISUAL_CONTRACT["project_art"].get(kind, VISUAL_CONTRACT["project_art"]["talks"])
    )
    title_id = f"{kind}CardTitle"
    desc_id = f"{kind}CardDescription"
    description = (
        f'{project["title"]}: {world_label.lower()}. Clean illustrative artwork; '
        f'project details are provided below the cover. Status: {project.get("status", "published")}. '
        f'{project["summary"]}'
    )
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="{title_id} {desc_id}">
<title id="{title_id}">{esc(project["title"])} — {esc(world_label.lower())}</title>
<desc id="{desc_id}">{esc(description)}</desc>
<defs>
{project_motion_style(kind)}
<linearGradient id="{kind}Scrim" x1="0" y1="0" x2="1" y2="1">
 <stop offset="0" stop-color="#000" stop-opacity=".08"/><stop offset=".56" stop-color="#000" stop-opacity=".02"/>
 <stop offset="1" stop-color="#000" stop-opacity=".38"/>
</linearGradient>
<radialGradient id="{kind}Glow" cx="82%" cy="22%" r="76%">
 <stop offset="0" stop-color="{world["accent"]}" stop-opacity=".18"/><stop offset="1" stop-color="{world["accent"]}" stop-opacity="0"/>
</radialGradient>
<pattern id="{kind}MicroGrid" width="28" height="28" patternUnits="userSpaceOnUse">
 <path d="M28 0H0V28" fill="none" stroke="{world["accent_soft"]}" stroke-width=".45" opacity=".09"/>
</pattern>
</defs>
<rect x="1" y="1" width="718" height="358" rx="9" fill="{world["canvas"]}" stroke="{world["line"]}"/>
<image href="{art}" x="2" y="2" width="716" height="356" preserveAspectRatio="xMidYMid slice"/>
<rect x="2" y="2" width="716" height="356" fill="url(#{kind}Scrim)"/>
<rect x="2" y="2" width="716" height="356" fill="url(#{kind}Glow)"/>
<rect x="2" y="2" width="716" height="356" fill="url(#{kind}MicroGrid)"/>
<g class="{kind}-motion" aria-hidden="true" pointer-events="none">
<path d="M28 18H692V342H28Z" fill="none" stroke="{world["accent"]}" stroke-width="1.4" stroke-dasharray="18 742" stroke-dashoffset="760" class="{kind}-frame-sweep" opacity=".46"/>
<path d="M38 28h58M38 28v42M682 28h-58M682 28v42M38 332h58M38 332v-42M682 332h-58M682 332v-42" fill="none" stroke="{world["accent_soft"]}" stroke-width="1" opacity=".56"/>
<ellipse cx="590" cy="86" rx="92" ry="28" fill="none" stroke="{world["accent_soft"]}" stroke-width="1" stroke-dasharray="3 12" opacity=".42" class="{kind}-ambient-orbit"/>
<circle cx="590" cy="86" r="4" fill="{world["accent"]}" class="{kind}-ambient-pulse"/>
<path d="M42 310H242" stroke="{world["accent"]}" stroke-width="1.5" stroke-dasharray="3 12" opacity=".48" class="{kind}-frame-sweep"/>
{clean_project_overlay_svg(kind, world)}
</g>
<rect x="1" y="1" width="718" height="358" rx="9" fill="none" stroke="{world["accent"]}" stroke-opacity=".34"/>
</svg>'''


def build_arsenal_svg(cfg):
    W, H = 1500, 540
    tech = [
        (750, 76, "TYPESCRIPT"), (1000, 116, "REACT / NEXT"), (1182, 264, "THREE.JS / R3F"),
        (1030, 424, "PYTHON / ML"), (750, 474, "FASTAPI"), (470, 424, "NODE / REST"),
        (318, 264, "DOCKER / AWS"), (500, 116, "VITEST / CI"),
    ]
    spokes = []
    labels = []
    for i, (x, y, label) in enumerate(tech):
        spokes.append(
            f'<path d="M750 270 L{x} {y}" stroke="#671515" stroke-width="1.2" '
            f'stroke-dasharray="5 11"><animate attributeName="stroke-dashoffset" '
            f'values="0;-64" dur="{4+i*.45:.1f}s" repeatCount="indefinite"/></path>'
        )
        labels.append(
            f'<g><rect x="{x-76}" y="{y-22}" width="152" height="44" rx="4" '
            f'fill="#070101" stroke="#4c0d0d"/>'
            f'<circle cx="{x-58}" cy="{y}" r="4" fill="#e84b4b">'
            f'<animate attributeName="opacity" values=".25;1;.25" dur="{1.4+i*.17:.2f}s" '
            f'repeatCount="indefinite"/></circle>'
            f'<text x="{x+8}" y="{y+5}" text-anchor="middle" class="mono" font-size="11" '
            f'fill="#d9cccc" letter-spacing="1">{esc(label)}</text></g>'
        )
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<radialGradient id="arsenalGlow">
<stop offset="0" stop-color="#e84b4b" stop-opacity=".2"/>
<stop offset="1" stop-color="#e84b4b" stop-opacity="0"/>
</radialGradient>
<pattern id="arsenalGrid" width="30" height="30" patternUnits="userSpaceOnUse">
<path d="M30 0H0V30" fill="none" stroke="#671515" stroke-width=".45" opacity=".09"/>
</pattern>
</defs>
<rect x="1" y="1" width="1498" height="538" rx="7" fill="#020202" stroke="#350909"/>
<rect x="1" y="1" width="1498" height="538" rx="7" fill="url(#arsenalGrid)"/>
<image href="{asset_data_uri(SUPPORTING_ART["atlas"])}" x="260" y="20" width="980" height="500" preserveAspectRatio="xMidYMid slice" opacity=".24"/>
<rect x="260" y="20" width="980" height="500" rx="6" fill="#020202" opacity=".34"/>
<circle cx="750" cy="270" r="246" fill="url(#arsenalGlow)"/>
<ellipse cx="750" cy="270" rx="390" ry="210" fill="none" stroke="#310808"/>
<ellipse cx="750" cy="270" rx="295" ry="158" fill="none" stroke="#671515"
 stroke-dasharray="8 14" opacity=".65">
<animateTransform attributeName="transform" type="rotate" from="0 750 270"
 to="360 750 270" dur="34s" repeatCount="indefinite"/>
</ellipse>
<circle cx="750" cy="270" r="126" fill="none" stroke="#e84b4b" opacity=".18"
 stroke-dasharray="3 12">
<animateTransform attributeName="transform" type="rotate" from="360 750 270"
 to="0 750 270" dur="18s" repeatCount="indefinite"/>
</circle>
{"".join(spokes)}
{"".join(labels)}
<circle cx="750" cy="270" r="82" fill="#050101" stroke="#e84b4b" stroke-width="1.5"/>
<circle cx="750" cy="270" r="64" fill="none" stroke="#ff8a7f" opacity=".55"
 stroke-dasharray="5 8">
<animateTransform attributeName="transform" type="rotate" from="0 750 270"
 to="-360 750 270" dur="9s" repeatCount="indefinite"/>
</circle>
<text x="750" y="262" text-anchor="middle" class="serif" font-size="31" fill="#f5eaea">AYR</text>
<text x="750" y="289" text-anchor="middle" class="mono" font-size="9" fill="#e84b4b"
 letter-spacing="2">TECHNICAL CORE</text>
<text x="38" y="44" class="mono" font-size="10" fill="#8d7777" letter-spacing="2">
PRODUCT · SYSTEMS · INFRASTRUCTURE
</text>
<text x="1462" y="514" text-anchor="end" class="mono" font-size="9" fill="#6f5b5b"
 letter-spacing="2">TOOLS ARE LOADOUT. SYSTEMS ARE THE WORK.</text>
</svg>'''


def build_finale_svg(cfg):
    W, H = 1500, 300
    rng = random.Random(cfg["seed"] + 1400)
    stars = "".join(
        f'<circle cx="{rng.uniform(20,W-20):.1f}" cy="{rng.uniform(10,150):.1f}" '
        f'r="{rng.uniform(.5,1.6):.2f}" fill="#ff8a7f" opacity="{rng.uniform(.15,.75):.2f}">'
        f'<animate attributeName="opacity" values=".1;.9;.1" dur="{rng.uniform(2,5):.2f}s" '
        f'begin="-{rng.uniform(0,4):.2f}s" repeatCount="indefinite"/></circle>'
        for _ in range(42)
    )
    return f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
<defs>
{experience_font_defs()}
<radialGradient id="finalSun">
<stop offset="0" stop-color="#ff8a7f"/><stop offset=".38" stop-color="#e84b4b"/>
<stop offset="1" stop-color="#671515" stop-opacity="0"/>
</radialGradient>
<linearGradient id="finalHorizon" x1="0%" y1="0%" x2="0%" y2="100%">
<stop offset="0%" stop-color="#000"/><stop offset="100%" stop-color="#220404"/>
</linearGradient>
<pattern id="floorGrid" width="62" height="28" patternUnits="userSpaceOnUse"
 patternTransform="skewX(-26)">
<path d="M62 0H0V28" fill="none" stroke="#e84b4b" stroke-width=".7" opacity=".18"/>
</pattern>
</defs>
<rect width="{W}" height="{H}" fill="url(#finalHorizon)"/>
<image href="{asset_data_uri(SUPPORTING_ART["channel"])}" x="0" y="0" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice" opacity=".46"/>
<rect width="{W}" height="{H}" fill="#000" opacity=".24"/>
{stars}
<circle cx="750" cy="230" r="176" fill="url(#finalSun)" opacity=".68">
<animate attributeName="opacity" values=".52;.78;.52" dur="5s" repeatCount="indefinite"/>
</circle>
<rect y="204" width="{W}" height="96" fill="url(#floorGrid)"/>
<rect y="203" width="{W}" height="1" fill="#ff8a7f" opacity=".7"/>
<rect x="280" y="40" width="940" height="136" rx="5" fill="#000" opacity=".74"
 stroke="#671515"/>
<text x="750" y="100" text-anchor="middle" class="serif" font-size="48" fill="#f5eaea"
 letter-spacing="3">GRIND. BUILD. REPEAT.</text>
<text x="750" y="137" text-anchor="middle" class="mono" font-size="11" fill="#c4b4b4"
 letter-spacing="3">NO NOISE · NO SHORTCUTS · JUST FOCUS AND THE WORK</text>
<circle cx="610" cy="160" r="4" fill="#e84b4b">
<animate attributeName="opacity" values=".2;1;.2" dur="1.4s" repeatCount="indefinite"/>
</circle>
<text x="750" y="165" text-anchor="middle" class="mono" font-size="9" fill="#e84b4b"
 letter-spacing="2">CHANNEL OPEN // COLLABORATION SIGNAL ACTIVE</text>
</svg>'''


def generate_legacy_asset_set():
    os.makedirs(OUT_DIR, exist_ok=True)

    hero = build_cinematic_hero_svg(CONFIG)
    hero_path = os.path.join(OUT_DIR, "hero.svg")
    with open(hero_path, "w", encoding="utf-8") as f:
        f.write(hero)
    print(f"wrote {hero_path} ({len(hero)/1024:.1f} KB)")

    for label, color in [("primary", CONFIG["primary"]), ("secondary", CONFIG["secondary"])]:
        div = build_divider_svg(color)
        div_path = os.path.join(OUT_DIR, f"divider-{label}.svg")
        with open(div_path, "w", encoding="utf-8") as f:
            f.write(div)
        print(f"wrote {div_path} ({len(div)/1024:.1f} KB)")

    wave_specs = [
        ("wave-header", CONFIG["wave_header_stops"], True, 12, CONFIG["seed"] + 1),
        ("wave-footer", CONFIG["wave_footer_stops"], False, 12, CONFIG["seed"] + 2),
    ]
    for name, stops, crest_up, star_count, seed in wave_specs:
        svg = build_wave_banner_svg(1500, 40, stops, crest_up, star_count, CONFIG["primary"], seed)
        path = os.path.join(OUT_DIR, f"{name}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path} ({len(svg)/1024:.1f} KB)")

    wave_final = build_wave_final_svg(CONFIG)
    wave_final_path = os.path.join(OUT_DIR, "wave-final.svg")
    with open(wave_final_path, "w", encoding="utf-8") as f:
        f.write(wave_final)
    print(f"wrote {wave_final_path} ({len(wave_final)/1024:.1f} KB)")

    tagline = build_tagline_svg(CONFIG)
    tagline_path = os.path.join(OUT_DIR, "tagline.svg")
    with open(tagline_path, "w", encoding="utf-8") as f:
        f.write(tagline)
    print(f"wrote {tagline_path} ({len(tagline)/1024:.1f} KB)")

    for i, (name, glyph, color_key) in enumerate(CONFIG["seals"]):
        seal = build_seal_svg(glyph, CONFIG[color_key], CONFIG["seed"] + 100 + i)
        seal_path = os.path.join(OUT_DIR, f"{name}.svg")
        with open(seal_path, "w", encoding="utf-8") as f:
            f.write(seal)
        print(f"wrote {seal_path} ({len(seal)/1024:.1f} KB)")

    panel_headers = [
        ("panel-profile", "SYSTEM PROFILE", "STATUS // BUILDING"),
        ("panel-showcase", "PROJECT SHOWCASE", "06 SYSTEMS // 01 ACTIVE BUILD"),
        ("panel-loadout", "TECHNICAL LOADOUT", "PRODUCT // SYSTEMS // INFRA"),
        ("panel-record", "SYSTEM RECORD", "PUBLIC BUILD LOG"),
    ]
    for filename, title, subtitle in panel_headers:
        panel = build_panel_header_svg(title, subtitle, CONFIG)
        panel_path = os.path.join(OUT_DIR, f"{filename}.svg")
        with open(panel_path, "w", encoding="utf-8") as f:
            f.write(panel)
        print(f"wrote {panel_path} ({len(panel)/1024:.1f} KB)")

    experience_assets = {
        "signal-strip": build_signal_strip_svg(CONFIG),
        "identity-console": build_identity_console_svg(CONFIG),
        "operator-gateway": build_operator_gateway_svg(CONFIG),
        "achievement-rack": build_achievement_rack_svg(CONFIG),
        "protocol-engineer": build_protocol_engineer_svg(CONFIG),
        "protocol-product": build_protocol_product_svg(CONFIG),
        "protocol-human": build_protocol_human_svg(CONFIG),
        "project-portfolio": build_featured_project_svg(CONFIG),
        "arsenal": build_arsenal_svg(CONFIG),
        "finale": build_finale_svg(CONFIG),
    }
    for filename, svg in experience_assets.items():
        path = os.path.join(OUT_DIR, f"{filename}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path} ({len(svg)/1024:.1f} KB)")

    nav_specs = [
        ("nav-portfolio", "PORTFOLIO", "ENTER THE SYSTEM", "◢"),
        ("nav-projects", "PROJECTS", "EXPLORE THE BUILDS", "⌁"),
        ("nav-steam", "STEAM", "OPERATOR PROFILE", "◉"),
        ("nav-contact", "CONNECT", "OPEN A CHANNEL", "◇"),
    ]
    for i, (filename, label, code, glyph) in enumerate(nav_specs):
        svg = build_nav_button_svg(label, code, glyph, CONFIG, CONFIG["seed"] + 1500 + i)
        path = os.path.join(OUT_DIR, f"{filename}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path} ({len(svg)/1024:.1f} KB)")

    section_specs = [
        ("section-identity", "01", "OPERATOR / IDENTITY", "THE PERSON BEHIND THE SYSTEMS"),
        ("section-projects", "02", "SELECTED / SYSTEMS", "CLICK ANY VISUAL TO OPEN THE BUILD"),
        ("section-arsenal", "03", "TECHNICAL / ARSENAL", "PRODUCT · SYSTEMS · INFRASTRUCTURE"),
        ("section-record", "04", "PUBLIC / RECORD", "REPOSITORIES · LANGUAGES · SIGNAL"),
    ]
    for filename, index, title, subtitle in section_specs:
        svg = build_section_header_svg(index, title, subtitle, CONFIG)
        path = os.path.join(OUT_DIR, f"{filename}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path} ({len(svg)/1024:.1f} KB)")

    projects = [
        {
            "filename": "project-helios", "kind": "helios", "code": "SYS-02",
            "domain": "REALTIME TELEMETRY", "title": "YOR HELIOS",
            "stack": "PYTHON · FASTAPI · WEBSOCKETS · DOCKER",
            "summary": "Threshold intelligence and anomaly alerts, streamed live.",
        },
        {
            "filename": "project-zenith", "kind": "zenith", "code": "SYS-03",
            "domain": "GEOSPATIAL SOLAR", "title": "YOR ZENITH",
            "stack": "REACT · TYPESCRIPT · THREE.JS · PYTHON",
            "summary": "Roof geometry, irradiance, placement, ROI, and payback.",
        },
        {
            "filename": "project-vision", "kind": "vision", "code": "SYS-04",
            "domain": "COMPUTER VISION", "title": "AI VS REAL",
            "stack": "PYTHON · OPENCV · SCIKIT-LEARN · STREAMLIT",
            "summary": "Texture intelligence with calibrated confidence.",
        },
        {
            "filename": "project-talks", "kind": "talks", "code": "SYS-05",
            "domain": "REALTIME COMMS", "title": "YOR TALKS",
            "stack": "REACT · NEXT.JS · FASTAPI · WEBSOCKET",
            "summary": "Bidirectional rooms, delivery, auth, and presence.",
        },
        {
            "filename": "project-token-usage", "kind": "token-usage", "code": "SYS-05",
            "domain": "MULTI-AI USAGE", "title": "YOR TOKEN USAGE",
            "stack": "JAVASCRIPT · MANIFEST V3 · CHROME EXTENSIONS",
            "summary": "Local-first usage capture, dashboards, exports, and optional sync.",
        },
        {
            "filename": "project-next", "kind": "next", "code": "SYS-07",
            "domain": "OPEN CHANNEL", "title": "NEXT TRANSMISSION",
            "stack": "COLLABORATION · RESEARCH · OPEN SOURCE",
            "summary": "Bring the difficult problem. We'll build the system.",
        },
    ]
    for project in projects:
        svg = build_project_card_svg(project, CONFIG)
        path = os.path.join(OUT_DIR, f'{project["filename"]}.svg')
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path} ({len(svg)/1024:.1f} KB)")


def canonical_project_card_spec(project):
    return {
        "kind": project["id"],
        "code": f'SYS-{project["order"]:02d}',
        "domain": project["codename"],
        "title": project["name"].upper(),
        "stack": " · ".join(project["stack"][:4]).upper(),
        "summary": project["proof"][0].rstrip(".") + ".",
        "status": project["status"],
        "period": project["period"],
    }


def build_atlas_asset_manifest():
    """Build only assets used by the public README."""
    manifest = {
        "hero.svg": build_cinematic_hero_svg(CONFIG),
        "identity-console.svg": build_identity_console_svg(CONFIG),
        "signal-strip.svg": build_signal_strip_svg(CONFIG),
        "field-notes.svg": build_field_notes_svg(CONFIG),
        "skills-matrix.svg": build_skills_matrix_svg(CONFIG),
        "operator-gateway.svg": build_operator_gateway_svg(CONFIG),
        "achievement-rack.svg": build_achievement_rack_svg(CONFIG),
        "protocol-engineer.svg": build_protocol_engineer_svg(CONFIG),
        "protocol-product.svg": build_protocol_product_svg(CONFIG),
        "protocol-human.svg": build_protocol_human_svg(CONFIG),
        "project-portfolio-v2.svg": build_featured_project_svg(CONFIG),
        "project-portfolio-mobile-v2.svg": build_featured_project_svg(CONFIG, mobile=True),
        "dossier-toggle.svg": build_dossier_toggle_svg(),
        "arsenal.svg": build_arsenal_svg(CONFIG),
        "finale.svg": build_finale_svg(CONFIG),
    }

    for index, (target, label) in enumerate((
        ("projects", "PROJECTS"), ("experience", "EXPERIENCE"),
        ("activity", "ACTIVITY"), ("contact", "CONTACT"),
    )):
        manifest[f"jump-{target}.svg"] = build_jump_button_svg(label, index)

    for index, proof_item in enumerate(PROFILE["proof"]):
        manifest[f'proof-{proof_item["id"]}.svg'] = build_proof_card_svg(
            proof_item, index, CONFIG
        )

    nav_specs = (
        ("nav-portfolio.svg", "PORTFOLIO", "ENTER THE SYSTEM", "◢"),
        ("nav-projects.svg", "PROJECTS", "EXPLORE THE BUILDS", "⌁"),
        ("nav-resume.svg", "RÉSUMÉ", "VIEW PUBLIC RECORD", "▤"),
        ("nav-linkedin.svg", "LINKEDIN", "OPEN PROFESSIONAL LINK", "◇"),
        ("nav-live.svg", "LIVE SYSTEM", "LAUNCH DEPLOYMENT", "◈"),
        ("nav-source.svg", "SOURCE", "INSPECT REPOSITORY", "⌁"),
        ("nav-email.svg", "EMAIL", "TRANSMIT MESSAGE", "◇"),
        ("nav-github.svg", "GITHUB", "OPEN BUILD RECORD", "⌁"),
        ("nav-devpost.svg", "DEVPOST", "VIEW PROTOTYPES", "◈"),
        ("nav-steam.svg", "STEAM", "OPEN HUMAN ARCHIVE", "◉"),
    )
    for index, (filename, label, code, glyph) in enumerate(nav_specs):
        manifest[filename] = build_nav_button_svg(
            label, code, glyph, CONFIG, CONFIG["seed"] + 1500 + index
        )

    section_specs = (
        ("section-projects.svg", "01", "SELECTED / SYSTEMS", "SIX SYSTEMS · PUBLIC PROOF · VERIFIED DATA"),
        ("section-field.svg", "02", "FIELD / NOTES", "EXPERIENCE · EDUCATION · TRAJECTORY"),
        ("section-arsenal.svg", "03", "TECHNICAL / RANGE", "PRODUCT · BACKEND · APPLIED ML"),
        ("section-record.svg", "04", "LIVE / TELEMETRY", "TOTAL VIEWS · 365-DAY STREAM · PUBLIC SIGNALS"),
        ("section-operator.svg", "05", "OPERATOR / MODE", "INTERACTIVE PROTOCOL ARCHIVE"),
        ("section-channel.svg", "06", "OPEN / CHANNEL", "INTERNSHIPS · PRODUCTS · COLLABORATION"),
    )
    for filename, index, title, subtitle in section_specs:
        manifest[filename] = build_section_header_svg(index, title, subtitle, CONFIG)

    projects = {project["id"]: project for project in PROFILE["projects"]}
    for project_id in ("vision", "zenith", "helios", "token-usage", "talks"):
        manifest[f"project-{project_id}.svg"] = build_project_card_svg(
            canonical_project_card_spec(projects[project_id]), CONFIG
        )

    for project in PROFILE["projects"]:
        manifest[f'project-summary-{project["id"]}.svg'] = build_project_summary_svg(
            project, CONFIG
        )
        manifest[f'project-dossier-{project["id"]}.svg'] = build_project_dossier_svg(
            project, CONFIG
        )

    return apply_atlas_treatment(manifest)


def build_asset_manifest():
    from redline import build_surfaces

    manifest = build_surfaces(PROFILE)
    manifest["hero.svg"] = build_cinematic_hero_svg(CONFIG)
    manifest["project-portfolio-v2.svg"] = build_featured_project_svg(CONFIG)
    manifest["project-portfolio-mobile-v2.svg"] = build_featured_project_svg(CONFIG, mobile=True)
    for project in PROFILE["projects"]:
        if project["id"] != "portfolio":
            manifest[f'project-{project["id"]}.svg'] = build_project_card_svg(
                canonical_project_card_spec(project), CONFIG
            )
    return {name: apply_red_theme(svg) for name, svg in manifest.items()}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = build_asset_manifest()
    expected = set(manifest)
    preserved = {"stats.svg", "stats-mobile.svg", "contribution-stream.svg", "contribution-stream-mobile.svg"}

    for stale_path in OUT_DIR.glob("*.svg"):
        if stale_path.name not in expected | preserved:
            stale_path.unlink()
            print(f"removed stale generated asset {stale_path}")

    total_bytes = 0
    for filename, svg in manifest.items():
        path = OUT_DIR / filename
        path.write_text(svg, encoding="utf-8")
        size = path.stat().st_size
        total_bytes += size
        print(f"wrote {path} ({size / 1024:.1f} KB)")

    print(f"generated {len(manifest)} README assets ({total_bytes / 1024:.1f} KB total)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
