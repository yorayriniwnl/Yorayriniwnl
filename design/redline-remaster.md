# Spectrum command deck

The profile is generated from `data/profile.json` by `scripts/generate_readme.py`. `scripts/generate_assets.py` owns the SVG surfaces, `scripts/generate_motion.py` owns the six-world motion reel, and `design/yor-tokens.json` is the visual source of truth.

## Audit findings behind this pass

- The live README used images for nearly all copy. The rendered article had no selectable body text, including project summaries and contact navigation.
- The opening repeated its identity panel, social buttons, proof cards, signal strip, atlas, and project selectors before the first project.
- Most of the 82 referenced visual assets shared the same crimson interface treatment, so the six project worlds did not read as distinct systems.
- GitHub's rendered content column measured about 846 px at desktop width, 308 px in a 390 px viewport, and 238 px in a 320 px viewport. Several 360 px graphics therefore had to shrink sharply on narrow screens.
- The previous local preview used a 742 px wrapper and did not match the live article width.
- The public account sidebar still showed an older availability and location than the canonical README data. Those account settings are outside this repository.

## Current composition

The opening pairs the existing cinematic portrait with plain-text role, positioning, availability, and contact links. A desktop/mobile motion reel follows immediately and has still-image sources for reduced-motion preferences. Six numbered project entries use the original cover artwork, readable summaries, visible stacks and links, and native proof disclosures. Field notes, public activity, and a compact credentials disclosure close the page.

The global crimson frame stays intact. Portfolio, Helios, Zenith, Vision, Talks, and Token Usage now have separate color signatures in the shared project tokens and the motion reel. The Token Usage project points to its own world token rather than borrowing Talks' palette.

## Verification and publication

The normal checks are `python scripts/profile_data.py`, `python scripts/generate_assets.py`, `python scripts/generate_readme.py --check`, `python scripts/generate_motion.py`, and `python -m unittest discover -s tests -v`. Run `scripts/optimize_assets.py` to regenerate image derivatives; it also checks the approved portrait hash.

The GitHub Actions workflow publishes generated SVGs and the `systems-reel*.gif` / `systems-reel*.png` files to the `output` branch. Verify both the source commit and the rendered GitHub profile after publishing. Do not infer live telemetry from the illustrative motion reel; public stats and contribution cards are separately timestamped snapshots.

## Artwork provenance

The existing hero and six project covers remain the supplied artwork. Their source and optimized delivery files are recorded in `data/profile.json`. The six-world reel is generated from code and shared design tokens, with no external media or fonts.
