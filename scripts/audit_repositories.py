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
        "pin_priority": 3,
    },
    "Yor-Helios": {
        "classification": "flagship-realtime",
        "status": "IN_DEVELOPMENT",
        "intent": "Realtime energy telemetry and operator dashboard system under active development.",
        "pin_priority": 4,
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
        "pin_priority": None,
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
        "pin_priority": 5,
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
        "pin_priority": 6,
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