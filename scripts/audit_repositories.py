#!/usr/bin/env python3
"""Build a read-only, evidence-first audit of the account's public repositories.

The scanner intentionally records counts, paths, and claims to review without
copying suspected secrets or private file contents into the public profile.
Run it against a directory of local clones so every finding can be reproduced
without trusting README prose alone.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any


OWNER = "yorayriniwnl"
DEFAULT_REPOSITORIES = (
    "Yor-Solar-Nexus",
    "mentor-mentee-system",
    "Yor-Zenith",
    "Yor-Ai-vs-real-image",
    "Yor-Ayrin-iwnl",
    "Yor-Helios",
    "Yor-Feelings",
    "Yorayriniwnl",
    "Yor-Status",
    "Yor-Talks",
    "Eat-a-lot",
    "Yorayriniwnl.in",
    "CBSE-Result-Analyzer",
    "Trading_Bot",
    "Taskflow",
    "Hyperliquid_Analysis",
    "Yor_Token_Usage",
    "Yor-Project-Health-Tracker",
    "Yor-Store",
    "Landgrabbers_2",
    "yorayriniwnl.in2",
    "yor-stories",
    "yor-story",
    "yor-talksv2",
    "Portfolio-Ayush-Roy",
    "CandidateX",
    "Hybrid-Intelligent-Network-Intrusion-Detection-System",
    "Yor-World",
)

REPO_OVERRIDES: dict[str, dict[str, Any]] = {
    "Yorayriniwnl": {
        "classification": "profile",
        "status": "VERIFIED",
        "intent": "Account home: generated profile, public proof, and the visual system source.",
        "pin_priority": None,
    },
    "yor-talksv2": {
        "classification": "flagship-full-stack",
        "status": "DEMO",
        "intent": "Primary full-stack realtime communication system; public beta evidence is documented, launch gates remain visible.",
        "pin_priority": 2,
    },
    "Yor-Helios": {
        "classification": "flagship-realtime",
        "status": "IN_DEVELOPMENT",
        "intent": "Realtime energy telemetry and operator dashboard system under active development.",
        "pin_priority": 3,
    },
    "Yor-Talks": {
        "classification": "legacy-product",
        "status": "ARCHIVE_CANDIDATE",
        "intent": "Legacy communication predecessor; retain history and explain its relationship to V2.",
        "pin_priority": None,
    },
    "Hyperliquid_Analysis": {
        "classification": "flagship-research",
        "status": "VERIFIED",
        "intent": "Evidence-first quantitative research dossier over preserved assignment exports.",
        "pin_priority": 6,
    },
    "C_PlusPlus": {
        "classification": "learning-log",
        "status": "LEARNING",
        "intent": "Small C++ learning log; intentionally modest and not presented as a flagship product.",
        "pin_priority": None,
    },
    "Yor-Feelings": {
        "classification": "experimental-interface",
        "status": "EXPERIMENTAL",
        "intent": "Mood-responsive interaction experiment; identity and privacy boundaries need clear documentation.",
        "pin_priority": None,
    },
    "yor-stories": {
        "classification": "empty-shell",
        "status": "ARCHIVE_CANDIDATE",
        "intent": "Empty public shell; do not leave unexplained in the final public catalog.",
        "pin_priority": None,
    },
    "yorayriniwnl.in2": {
        "classification": "legacy-portfolio",
        "status": "ARCHIVE_CANDIDATE",
        "intent": "Older portfolio candidate; compare against the focused portfolio and field hub before any archive action.",
        "pin_priority": None,
    },
    "Yorayriniwnl.in": {
        "classification": "field-hub",
        "status": "REPORTED",
        "intent": "Broader field hub distinct from the focused portfolio; relationship and outbound links need verification.",
        "pin_priority": None,
    },
    "Yor-Status": {
        "classification": "experimental-civic",
        "status": "EXPERIMENTAL",
        "intent": "Civic accountability prototype; preserve methodology and provenance rather than unsupported scale language.",
        "pin_priority": None,
    },
    "Landgrabbers_2": {
        "classification": "empty-shell",
        "status": "ARCHIVE_CANDIDATE",
        "intent": "Empty public shell; hold for explicit archive/private/delete decision.",
        "pin_priority": None,
    },
    "yor-story": {
        "classification": "writing-broadcast",
        "status": "EXPERIMENTAL",
        "intent": "ON AIR writing/broadcast archive with draft gating; preserve the authored aesthetic and writing boundary.",
        "pin_priority": None,
    },
    "CBSE-Result-Analyzer": {
        "classification": "data-tool",
        "status": "DEMO",
        "intent": "Educational data-transformation tool across CLI, Flask, and Streamlit entry points.",
        "pin_priority": None,
    },
    "Yor-Solar-Nexus": {
        "classification": "superseded-concept",
        "status": "ARCHIVE_CANDIDATE",
        "intent": "Conceptual solar predecessor; compare against Zenith and preserve attribution if superseded.",
        "pin_priority": None,
    },
    "mentor-mentee-system": {
        "classification": "platform",
        "status": "DEMO",
        "intent": "Mentor/mentee matching platform with a documented scoring and matching flow.",
        "pin_priority": None,
    },
    "Yor-Store": {
        "classification": "scraping-product",
        "status": "DEMO",
        "intent": "Grocery price comparison prototype; integration scope and scraper durability need explicit limits.",
        "pin_priority": None,
    },
    "Yor-Zenith": {
        "classification": "flagship-product",
        "status": "DEMO",
        "intent": "Solar decision-support product with 3D planning and financial modeling; preserve contribution attribution.",
        "pin_priority": 4,
    },
    "Yor-Project-Health-Tracker": {
        "classification": "admin-scaffold",
        "status": "DEMO",
        "intent": "Health-tracking scaffold; distinguish seeded/demo data from production claims and never publish reusable credentials.",
        "pin_priority": None,
    },
    "Yor-Ai-vs-real-image": {
        "classification": "flagship-ml",
        "status": "DEMO",
        "intent": "Classical texture-feature image classifier with held-out evaluation; document dataset and inference limits.",
        "pin_priority": 5,
    },
    "Yor-Ayrin-iwnl": {
        "classification": "legacy-portfolio",
        "status": "LEGACY",
        "intent": "Former portfolio implementation retained for historical context; the canonical recruiter-facing source is Portfolio-Ayush-Roy.",
        "pin_priority": None,
    },
    "Eat-a-lot": {
        "classification": "demo-product",
        "status": "DEMO",
        "intent": "Food ordering/product prototype; document SQLite durability, seeded accounts, and hosted-runtime boundaries.",
        "pin_priority": None,
    },
    "Trading_Bot": {
        "classification": "systems-experiment",
        "status": "EXPERIMENTAL",
        "intent": "Binance Futures Testnet execution experiment; no live trading or profit claims.",
        "pin_priority": None,
    },
    "Taskflow": {
        "classification": "engineering-submission",
        "status": "DEMO",
        "intent": "Backend-focused internship assignment and workflow app; preserve assignment provenance.",
        "pin_priority": None,
    },
    "Yor_Token_Usage": {
        "classification": "browser-extension",
        "status": "EXPERIMENTAL",
        "intent": "Chrome MV3 multi-AI usage cockpit; permission, storage, privacy, and clear-data behavior need a dedicated README.",
        "pin_priority": None,
    },,
    "Portfolio-Ayush-Roy": {
        "classification": "flagship-portfolio",
        "status": "VERIFIED",
        "intent": "Canonical recruiter-facing portfolio with evidence-backed case studies and browser QA.",
        "pin_priority": 1,
    },
    "CandidateX": {
        "classification": "flagship-research",
        "status": "RESEARCH_DEMO",
        "intent": "Evidence-first candidate capability research system with explicit synthetic-data and decision-support boundaries.",
        "pin_priority": 2,
    },
    "Hybrid-Intelligent-Network-Intrusion-Detection-System": {
        "classification": "academic-ml-security",
        "status": "RESEARCH_DEMO",
        "intent": "Hybrid NIDS major-project prototype with bounded held-out-category experiments and explainability evidence.",
        "pin_priority": None,
    },
    "Yor-World": {
        "classification": "production-planning-workspace",
        "status": "IN_DEVELOPMENT",
        "intent": "Evidence-heavy planning and feasibility workspace for the next interactive portfolio generation.",
        "pin_priority": None,
    }
}

TEXT_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".css",
    ".csv",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".scss",
    ".sh",
    ".sql",
    ".svg",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
PLACEHOLDER_PATTERNS = {
    "replace-marker": re.compile(r"REPLACE_WITH|YOUR_(?:API|URL|KEY)|TODO|TBD|lorem ipsum|coming soon|placeholder", re.I),
    "example-domain": re.compile(r"(?:https?://)?(?:www\.)?example\.com", re.I),
}
HYPE_PATTERNS = {
    "valuation-language": re.compile(r"billion dollar|unicorn|valuation|million-dollar", re.I),
    "unsupported-scale": re.compile(r"India['’]s\s+#?1|production[- ]ready|production[- ]grade|enterprise\s+v\d", re.I),
}
SENSITIVE_PATTERNS = {
    "private-key-marker": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "credential-assignment": re.compile(r"\b(?:password|passwd|secret|api[_ -]?key)\s*[:=]", re.I),
}
MANIFEST_NAMES = {
    "package.json",
    "pnpm-workspace.yaml",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "vercel.json",
    "vite.config.ts",
    "vite.config.js",
    "next.config.js",
    "next.config.mjs",
}


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip()


def api_catalog() -> dict[str, dict[str, Any]]:
    url = f"https://api.github.com/users/{OWNER}/repos?per_page=100&sort=updated"
    request = urllib.request.Request(url, headers={"User-Agent": "yorayriniwnl-repository-audit/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return {}
    return {item["name"]: item for item in payload if item.get("name")}


def tracked_files(repo: Path) -> list[Path]:
    output = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo,
        check=False,
        capture_output=True,
    ).stdout
    return [repo / Path(raw.decode("utf-8", errors="replace")) for raw in output.split(b"\0") if raw]


def scan_text(path: Path) -> list[str]:
    if path.suffix.lower() not in TEXT_SUFFIXES or path.stat().st_size > 2_000_000:
        return []
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []


def scan_patterns(files: list[Path], patterns: dict[str, re.Pattern[str]], root: Path) -> dict[str, Any]:
    counts = {name: 0 for name in patterns}
    paths: set[str] = set()
    for path in files:
        lines = scan_text(path)
        if not lines:
            continue
        text = "\n".join(lines)
        matched = False
        for name, pattern in patterns.items():
            hits = len(pattern.findall(text))
            counts[name] += hits
            matched = matched or hits > 0
        if matched:
            paths.add(relative(path, root))
    return {"counts": counts, "paths": sorted(paths)[:40], "total": sum(counts.values())}


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def audit_repository(repo: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    files = tracked_files(repo)
    sizes = sorted(
        ((path.stat().st_size, relative(path, repo)) for path in files if path.is_file()),
        reverse=True,
    )
    readmes = [relative(path, repo) for path in files if path.name.lower().startswith("readme")]
    manifests = [relative(path, repo) for path in files if path.name in MANIFEST_NAMES]
    ci = [relative(path, repo) for path in files if ".github/workflows/" in relative(path, repo)]
    tests = [
        relative(path, repo)
        for path in files
        if re.search(r"(?:^|/)(?:tests?|__tests__|spec)(?:/|$)|(?:test|spec)[_-].*\.(?:py|js|ts|tsx)$", relative(path, repo), re.I)
    ]
    overrides = REPO_OVERRIDES.get(repo.name, {})
    return {
        "name": repo.name,
        "public": True,
        "classification": overrides.get("classification", "unclassified"),
        "status": overrides.get("status", "REVIEW"),
        "intent": overrides.get("intent", "Needs manual intent statement."),
        "pin_priority": overrides.get("pin_priority"),
        "github": {
            "description": metadata.get("description"),
            "homepage": metadata.get("homepage"),
            "topics": metadata.get("topics", []),
            "language": metadata.get("language"),
            "default_branch": metadata.get("default_branch"),
            "archived": metadata.get("archived"),
            "fork": metadata.get("fork"),
            "updated_at": metadata.get("updated_at"),
            "pushed_at": metadata.get("pushed_at"),
        },
        "git": {
            "head": run_git(repo, "rev-parse", "HEAD"),
            "head_subject": run_git(repo, "log", "-1", "--format=%s"),
            "branch": run_git(repo, "branch", "--show-current"),
            "remote": run_git(repo, "remote", "get-url", "origin"),
            "shallow": (repo / ".git" / "shallow").is_file(),
        },
        "checks": {
            "tracked_file_count": len(files),
            "tracked_bytes": sum(size for size, _ in sizes),
            "readme_files": readmes,
            "manifest_files": manifests,
            "ci_workflows": ci,
            "test_files": tests[:80],
            "largest_files": [{"path": path, "bytes": size} for size, path in sizes[:8]],
            "empty_repository": len(files) == 0,
            "large_artifact_paths": [path for size, path in sizes if size >= 10_000_000][:30],
            "placeholder_scan": scan_patterns(files, PLACEHOLDER_PATTERNS, repo),
            "hype_scan": scan_patterns(files, HYPE_PATTERNS, repo),
            "sensitive_literal_scan": scan_patterns(files, SENSITIVE_PATTERNS, repo),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos-root", type=Path, required=True, help="Directory containing one local clone per public repository")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review-date", default=str(date.today()))
    parser.add_argument("--offline", action="store_true", help="Skip the public GitHub metadata request")
    args = parser.parse_args()

    metadata = {} if args.offline else api_catalog()
    repositories = []
    missing = []
    for name in DEFAULT_REPOSITORIES:
        repo = args.repos_root / name
        if not repo.is_dir():
            missing.append(name)
            continue
        repositories.append(audit_repository(repo, metadata.get(name, {})))

    proposed_pins = [
        {"name": repo["name"], "reason": repo["intent"]}
        for repo in sorted(repositories, key=lambda item: item.get("pin_priority") or 999)
        if repo.get("pin_priority")
    ]
    result = {
        "schema_version": 1,
        "account": OWNER,
        "reviewed_on": args.review_date,
        "scope": "Public repositories returned by the GitHub user API and checked out locally; no destructive actions performed.",
        "repository_count_expected": len(DEFAULT_REPOSITORIES),
        "repository_count_audited": len(repositories),
        "missing_local_clones": missing,
        "proposed_pins": proposed_pins,
        "repositories": repositories,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"audited {len(repositories)}/{len(DEFAULT_REPOSITORIES)} repositories -> {args.output}")
    if missing:
        print(f"missing local clones: {', '.join(missing)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())