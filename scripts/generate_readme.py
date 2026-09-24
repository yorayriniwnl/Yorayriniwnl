#!/usr/bin/env python3
"""Render the public GitHub profile from canonical data and owned visual assets."""
from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from profile_data import load_profile
from redline import ORDER, REVISION, SHORT

ROOT = SCRIPT_DIR.parent
README_PATH = ROOT / "README.md"
PROFILE_REPOSITORY = "Yorayriniwnl"
SELECTED_PROJECT_IDS = ORDER
PROJECT_VISUALS = {p: f'project-{p}.svg' for p in ORDER}
PROJECT_VISUALS["portfolio"] = "project-portfolio-v2.svg"
PROJECT_SUMMARIES = {p: f'project-summary-{p}.svg' for p in ORDER}
RESPONSIVE_ASSETS = {
    "identity-console.svg", "signal-strip.svg", "field-notes.svg", "skills-matrix.svg",
    "arsenal.svg", "finale.svg", "operator-gateway.svg", "achievement-rack.svg",
    "protocol-engineer.svg", "protocol-product.svg", "protocol-human.svg",
    "stats.svg", "contribution-stream.svg",
    "dossier-toggle.svg",
    *[f'section-{s}.svg' for s in ("projects", "field", "arsenal", "record", "operator", "channel")],
    *PROJECT_SUMMARIES.values(), *[f'project-dossier-{p}.svg' for p in ORDER],
}
MOTION_ASSETS = ("systems-reel-v8.gif", "systems-reel-mobile-v8.gif", "systems-reel-v8-still.png", "systems-reel-mobile-v8-still.png")
ASSET_REVISIONS = {
    "hero.svg": "career-v1",
    **{f'{name}{suffix}.svg': "career-v1" for name in ("identity-console", "section-channel", "finale") for suffix in ("", "-mobile")},
    "project-portfolio-v2.svg": "raster-v8", "project-portfolio-mobile-v2.svg": "raster-v8",
    "project-helios.svg": "raster-v15", "project-zenith.svg": "raster-v14",
    "project-vision.svg": "raster-v16", "project-talks.svg": "raster-v14", "project-token-usage.svg": "raster-v15",
    **{name: "motion-v8" for name in MOTION_ASSETS},
}
# Compact control geometry changed after checking GitHub's narrower mobile column.
CONTROL_REVISION = "redline-v2"


def raw_asset_url(handle, filename):
    revision = ASSET_REVISIONS.get(filename, CONTROL_REVISION if filename.startswith(("jump-", "nav-", "project-index-")) else REVISION)
    return f'https://raw.githubusercontent.com/{handle}/{PROFILE_REPOSITORY}/output/{filename}?rev={revision}'


def profile_views_url(handle):
    return f'https://komarev.com/ghpvc/?username={handle}&amp;label=TOTAL+PROFILE+VIEWS&amp;color=ff1f2d&amp;style=for-the-badge&amp;abbreviated=false'


def image(filename, alt, handle, width="100%"):
    tag = f'<img src="{raw_asset_url(handle, filename)}" width="{width}" alt="{html.escape(alt, quote=True)}"/>'
    mobile = filename.replace(".svg", "-mobile.svg")
    if filename == "project-portfolio-v2.svg":
        mobile = "project-portfolio-mobile-v2.svg"
    if filename in RESPONSIVE_ASSETS or filename == "project-portfolio-v2.svg":
        return f'<picture><source media="(max-width: 600px)" srcset="{raw_asset_url(handle, mobile)}"/>{tag}</picture>'
    return tag


def linked_image(href, filename, alt, handle, width="100%"):
    return [f'<a href="{html.escape(href, quote=True)}">{image(filename, alt, handle, width)}</a>']


def linked_button(href, filename, alt, handle):
    # GitHub prefixes authored IDs during sanitization; target the rendered ID.
    if href.startswith('#') and not href.startswith('#user-content-'):
        href = '#user-content-' + href[1:]
    return linked_image(href, filename, alt, handle, "145")[0]


def buttons(items, handle):
    return ['<p align="center">', *[linked_button(url, asset, alt, handle) for url, asset, alt in items], '</p>', '']


def systems_reel(handle):
    variants = (
        ("(max-width: 600px) and (prefers-reduced-motion: reduce)", "systems-reel-mobile-v8-still.png"),
        ("(prefers-reduced-motion: reduce)", "systems-reel-v8-still.png"),
        ("(max-width: 600px)", "systems-reel-mobile-v8.gif"),
    )
    return ["<picture>", *[f'<source media="{media}" srcset="{raw_asset_url(handle, asset)}"/>' for media, asset in variants],
            image("systems-reel-v8.gif", "Six project domains in motion. Illustrative animation, not live telemetry.", handle), "</picture>"]


def project_block(project, handle):
    pid = project["id"]
    target = project.get("live") or project["repo"]
    detail = f'{project["name"]}: {project["status"]}. {project["summary"]} Proof: {"; ".join(project["proof"])}. Stack: {"; ".join(project["stack"])}.'
    dossier_alt = f'Expand {project["name"]} project details'
    links = [(project["repo"], "nav-source.svg", f'Inspect {project["name"]} source repository')]
    if project.get("live"):
        links.insert(0, (project["live"], "nav-live.svg", f'Open {project["name"]} project'))
    return [f'<a id="project-{pid}"></a>', '',
            *linked_image(target, PROJECT_VISUALS[pid], f'{project["name"]}: {project["codename"].lower()}. Illustrative artwork.', handle), '',
            image(PROJECT_SUMMARIES[pid], detail, handle), '', '<details>',
            f'<summary>{image("dossier-toggle.svg", dossier_alt, handle, "95%")}</summary>', '',
            image(f'project-dossier-{pid}.svg', detail, handle), '', *buttons(links, handle), '</details>', '']


def render_readme(profile=None):
    p = profile or load_profile()
    contact, handle = p["contact"], p["identity"]["handle"]
    resume = f'https://github.com/{handle}/{PROFILE_REPOSITORY}/blob/main/output/pdf/Ayush_Roy_Resume_Public.pdf'
    lines = ['<!-- Generated by scripts/generate_readme.py from data/profile.json. -->', '', '<div align="center">', '',
             *linked_image(contact["portfolio"], "hero.svg", f'{p["identity"]["name"]}, {p["identity"]["role"]} and {p["identity"]["specialty"]}', handle), '',
             *buttons([(f'#{anchor}', f'jump-{slug}.svg', f'Jump to {label}') for anchor,slug,label in (
                 ("selected-systems","projects","selected projects"), ("field-notes","experience","experience and education"),
                 ("public-record","activity","GitHub activity and profile views"), ("open-channel","contact","contact and collaboration"))], handle),
             image("identity-console.svg", f'Currently {p["identity"]["role"]}. {p["identity"]["positioning"]} {p["availability"]["status"]}. {p["identity"]["location"]}.', handle), '',
             *buttons([(contact["portfolio"],"nav-portfolio.svg","Open Ayush Roy portfolio"),(resume,"nav-resume.svg","View Ayush Roy public resume"),
                       (contact["linkedin"],"nav-linkedin.svg","Connect on LinkedIn"),(f'mailto:{contact["email"]}',"nav-email.svg","Email Ayush Roy")],handle),
             image("signal-strip.svg","Product, realtime systems, computer vision, and 3D interfaces",handle), '', '<p>']
    for i,item in enumerate(p["proof"]):
        lines.append(image(f'proof-{item["id"]}.svg', f'{item["value"]} {item["label"]}. {item["detail"]}', handle, "350"))
        if i == 1:
            lines.append('<br/>')
    lines += ['</p>', '', '</div>', '', '<a id="selected-systems"></a>', '',
              image("section-projects.svg", "Section 01: six selected projects", handle), '',
              *buttons([(f'#project-{pid}',f'project-index-{pid}.svg',f'Jump to {SHORT[pid]}') for pid in ORDER],handle)]
    projects={project["id"]:project for project in p["projects"]}
    for pid in ORDER:
        lines += project_block(projects[pid],handle)
    exp,edu=p["experience"][0],p["education"][0]
    lines += ['<a id="field-notes"></a>', '', image("section-field.svg","Section 02: experience and education",handle),'',
              image("field-notes.svg",f'{exp["role"]} at {exp["organization"]}, {exp["period"]}. {exp["summary"]} {edu["degree"]} at {edu["institution"]}, {edu["period"]}. Coursework: {"; ".join(edu["coursework"])}.',handle),'',
              *buttons([(resume,"nav-resume.svg","View the public resume")],handle),
              image("section-arsenal.svg","Section 03: technical range",handle),'',image("arsenal.svg","Across the stack, from interface to infrastructure",handle),'',
              image("skills-matrix.svg", "; ".join(f'{key}: {", ".join(values)}' for key,values in p["skills"].items()),handle),'',
              '<a id="public-record"></a>','',image("section-record.svg","Section 04: public GitHub activity",handle),'',
              '<p align="center">',f'<img src="{profile_views_url(handle)}" width="350" alt="Total profile views, as counted by Komarev"/>','</p>','',
              *linked_image(contact["github"],"stats.svg","GitHub repositories, stars, followers, and languages. Timestamped public snapshot.",handle),'',
              *linked_image(contact["github"],"contribution-stream.svg","365 days of GitHub contributions, with date range and activity totals",handle),'',
              image("section-operator.svg","Section 05: the process and the person",handle),'','<details>',
              '<summary>'+image("operator-gateway.svg","Expand the field manual: process, principles, and off the clock",handle,"95%")+'</summary>','',
              *systems_reel(handle),'',image("achievement-rack.svg","Achievements beyond the code",handle),'',
              image("protocol-engineer.svg","Engineering process",handle),'',image("protocol-product.svg","Product principles",handle),'',
              *linked_image(contact["steam"],"protocol-human.svg","Off the clock: visit Ayush Roy on Steam",handle),'','</details>','',
              '<a id="open-channel"></a>','',image("section-channel.svg","Section 06: jobs and collaboration",handle),'',
              *linked_image(f'mailto:{contact["email"]}',"finale.svg","Start a conversation with Ayush Roy",handle),'',
              *buttons([(f'mailto:{contact["email"]}',"nav-email.svg","Email Ayush Roy"),(contact["linkedin"],"nav-linkedin.svg","Connect on LinkedIn"),
                        (contact["portfolio"],"nav-portfolio.svg","Open the portfolio"),(contact["github"],"nav-github.svg","Follow on GitHub"),
                        (contact["devpost"],"nav-devpost.svg","Explore Devpost prototypes"),(contact["steam"],"nav-steam.svg","Open Steam profile")],handle)]
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    rendered=render_readme()
    if args.check:
        if not README_PATH.is_file() or README_PATH.read_text(encoding='utf-8') != rendered:
            print('README.md is out of date; run scripts/generate_readme.py',file=sys.stderr)
            return 1
        print('README.md matches canonical profile data')
        return 0
    README_PATH.write_text(rendered,encoding='utf-8')
    print(f'wrote {README_PATH} ({len(rendered):,} characters)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
