#!/usr/bin/env python3
"""
POL copy-hallmarks gate — anti-AI-tell linter for reader-facing site copy.

PROVENANCE / LINEAGE
--------------------
INTERIM, POL-LOCAL implementation. Built 2026-07-23 from the ANTI-AI-TELL
copy ban (CLAUDE.md, 2026-07-11). This is NOT the canonical AINumbers
`copy-hallmarks` script. Per the single-lineage rule, when AINumbers lands
its canonical gate (COPY-GATE-2), VENDOR that script here with a provenance
header and DELETE this interim file. Do not fork/extend both in parallel.

WHAT IT CHECKS (reader-facing visible text only; <script>/<style>/<head>/
comments are stripped before analysis)
  ERROR  (exit 1 — blocks push/deploy):
    - two-tone contrast: "not just X but Y" / "not only" / "isn't just"
    - validation phrasing: "you're not alone"
    - dramatic fragment: "The result?" and kin
    - filler vocab: delve, tapestry, testament to, seamless(ly),
      game-changer, "it's worth noting", "in today's fast-paced"
    - emoji in headings or prose (real pictographs only)
  WARN   (exit 0 — reported, non-blocking for now):
    - italics <em>/<i>: the ban targets italics-FOR-EMPHASIS, but a linter
      cannot separate those from legitimate structural markup (glossary
      headwords, first-use technical terms). Reported for editorial review;
      remove emphasis-italics by hand, keep term-markup.
    - em-dash (—) in prose  [2000+ legacy separators; triage separately]
    - soft filler: elevate, unlock, quietly  [false-positive prone]

USAGE
  python scripts/copy-hallmarks.py              # scan default page set
  python scripts/copy-hallmarks.py a.html b.html # scan specific files
  --warn-only   report everything but always exit 0

Exit 1 if any ERROR-tier hit is found; 0 otherwise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Directories never scanned (not reader-facing site copy).
SKIP_DIRS = {".git", ".github", "node_modules", "scripts", "_archive"}

# Files that are crawler/machine hints, not reader-facing prose — exempt.
SKIP_FILES = {"llms.txt", "llms-full.txt"}

# Known pending, deliberately not blocking — each is a real issue with an open
# content/design decision. Resolve it, then delete the entry. Mirrors
# check-links.py's KNOWN_PENDING pattern.
PENDING_FILES = set()  # empty — tools.html retired (301 → ainumbers.co) 2026-07-23

# ── strip regions that are not prose ─────────────────────────────────
RE_SCRIPT = re.compile(r"<script\b[^>]*>.*?</script>", re.I | re.S)
RE_STYLE = re.compile(r"<style\b[^>]*>.*?</style>", re.I | re.S)
RE_HEAD = re.compile(r"<head\b[^>]*>.*?</head>", re.I | re.S)
RE_COMMENT = re.compile(r"<!--.*?-->", re.S)
RE_TAG = re.compile(r"<[^>]+>")

# ── ERROR-tier patterns (visible text unless noted) ──────────────────
RE_EM_TAG = re.compile(r"<(em|i)(\s[^>]*)?>", re.I)  # runs on body HTML, not text
# Real pictographic emoji only. Typographic arrows (→ ↗), check/cross
# dingbats (✓ ✗), and · separators are NOT emoji and must not be flagged.
EMOJI = re.compile(
    "[" "\U0001F000-\U0001FAFF" "\U00002600-\U000026FF" "]"
    "\U0000FE0F?",
)
# Non-emoji symbol glyphs used as UI controls (not prose): ☰ menu toggle.
ALLOWED_GLYPHS = {"☰"}

ERROR_TEXT = [
    ("two-tone-contrast", re.compile(r"\bnot just\b", re.I)),
    ("two-tone-contrast", re.compile(r"\bnot only\b", re.I)),
    ("two-tone-contrast", re.compile(r"\bisn'?t just\b", re.I)),
    ("two-tone-contrast", re.compile(r"\brather than just\b", re.I)),
    ("validation-phrasing", re.compile(r"\byou'?re not alone\b", re.I)),
    ("validation-phrasing", re.compile(r"\byou are not alone\b", re.I)),
    ("dramatic-fragment", re.compile(
        r"\bThe (result|catch|kicker|upshot|twist|reason|difference)\?")),
    ("filler-vocab", re.compile(r"\bdelve\b", re.I)),
    ("filler-vocab", re.compile(r"\btapestry\b", re.I)),
    ("filler-vocab", re.compile(r"\btestament to\b", re.I)),
    ("filler-vocab", re.compile(r"\bseamless(ly)?\b", re.I)),
    ("filler-vocab", re.compile(r"\bgame[- ]changer\b", re.I)),
    ("filler-vocab", re.compile(r"\bit'?s worth noting\b", re.I)),
    ("filler-vocab", re.compile(r"in today'?s fast-paced", re.I)),
]

# ── WARN-tier patterns ───────────────────────────────────────────────
WARN_TEXT = [
    ("em-dash", re.compile(r"—")),
    ("soft-filler", re.compile(r"\belevate\b", re.I)),
    ("soft-filler", re.compile(r"\bunlock\b", re.I)),
    ("soft-filler", re.compile(r"\bquietly\b", re.I)),
]


def prose(html: str) -> str:
    """Strip non-prose regions, then all tags → visible text."""
    for rx in (RE_COMMENT, RE_SCRIPT, RE_STYLE, RE_HEAD):
        html = rx.sub(" ", html)
    return RE_TAG.sub(" ", html)


def body_html(html: str) -> str:
    """HTML with script/style/head/comments removed but tags intact."""
    for rx in (RE_COMMENT, RE_SCRIPT, RE_STYLE, RE_HEAD):
        html = rx.sub(" ", html)
    return html


def default_files():
    files = []
    for p in REPO_ROOT.rglob("*.html"):
        parts = p.relative_to(REPO_ROOT).parts
        if any(part in SKIP_DIRS for part in parts):
            continue
        if p.name in SKIP_FILES:
            continue
        files.append(p)
    return sorted(files)


def scan(path: Path):
    """Return (errors, warns) as lists of (category, snippet)."""
    html = path.read_text(encoding="utf-8", errors="ignore")
    text = prose(html)
    bhtml = body_html(html)
    errors, warns = [], []

    for cat, rx in ERROR_TEXT:
        for m in rx.finditer(text):
            errors.append((cat, _ctx(text, m)))
    for m in EMOJI.finditer(text):
        if m.group(0).rstrip("️") in ALLOWED_GLYPHS:
            continue
        errors.append(("emoji-in-prose", repr(m.group(0))))

    for m in RE_EM_TAG.finditer(bhtml):
        warns.append(("italics", m.group(0)))
    for cat, rx in WARN_TEXT:
        for m in rx.finditer(text):
            warns.append((cat, _ctx(text, m)))
    return errors, warns


def _ctx(text: str, m, span: int = 32) -> str:
    a = max(0, m.start() - span)
    b = min(len(text), m.end() + span)
    return " ".join(text[a:b].split())


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows console is cp1252
    except Exception:
        pass
    warn_only = "--warn-only" in argv
    argv = [a for a in argv if not a.startswith("--")]
    files = [Path(a).resolve() for a in argv] if argv else default_files()

    total_err = total_warn = total_pending = 0
    for f in files:
        errors, warns = scan(f)
        pending = f.name in PENDING_FILES
        if pending:
            total_pending += len(errors)
        else:
            total_err += len(errors)
        total_warn += len(warns)
        if errors or warns:
            rel = f.relative_to(REPO_ROOT) if str(f).startswith(str(REPO_ROOT)) else f
            print(f"\n{rel}" + ("  [PENDING — not blocking]" if pending else ""))
            tag = "pend " if pending else "ERROR"
            for cat, snip in errors:
                print(f"  {tag}  [{cat}] {snip}")
            for cat, snip in warns:
                print(f"  warn   [{cat}] {snip}")

    print(f"\nScanned {len(files)} files — {total_err} error(s), "
          f"{total_pending} pending, {total_warn} warn(s).")
    if total_err and not warn_only:
        print("Copy-hallmarks gate FAILED. Fix ERROR-tier hits before pushing.")
        return 1
    print("Copy-hallmarks gate OK (no blocking hits).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
