#!/usr/bin/env python3
"""
audit_batch_a.py — mechanical corrections from POL_Content_Audit_2026-06-10.md (Batch A).

Dry-run by default: prints every planned change and every flag, writes nothing.
Run with --write to apply. Self-verifying: any file that still contains a
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
# (id, literal_old, new, scope_prefix_or_None, expected_min, expected_max)
# scope: None = all files; "demos" = demos/ subtree only; exact paths unsupported —
#        use precise old strings to limit matches naturally.
RULES = [

    # ── 1. GENIUS Act year (signed 2025-07-18; effective 2027-01-18) ─────────
    # Mins set to 0: most have been applied manually; script will still fix any
    # remaining instances found during the run.
    ("genius-year-paren", "GENIUS Act (2024)", "GENIUS Act (2025)", None, 0, 8),
    ("genius-year-bare",  "GENIUS Act 2024",   "GENIUS Act 2025",   None, 0, 8),

    # ── 2. GENIUS Act effective date — a2a-comparison.html ───────────────────
    ("genius-eff-a2a",
     "entering into force on August 4, 2025 "
     "(the July 18 date is the signing date; August 4 is the effective date; "
     "source: Congress.gov)",
     "taking effect on January 18, 2027 "
     "(July 18, 2025 is the signing date; January 18, 2027 is the effective date; "
     "source: Congress.gov)",
     None, 0, 1),

    # ── 3. GENIUS Act effective date — glossary.html ─────────────────────────
    ("genius-eff-gloss",
     "entering into force on August 4, 2025 "
     "(the July 18 date refers to signing; August 4 is the effective date; "
     "source: Congress.gov / White House signing statement)",
     "taking effect on January 18, 2027 "
     "(July 18, 2025 is the signing date; January 18, 2027 is the effective date; "
     "source: Congress.gov / White House signing statement)",
     None, 0, 1),

    # ── 4. RTP cap cite date ──────────────────────────────────────────────────
    ("rtp-cite",
     "TCH RTP rulebook (Feb 2024 cap)",
     "TCH RTP rulebook (Feb 2025 — $10M cap)",
     None, 0, 1),

    # ── 5. NACHA same-day ACH cap date ───────────────────────────────────────
    ("nacha-cap",
     "NACHA same-day cap $1M (2024)",
     "NACHA same-day cap $1M (eff. Mar 2022)",
     None, 0, 1),

    # ── 6. AP2 terminal animation schema identifiers ──────────────────────────
    ("ap2-schema-id",
     "ap2-v1.0",
     "policy-mandate-v1",
     None, 0, 6),

    # ── 7. AP2 FAQ description (demos/index.html JSON-LD × HTML = 2 hits) ─────
    ("ap2-faq-text",
     "AP2 (Agent Payments Protocol) v1.0 is a schema for expressing payment and "
     "policy mandates that AI agents can execute deterministically. Each scenario "
     "can export its result as an Policy Mandate v1 mandate, so the output can be "
     "replayed by an agent runtime or reviewed by an audit team.",
     "AP2 is Google’s Agent Payments Protocol (v0.2.0, FIDO Alliance), a "
     "standard for expressing payment policies that AI agents can execute. Each "
     "scenario exports its result as a Policy Mandate (schema: "
     "@postoaklabs.com/policy-mandate-v1) so the output can be consumed by "
     "AP2-capable agents, replayed by an agent runtime, or reviewed by an audit team.",
     None, 0, 2),

    # ── 8. West Africa CTA: remove DCash interop claim ───────────────────────
    ("west-africa-dcash",
     "eNaira, cNGN, and DCash interoperability is live infrastructure, not a concept. "
     "If you’re a commercial bank, central bank, or fintech evaluating West Africa "
     "corridor strategy, let’s talk specifics.",
     "West Africa’s digital payment landscape is rapidly evolving — eNaira, "
     "cNGN, and regional interoperability frameworks are advancing. If you’re a "
     "commercial bank, central bank, or fintech evaluating West Africa corridor strategy, "
     "let’s talk specifics.",
     None, 0, 1),

    # ── 9. West Africa CTA heading ────────────────────────────────────────────
    ("west-africa-heading",
     "We’ve built tokenised payment rails across frontier corridors.",
     "We’ve advised on tokenised payment rail implementations across frontier corridors.",
     None, 0, 1),

    # ── 10. West Africa footer ────────────────────────────────────────────────
    ("deploy-westafr-footer",
     "Post Oak Labs · production deployments in the Caribbean &amp; South Asia "
     "· ECOWAS / WAEMU corridor advisory",
     "Post Oak Labs · advisory on production tokenized payment deployments "
     "· ECOWAS / WAEMU corridor advisory",
     None, 0, 1),

    # ── 11. mBridge footer ────────────────────────────────────────────────────
    ("deploy-mbridge-footer",
     "Post Oak Labs · CBDC advisory for central banks and commercial banks "
     "· Caribbean &amp; South Asia deployments",
     "Post Oak Labs · CBDC advisory for central banks and commercial banks "
     "· frontier market experience",
     None, 0, 1),

    # ── 12. "we’ve built tokenized rails in the Caribbean and South Asia" ──────
    ("deploy-built-rails",
     "we’ve built tokenized rails in the Caribbean and South Asia. Let’s talk.",
     "we’ve advised on tokenized rail implementations across frontier markets. "
     "Let’s talk.",
     None, 0, 5),

    # ── 13. demos/index.html: "production deployments in the Caribbean and South Asia" ──
    ("deploy-demos-index",
     "with production deployments in the Caribbean and South Asia.",
     "with advisory on production deployments across frontier markets.",
     None, 0, 2),

    # ── 14. a2a-comparison.html CTA (HTML data-i18n + i18n JSON = ×2) ─────────
    ("deploy-a2a-comp-cta",
     "We have built production systems in the Caribbean and South Asia. "
     "We know what works.",
     "We have advised on and supported production deployments across frontier markets. "
     "We know what works.",
     None, 0, 2),

    # ── 15. a2a-comparison.html table cell ────────────────────────────────────
    ("deploy-a2a-comp-table",
     "where Post Oak Labs has deployed production infrastructure",
     "where Post Oak Labs has advised on production infrastructure deployments",
     None, 0, 1),

    # ── 16. a2a-payments.html: OG + Twitter meta (×2) ────────────────────────
    ("deploy-a2a-pay-meta",
     "Active deployments in the Caribbean and South Asia.",
     "Frontier market advisory across the Caribbean, South Asia, and Latin America.",
     None, 0, 2),

    # ── 17. a2a-payments.html: JSON-LD description ────────────────────────────
    ("deploy-a2a-pay-jsonld",
     "Post Oak Labs has deployed production systems in the Caribbean and South Asia.",
     "Post Oak Labs has advised on and supported production deployments across frontier markets.",
     None, 0, 1),

    # ── 18. a2a-payments.html: hero-sub (HTML + i18n EN = ×2) ─────────────────
    ("deploy-a2a-pay-herosub",
     "Our team has built production systems in this space",
     "Our team has direct production experience in this space",
     None, 0, 2),

    # ── 19. a2a-payments.html: <h4>Production deployments active</h4> ─────────
    ("deploy-a2a-pay-h4",
     "<h4>Production deployments active</h4>",
     "<h4>Production deployment advisory</h4>",
     None, 0, 1),

    # ── 20. a2a-workflow.html: meta description ───────────────────────────────
    ("deploy-a2a-wf-meta",
     "Post Oak Labs has built production systems at this layer.",
     "Post Oak Labs has advised on and supported production deployments at this layer.",
     None, 0, 1),

    # ── 21. a2a-workflow.html: CTA paragraph ──────────────────────────────────
    ("deploy-a2a-wf-cta",
     "We have built production systems. We know what works and what doesn’t.",
     "We have advised on and supported production deployments. "
     "We know what works and what doesn’t.",
     None, 0, 1),

    # ── 22. index.html: meta description ──────────────────────────────────────
    ("deploy-idx-meta",
     "Production deployments in the Caribbean and South Asia. "
     "Focused on Latin America, Africa, and emerging markets.",
     "Frontier market focus: Latin America, Africa, the Caribbean, and South Asia.",
     None, 0, 1),

    # ── 23. index.html: hero-sub (HTML + i18n EN = ×2) ────────────────────────
    ("deploy-idx-herosub",
     "Production deployments in the Caribbean and South Asia; "
     "primary focus on Latin America and Africa.",
     "Primary focus on Latin America, Africa, the Caribbean, and South Asia.",
     None, 0, 2),

    # ── 24. index.html: stat-1 label (HTML + i18n = ×2) ──────────────────────
    ("deploy-idx-stat1",
     "Regions · active deployments",
     "Regions · active advisory",
     None, 0, 2),

    # ── 25. index.html: stat-2 label (HTML + i18n = ×2) ──────────────────────
    ("deploy-idx-stat2",
     "Systems live · Caribbean & South Asia",
     "Active advisory · frontier markets",
     None, 0, 2),

    # ── 26. index.html: svc1-p (HTML + i18n EN = ×2) ─────────────────────────
    ("deploy-idx-svc1p",
     "We have built and integrated production systems in the Caribbean and South Asia. "
     "This is infrastructure work, not just advisory.",
     "We have advised on and supported production deployments across frontier markets.",
     None, 0, 2),

    # ── 27. index.html: track-p HTML version ──────────────────────────────────
    ("deploy-idx-trackp-html",
     "Team members have built and deployed production tokenized payment systems in "
     "the Caribbean and South Asia: live systems, not pilots.",
     "Team members bring direct production experience from tokenized payment deployments "
     "across frontier markets.",
     None, 0, 1),

    # ── 28. index.html: track-p i18n EN version ───────────────────────────────
    ("deploy-idx-trackp-i18n",
     "Team members have built and deployed production tokenized payment systems in "
     "the Caribbean and South Asia.",
     "Team members bring direct production experience from tokenized payment deployments "
     "across frontier markets.",
     None, 0, 1),

    # ── 29. index.html: reg4-p (HTML + i18n EN = ×2) ─────────────────────────
    ("deploy-idx-reg4p",
     "Production tokenized payment systems deployed in South Asia.",
     "South Asia is a key focus region for tokenized payment infrastructure advisory.",
     None, 0, 2),

    # ── 30. "Built for <strong>" strips in demo hub files (×5) ───────────────
    ("builtfor-strip",
     "Built for <strong>",
     "For teams working with <strong>",
     "demos", 0, 6),

    # ── 31. audienceType: agentic-runtime hub ─────────────────────────────────
    ("audience-agentic",
     "\"audienceType\": \"Agent runtime engineering — Anthropic, Google AP2, OpenAI function-calling, Vellum, LangChain\"",
     "\"audienceType\": \"Agent runtime engineering teams working with Anthropic, Google AP2, OpenAI function-calling, Vellum, LangChain\"",
     None, 0, 1),

    # ── 32. audienceType: baas hub ────────────────────────────────────────────
    ("audience-baas",
     "\"audienceType\": \"BaaS platforms — Unit, Synctera, Treasury Prime, Marqeta, Galileo\"",
     "\"audienceType\": \"Teams working with BaaS platforms including Unit, Synctera, Treasury Prime, Marqeta, Galileo\"",
     None, 0, 1),

    # ── 33. audienceType: processors hub ─────────────────────────────────────
    ("audience-processors",
     "\"audienceType\": \"Payment processors — Stripe Compliance, Adyen, Worldpay, Checkout.com\"",
     "\"audienceType\": \"Teams working with payment processors including Stripe Compliance, Adyen, Worldpay, Checkout.com\"",
     None, 0, 1),

    # ── 34. audienceType: regtech hub ─────────────────────────────────────────
    ("audience-regtech",
     "\"audienceType\": \"RegTech operators — ComplyAdvantage, Sumsub, Hummingbird, Unit21, ThetaRay\"",
     "\"audienceType\": \"Teams working with RegTech platforms including ComplyAdvantage, Sumsub, Hummingbird, Unit21, ThetaRay\"",
     None, 0, 1),

    # ── 35. audienceType: stablecoin-issuer hub ───────────────────────────────
    ("audience-stablecoin",
     "\"audienceType\": \"Stablecoin issuers — Paxos, Circle, Bridge (post-Stripe), Anchorage\"",
     "\"audienceType\": \"Teams working with stablecoin issuers including Paxos, Circle, Bridge (post-Stripe), Anchorage\"",
     None, 0, 1),

    # ── 36. ap2_version field rename → schema_version ────────────────────────
    # The Policy Mandate JSON field ‘ap2_version’ implies Google AP2 versioning
    # (currently v0.2.0). Rename to ‘schema_version’ to clarify it’s the Policy
    # Mandate schema version (v1), not Google AP2’s version number.
    # Covers: JS object literals, JSON in placeholders, validator comparisons,
    # property accesses (m.ap2_version), and error message strings.
    # Scoped to demos/ — top-level pages don’t emit Policy Mandate JSON.
    ("ap2ver-field",
     "ap2_version",
     "schema_version",
     "demos", 0, 80),

    # ── 37. index.html: reg3-p Caribbean card text (HTML + i18n EN = ×2) ─────
    # Decision §9.1: reword to "advisory on production deployments"
    ("deploy-idx-reg3p",
     "We have active production deployments in the Caribbean region. "
     "Our familiarity with the regulatory environment, correspondent banking "
     "constraints, and the specific remittance dynamics of this region is direct.",
     "We have advised on production deployments in the Caribbean region. "
     "Our familiarity with the regulatory environment, correspondent banking "
     "constraints, and the specific remittance dynamics of this region is direct.",
     None, 0, 2),

    # ── 38. index.html: reg3-lbl + reg4-lbl card labels (HTML + i18n = ×4) ───
    # Both Caribbean and South Asia cards use this label text.
    ("deploy-idx-reg-lbl",
     "Active · Production Deployments",
     "Advisory · Production Deployments",
     None, 0, 4),
]

# ── Context-gated rule: EU TFR 2024/1624 → 2023/1113 ────────────────────────
# 2024/1624 is the AMLR and is CORRECT in AMLR contexts — only fix TFR refs.
TFR_OLD, TFR_NEW = "2024/1624", "2023/1113"
TFR_YES = re.compile(r"TFR|Transfer of Funds|travel rule", re.IGNORECASE)
TFR_NO  = re.compile(r"AMLR|1620|Anti-Money Laundering Regulation", re.IGNORECASE)

# ── Must not survive in any written file (anomaly → file skipped, reported) ──
MUST_ELIMINATE = [
    "GENIUS Act (2024)",
    "GENIUS Act 2024",
    "August 4, 2025",          # catches any remaining GENIUS effective-date errors
    "TCH RTP rulebook (Feb 2024 cap)",
    "NACHA same-day cap $1M (2024)",
    "ap2-v1.0",
]

# ── Flag-only: report for Batch B manual handling, change nothing ─────────────
FLAGS = [
    ("flag-ap2-v1-residual",   re.compile(r"AP2 v1\.0",  re.IGNORECASE)),
    ("flag-ap2-residual",      re.compile(
        r"(?<![Gg]oogle\s)(?<!google-)AP2\s(?:mandate|JSON|schema|export|stable)",
        re.IGNORECASE)),
    ("flag-builtfor",          re.compile(r"Built for [A-Z]")),
    ("flag-deploy-carib",      re.compile(r"(?:built|deployed|live)\b[^\n]{0,60}"
                                           r"Caribbean", re.IGNORECASE)),
    ("flag-fednow-500k",       re.compile(r"FedNow[^\n]{0,80}\$500", re.IGNORECASE)),
    ("flag-count-residual",    re.compile(
        r"\b(?:259|260|268)\b[^\n]{0,30}(?:tool|scenario)", re.IGNORECASE)),
    ("flag-tfr-ambiguous",     re.compile(r"2024/1624")),  # post-TFR-rule leftovers
    ("flag-aug4-residual",     re.compile(r"August 4,\s*2025")),
]
# "limited number of institutions" is intentional on these pages; don't flag
FLAG_EXEMPT_SCARCITY = {"contact.html", "a2a-engagement-roadmap.html", "index.html"}

TARGET_GLOBS = ["*.html", "demos/**/*.html", "llms.txt", "README.md"]
SKIP_PARTS   = {".git", ".github", "scripts"}


def target_files():
    seen = set()
    for g in TARGET_GLOBS:
        for p in sorted(REPO.glob(g)):
            if p.is_file() and not (set(p.relative_to(REPO).parts) & SKIP_PARTS):
                seen.add(p)
    return sorted(seen)


# Apostrophe variants — chr() calls are unambiguous in any editor
_APOS_STRAIGHT = chr(0x0027)   # U+0027  straight apostrophe
_APOS_CURLY    = chr(0x2019)   # U+2019  right single quotation mark (curly)


def _apos_variants(s):
    """Yield s with straight apostrophes, then curly, skipping duplicates."""
    straight = s.replace(_APOS_CURLY, _APOS_STRAIGHT)
    curly    = s.replace(_APOS_STRAIGHT, _APOS_CURLY)
    seen = set()
    for v in (s, straight, curly):
        if v not in seen:
            seen.add(v)
            yield v


def smart_replace(text, old, new):
    """Replace old→new, trying straight and curly apostrophe variants if needed."""
    for variant in _apos_variants(old):
        c = text.count(variant)
        if c:
            return text.replace(variant, new), c
    return text, 0


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
    ap.add_argument("--write", action="store_true",
                    help="apply changes (default: dry run)")
    args = ap.parse_args()

    rule_totals  = {rid: 0 for rid, *_ in RULES}
    rule_totals["tfr-gated"] = 0
    anomalies, flags_report, changed_files = [], [], []

    for path in target_files():
        rel  = path.relative_to(REPO).as_posix()
        raw  = path.read_text(encoding="utf-8", newline="")
        text = raw

        per_file = []
        for rid, old, new, scope, *_ in RULES:
            if scope and not rel.startswith(scope + "/"):
                continue
            text, c = smart_replace(text, old, new)
            if c:
                rule_totals[rid] += c
                per_file.append(f"{rid}×{c}")

        text, c = apply_tfr(text)
        if c:
            rule_totals["tfr-gated"] += c
            per_file.append(f"tfr-gated×{c}")

        # Self-verification: refuse files that still contain must-eliminate patterns
        leftovers = [p for p in MUST_ELIMINATE
                     if any(v in text for v in _apos_variants(p))]
        if leftovers and per_file:
            anomalies.append((rel, leftovers))
            print(f"ANOMALY  {rel}: would still contain {leftovers} — NOT writing")
            continue
        if leftovers:
            anomalies.append((rel, leftovers))
            print(f"ANOMALY  {rel}: contains {leftovers}, no rule matched "
                  f"— needs manual fix")
            continue

        # Flag-only patterns (on post-replacement text)
        stem = path.name
        for fid, rx in FLAGS:
            if fid == "flag-deploy-carib" and stem in FLAG_EXEMPT_SCARCITY:
                continue
            for m in rx.finditer(text):
                ln = text.count("\n", 0, m.start()) + 1
                flags_report.append(
                    f"{fid:28s} {rel}:{ln}  …{m.group(0)[:70]}")

        if text != raw:
            changed_files.append((rel, per_file))
            if args.write:
                path.write_text(text, encoding="utf-8", newline="")

    mode = "WRITE" if args.write else "DRY RUN"
    print(f"\n── {mode} summary "
          f"───────────────────────────")
    for rel, per in changed_files:
        print(f"  {rel}: {', '.join(per)}")
    print(f"\nFiles changed: {len(changed_files)}   Anomalies: {len(anomalies)}")

    print("\nPer-rule totals (expected ranges):")
    for rid, _, _, _, lo, hi in RULES:
        n  = rule_totals[rid]
        ok = "OK " if lo <= n <= hi else "OUT"
        print(f"  [{ok}] {rid:28s} {n:3d}  (expect {lo}–{hi})")
    print(f"  [   ] {'tfr-gated':28s} {rule_totals['tfr-gated']:3d}")

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
