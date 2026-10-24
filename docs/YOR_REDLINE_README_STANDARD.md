# YOR REDLINE · Repository README Design Standard

**Design owner:** [YOR / Ayush Roy](https://github.com/yorayriniwnl)  
**Status:** Applied across 28 non-archived, non-profile repositories on 2026-10-24.  
**Purpose:** Keep each repository technically useful and visually recognizable as part of the YOR engineering family.

## Core visual language

| Token | Value | Usage |
| --- | --- | --- |
| Obsidian | `#060507` | Primary cover background |
| Deep crimson | `#20060f` | Background gradient finish |
| Signal red | `#ff3449` | Emphasis, small markers, graph outlines |
| Warm white | `#fff3f3` | Hero title |
| Dust rose | `#e8cdd1` | Secondary title |
| Muted rose | `#ed8491` | Descriptor line |
| Editorial type | `Georgia, serif` fallback | Large project title inside SVG |
| Technical type | `Arial, sans-serif` | Small metadata, subheadings, labels |

The profile README remains the canonical reference for the full editorial identity. Repository covers simplify the identity deliberately: one dominant title, one subtitle, one purpose line, one restrained technical illustration.

## Asset contract

Each repository stores independent artwork at:

- `docs/yor-redline-cover.svg` (desktop, `1440 × 450`)
- `docs/yor-redline-cover-mobile.svg` (mobile, `720 × 760`)

Both assets are SVG and include accessible `<title>` and `<desc>` elements. Do not load runtime assets from third-party badge/image generators for the hero. Mobile artwork is a separately composed cover, not a scaled-down desktop text image.

## Markdown embed contract

```html
<!-- YOR REDLINE / README COVER V1 -->
<div align="center">

<picture>
  <source media="(max-width: 600px)" srcset="docs/yor-redline-cover-mobile.svg"/>
  <img src="docs/yor-redline-cover.svg" width="100%" alt="Project name | YOR REDLINE"/>
</picture>

<sub><strong>YOR / PROJECT DOSSIER</strong> · <a href="https://github.com/yorayriniwnl">GitHub</a> · <a href="https://yorayriniwnl.in">Portfolio</a></sub>

</div>
<!-- END YOR REDLINE -->
```

The actual headers use this contract in a more compact format.

## Editorial contract

1. **One project, one identity.** The cover must name the project accurately; diagrams must reflect the actual domain (for example, graphs, network nodes, solar geometry, security shield, or code editor).
2. **Keep the engineering documentation.** Preserve verified claims, API contracts, setup commands, troubleshooting steps, attribution, licensing, and evidence boundaries. Never replace substantive docs with decorative assets.
3. **State implementation status exactly.** Distinguish live, demo, experimental, research, historical, planning, and empty projects. Do not imply production readiness based on visual quality.
4. **Avoid visual noise.** No gratuitous GIFs, lengthy animated sequences, oversized badge walls, inconsistent typography, or mixed color themes.
5. **Check mobile and desktop.** Confirm both files exist, render, stay legible at narrow viewports, and do not clip text.
6. **Maintain local ownership.** Commit the SVGs inside their corresponding repositories. No runtime dependencies or custom JavaScript are required for README covers.
7. **Use a single cover block.** Keep one `<!-- YOR REDLINE / README COVER V1 -->` block per README to support safe updates. Avoid stacking competing hero banners.

## Repository rollout boundaries

- Profile repository `yorayriniwnl/Yorayriniwnl`: README already has bespoke art direction; preserved.
- Three archived repositories: preserved without modification; GitHub archived repositories are read-only.
- Two formerly empty repositories: given explicitly labeled README placeholders rather than invented features.
- All other active repositories: their original technical content is retained beneath the new responsive cover.

## Future change checklist

- [ ] Verify the project's real status, stack, and purpose from source.
- [ ] Produce project-specific desktop/mobile SVG covers with the brand tokens above.
- [ ] Ensure the README retains real technical documentation.
- [ ] Check images and links on GitHub, not only in local Markdown preview.
- [ ] Verify headings, alt text, and mobile line wrapping.
- [ ] Avoid claiming unmeasured results or production readiness.

Visual consistency is a system, not a collection of identical banners.

## V2: engineering dossier and navigation layer

The completed repository-wide redesign extends the responsive V1 identity with two additional project-specific assets:

- `docs/yor-redline-system.svg` (desktop system map, 1440 × 500)
- `docs/yor-redline-system-mobile.svg` (mobile system map, 720 × 920)

The README includes a single `<!-- YOR REDLINE / EXPERIENCE V2 -->` block before its first existing second-level section. Each V2 block provides:

1. A four-stage conceptual workflow based on the documented scope of that repository, with project-specific labels and illustration.
2. A compact **Project signal / Documented scope** table covering maturity, technical scope, and an explicit evidence boundary.
3. Direct Markdown navigation to the source README's existing technical documentation sections.
4. A responsive `<picture>` element with local SVG paths and descriptive alt text.

Do not turn diagrams into unsourced implementation or performance claims. Research prototypes, historical archives, experiments, and empty repositories should be labeled distinctly. Main technical documentation must remain accessible and unchanged in substance.

### Publication audit (V2)

- **32 repositories discovered** in the linked GitHub account.
- **28 non-profile, unarchived repositories** received the expanded V2 dossier, alongside their original V1 responsive covers. This includes two previously empty repositories that were initialized with honest placeholders.
- **1 canonical profile repository** keeps its existing bespoke README and serves as the design source of truth.
- **3 archived repositories** remain untouched because GitHub treats them as read-only.
- Source-level verification confirmed the README V1/V2 markers, relative image references, and both new system-map SVG assets across all 28 target repositories.
- **Limit of verification:** This does not constitute a complete rendered browser/device screenshot audit, nor does it certify live deployments or tests. A visual QA pass across GitHub desktop and mobile views is recommended after code-level checks.

To revise the design later, update the V2 block and its corresponding local desktop/mobile SVG files together. Do not overwrite sections outside the marked block without independent review.
