#!/usr/bin/env python3
"""
audit_batch_a.py — mechanical corrections from POL_Content_Audit_2026-06-10.md (Batch A).

Dry-run by default: prints every planned change and every flag, writes nothing.
Run with --write to apply. Self-verifying: any file that would still contain a
must-eliminate pattern after replacement is NOT written and is reported as an
anomaly. Line endings and encoding are preserved byte-for-byte outside the
replaced spans.

Usage (from repo root):
    python scripts/audit_batch_a.py            # dry run
    python scripts/audit_batch_a.py --write    # apply

Delete this script once Batch A is merged (single-use, per workspace convention).
"""

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# ── Replacement rules ────────────────────────────────────────────────────────
# (id, literal_old, new, scope_prefix or None, expected_min, expected_max)
RULES = [
    # GENIUS Act year + effective date (signed 2025-07-18; effective 2027-01-18)
    ("genius-year-paren", "GENIUS Act (2024)", "GENIUS Act (2025)", None, 1, 12),
    ("genius-year-bare",  "GENIUS Act 2024",   "GENIUS Act 2025",   None, 0, 12),
    ("genius-effective-1", "in force August 4, 2025", "effective January 18, 2027", None, 1, 8),
    ("genius-effective-2", "entered into force on August 4, 2025",
     "take effect on January 18, 2027", None, 0, 4),
    # RTP cap: $1M from Apr 2022, $10M since Feb 9, 2025
    ("rtp-limit-1", "$1M limit (raised Feb 2024)", "$10M limit (raised February 2025)", None, 0, 4),
    ("rtp-limit-2", "$1M cap since Feb 2024",      "$10M cap since February 2025",      None, 0, 4),
    ("rtp-limit-3", "$1M cap from February 2024",  "$10M cap since February 2025",      None, 0, 4),
    ("rtp-limit-4", "RTP cap $1M",                 "RTP cap $10M",                      None, 0, 4),
    # Fedwire ISO 20022 go-live was July 14, 2025 (not March)
    ("fedwire-date", "FedWire ISO 20022 migration (Mar 2025)",
     "FedWire ISO 20022 migration (Jul 2025)", None, 0, 4),
    # AP2 → Policy Mandate (in-house schema; AP2 is Google's protocol, v0.2/FIDO)
    ("ap2-stable", "AP2 v1.0 stable", "Policy Mandate v1", None, 0, 12),
    ("ap2-v1",     "AP2 v1.0",        "Policy Mandate v1", None, 10, 140),
    ("anthropic-attr", "Anthropic / Google AP2 working draft",
     "Google AP2 working draft (v0.2 · FIDO Alliance)", None, 0, 3),
    ("builtfor-agentic",
     "Built for Anthropic, Google AP2, OpenAI, Vellum, LangChain",
     "For teams working with Google AP2, OpenAI, Vellum, LangChain and other agentic runtimes",
     None, 0, 3),
    # Canonical tool count: 400+
    ("count-259-tool", "259-tool", "400+ tool", None, 0, 10),
    ("count-259",      "259 tools", "400+ tools", None, 0, 10),
    ("count-260-tool", "260-tool", "400+ tool", None, 0, 10),
    ("count-260plus",  "260+ tools", "400+ tools", None, 0, 10),
    ("count-268",      "268 tools", "400+ tools", None, 0, 12),
    ("count-100plus",  "100+ fintech tools", "400+ fintech tools", None, 0, 6),
    # Demo CTA credibility line (decision 1/5: advisory framing, global)
    ("cta-cred-line",
     "Post Oak Labs · production deployments in the Caribbean &amp; South Asia · works with a limited number of institutions at a time",
     "Post Oak Labs · advisory on production tokenized payment deployments · emerging and frontier markets worldwide",
     "demos", 30, 50),
    # Honest review stamp (these pages were reviewed in this audit)
    ("last-reviewed", "Last Reviewed · 2026-05-13", "Last Reviewed · 2026-06-10", None, 0, 20),
]

# Context-gated rule: 2024/1624 → 2023/1113 only where the line is about the
# TFR/travel rule. 2024/1624 is the AMLR and is CORRECT in AMLR contexts.
TFR_OLD, TFR_NEW = "2024/1624", "2023/1113"
TFR_YES = re.compile(r"TFR|Transfer of Funds|travel rule", re.IGNORECASE)
TFR_NO = re.compile(r"AMLR|1620|Anti-Money Laundering Regulation", re.IGNORECASE)

# Must not survive in any written file (anomaly → file skipped, reported)
MUST_ELIMINATE = [
    "GENIUS Act (2024)", "GENIUS Act 2024", "AP2 v1.0",
    "raised Feb 2024", "Last Reviewed · 2026-05-13", "YOUR_FORM_ID",
    "in force August 4, 2025",
]

# Flag-only: report for Batch B manual handling, change nothing
FLAGS = [
    ("flag-aug4-leftover", re.compile(r"August 4, 2025")),
    ("flag-tfr-ambiguous", re.compile(r"2024/1624")),  # post-replacement leftovers
    ("flag-ap2-residual", re.compile(r"(?<!Google )(?<!google-)AP2[ -](?:mandate|JSON|schema|export|v\d|stable)", re.IGNORECASE)),
    ("flag-builtfor", re.compile(r"Built for [A-Z]")),
    ("flag-fednow-500k", re.compile(r"FedNow[^\n]{0,80}\$500", re.IGNORECASE)),
    ("flag-deploy-claim", re.compile(r"production deployments in the Caribbean", re.IGNORECASE)),
    ("flag-count-residual", re.compile(r"\b(?:259|260|268)\b[^\n]{0,30}(?:tool|scenario)", re.IGNORECASE)),
    ("flag-scarcity", re.compile(r"limited number of institutions")),
]
FLAG_EXEMPT = {"contact.html", "index.html"}  # scarcity line allowed here

TARGET_GLOBS = ["*.html", "demos/**/*.html", "llms.txt", "README.md"]
SKIP_PARTS = {".git", ".github", "scripts"}


def target_files():
    seen = set()
    for g in TARGET_GLOBS:
        for p in sorted(REPO.glob(g)):
            if p.is_file() and not (set(p.relative_to(REPO).parts) & SKIP_PARTS):
                seen.add(p)
    return sorted(seen)


def apply_tfr(text):
    """Line-gated TFR regulation-number fix. Returns (new_text, n_replaced)."""
    out, n = [], 0
    for line in text.splitlines(keepends=True):
        if TFR_OLD in line and TFR_YES.search(line) and not TFR_NO.search(line):
            c = line.count(TFR_OLD)
            line = line.replace(TFR_OLD, TFR_NEW)
            n += c
        out.append(line)
    return "".join(out), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="apply changes (default: dry run)")
    args = ap.parse_args()

    rule_totals = {rid: 0 for rid, *_ in RULES}
    rule_totals["tfr-gated"] = 0
    anomalies, flags_report, changed_files = [], [], []

    for path in target_files():
        rel = path.relative_to(REPO).as_posix()
        raw = path.read_text(encoding="utf-8", newline="")
        text = raw

        per_file = []
        for rid, old, new, scope, *_ in RULES:
            if scope and not rel.startswith(scope + "/"):
                continue
            c = text.count(old)
            if c:
                text = text.replace(old, new)
                rule_totals[rid] += c
                per_file.append(f"{rid}×{c}")

        text, c = apply_tfr(text)
        if c:
            rule_totals["tfr-gated"] += c
            per_file.append(f"tfr-gated×{c}")

        # Self-verification: refuse files that still contain must-eliminate patterns
        leftovers = [p for p in MUST_ELIMINATE if p in text]
        if leftovers and per_file:
            anomalies.append((rel, leftovers))
            print(f"ANOMALY  {rel}: would still contain {leftovers} — NOT writing")
            continue
        if leftovers:
            anomalies.append((rel, leftovers))
            print(f"ANOMALY  {rel}: contains {leftovers}, no rule matched — needs manual fix")
            continue

        # Flag-only patterns (on post-replacement text)
        for fid, rx in FLAGS:
            if fid == "flag-scarcity" and path.name in FLAG_EXEMPT:
                continue
            for m in rx.finditer(text):
                ln = text.count("\n", 0, m.start()) + 1
                flags_report.append(f"{fid:22s} {rel}:{ln}  …{m.group(0)[:70]}")

        if text != raw:
            changed_files.append((rel, per_file))
            if args.write:
                path.write_text(text, encoding="utf-8", newline="")

    mode = "WRITE" if args.write else "DRY RUN"
    print(f"\n── {mode} summary ──────────────────────────────────────────")
    for rel, per in changed_files:
        print(f"  {rel}: {', '.join(per)}")
    print(f"\nFiles changed: {len(changed_files)}   Anomalies: {len(anomalies)}")
    print("\nPer-rule totals (expected ranges):")
    for rid, _, _, _, lo, hi in RULES:
        n = rule_totals[rid]
        ok = "OK " if lo <= n <= hi else "OUT"
        print(f"  [{ok}] {rid:20s} {n}  (expect {lo}–{hi})")
    print(f"  [   ] {'tfr-gated':20s} {rule_totals['tfr-gated']}")

    if flags_report:
        print(f"\nFlag-only findings for Batch B ({len(flags_report)}):")
        for f in flags_report:
            print("  " + f)

    out_of_range = [rid for rid, _, _, _, lo, hi in RULES
                    if not lo <= rule_totals[rid] <= hi]
    if out_of_range:
        print(f"\nWARNING: rules out of expected range: {out_of_range}")
        print("Review the dry-run output before --write.")
    if anomalies:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
