#!/usr/bin/env python3
"""Load and validate the public profile's canonical factual data."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = ROOT / "data" / "profile.json"
DEFAULT_TOKENS_PATH = ROOT / "design" / "yor-tokens.json"
DEFAULT_AUDIT_PATH = ROOT / "data" / "repo-audit.json"
PHONE_PATTERN = re.compile(r"(?:\+?91[\s.-]?)?[6-9]\d{4}[\s.-]?\d{5}")
REQUIRED_PROJECT_IDS = {"portfolio", "vision", "zenith", "helios", "token-usage", "talks"}
STALE_PUBLIC_CLAIMS = {
    "yorayriniwnl@gmail.com",
    "deep learning",
    "convolutional neural network",
}


class ProfileDataError(ValueError):
    """Raised when canonical profile data violates a publishing contract."""


def load_design_tokens(path: Path = DEFAULT_TOKENS_PATH) -> dict[str, Any]:
    """Load the shared visual contract used by profile asset generation."""
    with path.open(encoding="utf-8") as stream:
        tokens = json.load(stream)
    if tokens.get("schema_version") != 1:
        raise ProfileDataError("unsupported design token schema version")
    return tokens


def load_profile(path: Path = DEFAULT_DATA_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        profile = json.load(stream)
    validate_profile(profile)
    return profile


def load_repository_audit(path: Path = DEFAULT_AUDIT_PATH) -> dict[str, Any]:
    """Load the read-only account inventory that backs public profile curation."""
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def _require(mapping: dict[str, Any], keys: set[str], context: str) -> None:
    missing = sorted(keys - mapping.keys())
    if missing:
        raise ProfileDataError(f"{context} is missing: {', '.join(missing)}")


def _validate_public_content(profile: dict[str, Any]) -> None:
    serialized = json.dumps(profile, ensure_ascii=False).lower()
    if PHONE_PATTERN.search(serialized):
        raise ProfileDataError("public profile data must not contain a phone number")
    for stale_claim in STALE_PUBLIC_CLAIMS:
        if stale_claim in serialized:
            raise ProfileDataError(f"stale public claim found: {stale_claim}")


def _validate_projects(projects: list[dict[str, Any]]) -> None:
    ids = [project.get("id") for project in projects]
    if set(ids) != REQUIRED_PROJECT_IDS or len(ids) != len(set(ids)):
        raise ProfileDataError("project ids must be unique and match the canonical project set")

    repos: set[str] = set()
    orders: set[int] = set()
    required = {"id", "order", "name", "codename", "status", "repo", "summary", "proof", "stack"}
    for project in projects:
        _require(project, required, f"project {project.get('id', '<unknown>')}")
        repo = project["repo"]
        if not repo.startswith("https://github.com/yorayriniwnl/"):
            raise ProfileDataError(f"project repo must use the canonical GitHub account: {repo}")
        if repo.lower() in repos:
            raise ProfileDataError(f"duplicate project repo: {repo}")
        if project["order"] in orders:
            raise ProfileDataError(f"duplicate project order: {project['order']}")
        if not project["proof"] or not project["stack"]:
            raise ProfileDataError(f"project {project['id']} needs proof and stack entries")
        repos.add(repo.lower())
        orders.add(project["order"])


def _validate_hero(profile: dict[str, Any]) -> None:
    contract = profile["visual_contract"]
    _require(
        contract,
        {
            "approved_hero",
            "approved_hero_sha256",
            "optimized_hero",
            "high_resolution",
            "project_art",
            "palette",
            "source",
            "delivery",
            "github_derivative",
        },
        "visual contract",
    )
    hero_path = ROOT / contract["approved_hero"]
    if not hero_path.is_file():
        raise ProfileDataError(f"approved hero is missing: {hero_path}")
    actual = hashlib.sha256(hero_path.read_bytes()).hexdigest()
    if actual != contract["approved_hero_sha256"]:
        raise ProfileDataError("approved hero changed; restore the previous profile portrait")

    source = contract["source"]
    _require(source, {"hero", "flagship_art", "project_art", "supporting_art"}, "source visual contract")
    _require(contract["delivery"], {"hero", "flagship_art", "project_art", "supporting_art"}, "delivery visual contract")
    _require(contract["github_derivative"], {"hero", "project_art"}, "GitHub visual contract")
    if source["hero"] != contract["approved_hero"]:
        raise ProfileDataError("source hero must remain the approved hero")
    if contract["delivery"]["hero"] != contract["optimized_hero"]:
        raise ProfileDataError("delivery hero must match optimized_hero")
    expected_project_art = {"helios", "zenith", "vision", "talks", "token-usage"}
    if set(source["project_art"]) != expected_project_art:
        raise ProfileDataError("source project artwork must match the selected visual project set")
    if set(contract["delivery"]["project_art"]) != expected_project_art:
        raise ProfileDataError("delivery project artwork must match the selected visual project set")
    if set(contract["github_derivative"]["project_art"]) != expected_project_art:
        raise ProfileDataError("GitHub project derivatives must match the selected visual project set")
    for relative_path in (source["hero"], source["flagship_art"], *source["project_art"].values()):
        asset_path = ROOT / relative_path
        if not asset_path.is_file():
            raise ProfileDataError(f"source visual asset is missing: {relative_path}")
    if Path(source["flagship_art"]).suffix.lower() != ".png":
        raise ProfileDataError("source flagship artwork must be a PNG")
    if set(source["supporting_art"]) != {"identity", "atlas", "channel"}:
        raise ProfileDataError("source supporting artwork must cover identity, atlas, and channel")
    if set(contract["delivery"]["supporting_art"]) != {"identity", "atlas", "channel"}:
        raise ProfileDataError("delivery supporting artwork must cover identity, atlas, and channel")
    for relative_path in source["supporting_art"].values():
        asset_path = ROOT / relative_path
        if asset_path.suffix.lower() != ".png" or not asset_path.is_file():
            raise ProfileDataError(f"source supporting visual asset is missing: {relative_path}")

    derivative_paths = [contract["optimized_hero"], contract["delivery"]["flagship_art"], *contract["project_art"].values()]
    if set(contract["project_art"]) != expected_project_art:
        raise ProfileDataError("project artwork must match the selected visual project set")
    for relative_path in derivative_paths:
        asset_path = ROOT / relative_path
        if asset_path.suffix.lower() not in {".jpg", ".jpeg"} or not asset_path.is_file():
            raise ProfileDataError(f"optimized visual asset is missing: {relative_path}")
    if Path(contract["delivery"]["flagship_art"]).suffix.lower() not in {".jpg", ".jpeg"}:
        raise ProfileDataError("delivery flagship artwork must be a JPEG")
    for relative_path in contract["delivery"]["supporting_art"].values():
        asset_path = ROOT / relative_path
        if asset_path.suffix.lower() not in {".jpg", ".jpeg"} or not asset_path.is_file():
            raise ProfileDataError(f"optimized supporting visual asset is missing: {relative_path}")

    if contract["project_art"] != contract["delivery"]["project_art"]:
        raise ProfileDataError("project_art must be the delivery derivative map")
    github_derivatives = [
        contract["github_derivative"]["hero"],
        *contract["github_derivative"]["project_art"].values(),
    ]
    for relative_path in github_derivatives:
        if not relative_path.startswith("output/") or not relative_path.endswith(".svg"):
            raise ProfileDataError(f"GitHub derivative must be a published output SVG: {relative_path}")

    high_resolution = contract["high_resolution"]
    _require(high_resolution, {"hero", "project_art"}, "high-resolution visual contract")
    if set(high_resolution["project_art"]) != expected_project_art:
        raise ProfileDataError("high-resolution project artwork must match the selected visual project set")
    for relative_path in (high_resolution["hero"], *high_resolution["project_art"].values()):
        asset_path = ROOT / relative_path
        if asset_path.suffix.lower() not in {".jpg", ".jpeg"} or not asset_path.is_file():
            raise ProfileDataError(f"high-resolution visual asset is missing: {relative_path}")


def _validate_design_tokens(profile: dict[str, Any]) -> None:
    tokens = load_design_tokens()
    palette = profile["visual_contract"]["palette"]
    expected = {
        "void": tokens["color"]["void"],
        "panel": tokens["color"]["panel"],
        "crimson": tokens["color"]["crimson"],
        "deep_crimson": tokens["color"]["deepCrimson"],
        "signal": tokens["color"]["signal"],
        "paper": tokens["color"]["paper"],
        "muted": tokens["color"]["muted"],
    }
    if palette != expected:
        raise ProfileDataError(
            "visual contract palette must match design/yor-tokens.json"
        )
    required_sections = {"color", "worlds", "gradient", "typography", "geometry", "motion", "signal", "effects", "breakpoints", "accessibility"}
    missing = sorted(required_sections - tokens.keys())
    if missing:
        raise ProfileDataError(f"design token contract is missing: {', '.join(missing)}")
    required_worlds = {"portfolio", "helios", "zenith", "vision", "talks", "token-usage"}
    if set(tokens["worlds"]) != required_worlds:
        raise ProfileDataError("design token worlds must match the six visual systems")
    for world_id, world in tokens["worlds"].items():
        _require(
            world,
            {"label", "canvas", "surface", "surface_alt", "ink", "muted", "accent", "accent_soft", "line", "glow"},
            f"visual world {world_id}",
        )
        if world["accent"] not in {tokens["color"]["crimson"], tokens["color"]["secondaryCrimson"]}:
            raise ProfileDataError(
                f"visual world {world_id} must use a crimson-family accent"
            )
        if world["accent_soft"] != tokens["color"]["signal"]:
            raise ProfileDataError(
                f"visual world {world_id} must use the shared blush signal"
            )


def _validate_repository_audit() -> None:
    audit = load_repository_audit()
    _require(
        audit,
        {
            "schema_version",
            "account",
            "reviewed_on",
            "repository_count_expected",
            "repository_count_audited",
            "missing_local_clones",
            "proposed_pins",
            "repositories",
        },
        "repository audit",
    )
    if audit["schema_version"] != 1:
        raise ProfileDataError("unsupported repository audit schema version")
    if audit["account"] != "yorayriniwnl":
        raise ProfileDataError("repository audit account must be yorayriniwnl")

    repositories = audit["repositories"]
    names = [item.get("name") for item in repositories]
    expected_count = audit["repository_count_expected"]
    if expected_count != 25 or audit["repository_count_audited"] != expected_count:
        raise ProfileDataError("repository audit must cover the 25-repository public scope")
    if len(names) != expected_count or len(set(names)) != expected_count:
        raise ProfileDataError("repository audit must contain unique repository names")
    if audit["missing_local_clones"]:
        raise ProfileDataError("repository audit has missing local clones")
    if not all(item.get("public") is True for item in repositories):
        raise ProfileDataError("repository audit scope must contain only public repositories")

    pin_names = [item.get("name") for item in audit["proposed_pins"]]
    if pin_names != [
        "Yor-Ayrin-iwnl",
        "yor-talksv2",
        "Yor-Helios",
        "Yor-Zenith",
        "Yor-Ai-vs-real-image",
        "Hyperliquid_Analysis",
    ]:
        raise ProfileDataError("repository audit proposed pins changed unexpectedly")
    if not set(pin_names).issubset(names):
        raise ProfileDataError("repository audit proposed pins must exist in the audited set")


def validate_profile(profile: dict[str, Any]) -> None:
    _require(
        profile,
        {
            "schema_version",
            "identity",
            "contact",
            "availability",
            "proof",
            "experience",
            "education",
            "certifications",
            "achievements",
            "skills",
            "projects",
            "visual_contract",
        },
        "profile",
    )
    if profile["schema_version"] != 1:
        raise ProfileDataError("unsupported profile schema version")

    _require(profile["identity"], {"name", "handle", "role", "specialty", "positioning", "location"}, "identity")
    _require(profile["contact"], {"email", "portfolio", "github", "linkedin", "devpost", "steam"}, "contact")
    if profile["identity"]["name"] != "Ayush Roy":
        raise ProfileDataError("canonical public name must remain Ayush Roy")
    if profile["contact"]["email"] != "ayushroy.dev@gmail.com":
        raise ProfileDataError("canonical public email must be ayushroy.dev@gmail.com")

    proof_ids = {item.get("id") for item in profile["proof"]}
    if proof_ids != {"apps", "tests", "accuracy", "prototypes"}:
        raise ProfileDataError("proof metrics must include apps, tests, accuracy, and prototypes")

    _validate_projects(profile["projects"])
    _validate_public_content(profile)
    _validate_design_tokens(profile)
    _validate_repository_audit()
    _validate_hero(profile)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH)
    args = parser.parse_args()
    profile = load_profile(args.data)
    print(
        f"profile data valid: {profile['identity']['name']} | "
        f"{len(profile['projects'])} projects | {len(profile['proof'])} proof metrics"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
