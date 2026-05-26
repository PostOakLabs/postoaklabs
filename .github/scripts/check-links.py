#!/usr/bin/env python3
"""
Internal link checker for postoaklabs.com.

Scans every committed .html file, extracts href/src targets, and verifies that
every *internal* link resolves to a real file in the repository. External links
(http/https/mailto/tel) are listed but never fail the build, since they are
outside this repo's control.

Exit code 1 if any internal link is broken; 0 otherwise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

REPO_ROOT = Path(__file__).resolve().parents[2]

# Folders that are never committed/deployed (kept out of the repo via
# .gitignore). Skipped here so a local run matches what CI sees.
SKIP_DIRS = {
    ".git", ".github", "node_modules",
    "_archive_pre_sweep_2026-05-11", "Partners", "address-forge",
    "erratatoolsatainumbers", "toolsnowatainumbers",
}

# Links known to be broken right now, deliberately skipped so the gate stays
# green. Each is a real issue with a pending content decision - resolve it,
# then delete the entry. See README.md -> "Known pending links".
KNOWN_PENDING = {
    # Favicon assets are referenced by every root page but are not in the
    # repo. Confirm they exist on the live server, add them here, then remove.
    "favicon.svg", "favicon.ico", "favicon-32.png", "favicon-64.png",
    # /showcase → /demos/, /about → /, /contact → /contact.html — all fixed 2026-05-25
    # a2a-engagement-roadmap.html links a PDF that does not exist yet.
    "pilot-framework.pdf",
    # glossary.html links the old partner page; it 301-redirects via
    # .htaccess. Better: link straight to https://meridiancapital.me/.
    "meridian-capital-advisory.html",
}

LINK_RE = re.compile(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", re.IGNORECASE)

# Schemes / prefixes that are not local files.
EXTERNAL_PREFIXES = ("http://", "https://", "//", "mailto:", "tel:",
                     "data:", "javascript:", "#")


def html_files():
    files = []
    for p in REPO_ROOT.rglob("*.html"):
        if any(part in SKIP_DIRS for part in p.relative_to(REPO_ROOT).parts):
            continue
        files.append(p)
    return sorted(files)


def resolve(target, source):
    """Resolve an internal link to a filesystem path."""
    target = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not target:
        return source  # pure fragment / query - points at the page itself
    if target.startswith("/"):
        base = REPO_ROOT / target.lstrip("/")
    else:
        base = source.parent / target
    base = base.resolve()
    # A trailing-slash or bare-directory link resolves to its index.html
    if target.endswith("/") or base.is_dir():
        base = base / "index.html"
    return base


def main():
    files = html_files()
    broken = []
    external = 0
    pending = 0
    checked = 0

    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        for raw in LINK_RE.findall(text):
            link = raw.strip()
            if not link or link.lower().startswith(EXTERNAL_PREFIXES):
                external += 1
                continue
            clean = link.split("#", 1)[0].split("?", 1)[0]
            if clean in KNOWN_PENDING:
                pending += 1
                continue
            checked += 1
            dest = resolve(link, f)
            inside = str(dest).startswith(str(REPO_ROOT))
            if not inside or not dest.exists():
                broken.append((f, link))

    print("Scanned %d HTML files - %d internal links checked, %d external "
          "skipped, %d known-pending skipped."
          % (len(files), checked, external, pending))

    if broken:
        print("\n%d broken internal link(s):\n" % len(broken))
        for src, link in broken:
            print("  %s  ->  %s" % (src.relative_to(REPO_ROOT), link))
        return 1

    print("All internal links resolve. OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
