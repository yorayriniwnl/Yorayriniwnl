# Crimson profile remaster

The public composition is rendered by `scripts/redline.py`, with links and native disclosures in `scripts/generate_readme.py`. Canonical facts and artwork ownership stay in `data/profile.json`.

## Art direction

Black and saturated crimson, editorial serif headings, restrained interface glyphs, larger body text, and a slim moving edge. The six project covers and approved portrait remain byte-identical to their previous generated versions. New mobile layouts compose text at a 360px natural width instead of shrinking desktop text.

Project summaries introduce the idea. Their native disclosures contain the full evidence, stack, and source links. Six visual selectors jump directly to the projects. The existing six-world motion reel is inside the field manual, with mobile and reduced-motion posters.

GitHub sanitizes authored anchor IDs with a `user-content-` prefix. Shortcut URLs target that rendered ID; browser checks verify the destination's viewport position, not just the URL hash. Compact 145px controls fit two columns in GitHub's mobile README content area.

## Artwork provenance

Mode: built-in image-generation tool; new generation, not a portrait edit.

Selected source: `assets/crimson-studio-v1.png`.
Delivery: `assets/crimson-studio-v1-optimized.jpg` (1200 × 675, JPEG).
Use: the desktop and mobile identity panels. This is illustrative studio artwork, not a photograph of the owner's actual equipment.

Final prompt:

> undefined

## Verification and publication

Run `python scripts/profile_data.py`, `python scripts/generate_assets.py`, `python scripts/generate_readme.py --check`, and `python -m unittest discover -s tests -v`. `scripts/optimize_assets.py` produces deterministic image derivatives and checks the approved portrait hash.

Browser QA covered 1280px, 390px, and 320px widths: no horizontal overflow, missing images, or out-of-bounds text; all seven disclosures open; project selectors resolve; reduced-motion visitors receive still posters. Local preview evidence lives in ignored `tmp/redline-audit.json` and `tmp/redline-*.png`.

Public stats show their successful fetch time. The contribution card names its exact date range; both mobile and desktop retain every daily count. Language shares use all fetched code bytes in the denominator and do not imply skill proficiency. Incomplete language fetches stop publication.

Publish source to main and the generated SVGs to a detached worktree based on origin/output. Preserve the existing motion files and the public resume. Independently verify both remote SHAs and the actual GitHub README render.

At this remaster, GitHub Actions reported an account billing lock. Assets and fresh public snapshots are published directly; scheduled refreshes require that GitHub account issue to be resolved.
