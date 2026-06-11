#!/usr/bin/env python3
"""audit_batch_b_quick.py — dry-run by default.
python scripts/audit_batch_b_quick.py --write  to apply changes.

Fixes:
  demos/vasp-travel-rule-compliance-checker.html : EU 2024/1624 -> 2023/1113 (TFR, 4 hits)
  sitemap.html  : 268-tool -> 400+-tool (1 hit)
  tools.html    : 268 references -> 400+ (4 hits)
  faq.html      : production-deployment claims -> advisory language (6 hits)
  llms.txt      : production-deployment claims -> advisory language (4 hits)
"""

import sys
from pathlib import Path

WRITE = "--write" in sys.argv
REPO  = Path(__file__).resolve().parent.parent

# ── apostrophe-agnostic helpers ──────────────────────────────────────────────

_APOS_STRAIGHT = chr(0x0027)   # U+0027  '
_APOS_CURLY    = chr(0x2019)   # U+2019  ’

def _apos_variants(s):
    yield s
    if _APOS_STRAIGHT in s:
        yield s.replace(_APOS_STRAIGHT, _APOS_CURLY)
    if _APOS_CURLY in s:
        yield s.replace(_APOS_CURLY, _APOS_STRAIGHT)

def smart_replace(text, old, new):
    for variant in _apos_variants(old):
        c = text.count(variant)
        if c:
            return text.replace(variant, new), c
    return text, 0


# ── rules ────────────────────────────────────────────────────────────────────
# (rule_id, old, new, file_path_relative_to_REPO, min_expected, max_expected)

RULES = [
    # ── vasp: EU TFR mislabelled as 2024/1624 -> correct 2023/1113 ──────

    ("vasp-tfr-keywords",
     "EU Transfer of Funds Regulation, EU 2024/1624, FinCEN",
     "EU Transfer of Funds Regulation (EU) 2023/1113, FinCEN",
     "demos/vasp-travel-rule-compliance-checker.html", 1, 1),

    ("vasp-tfr-hero",
     "(Regulation 2024/1624, applicable from <b>30 December 2024</b>)",
     "(Regulation (EU) 2023/1113, applicable from <b>30 December 2024</b>)",
     "demos/vasp-travel-rule-compliance-checker.html", 1, 1),

    ("vasp-tfr-callout",
     "(Regulation (EU) 2024/1624, applicable from 30 December 2024)",
     "(Regulation (EU) 2023/1113, applicable from 30 December 2024)",
     "demos/vasp-travel-rule-compliance-checker.html", 1, 1),

    ("vasp-tfr-cite",
     "EU 2024/1624 Art. 14, 18",
     "EU 2023/1113 Art. 14, 18",
     "demos/vasp-travel-rule-compliance-checker.html", 1, 1),

    # ── sitemap: tool count ──────────────────────────────────────────────

    ("sitemap-count",
     "268-tool AINumbers.co catalog",
     "400+-tool AINumbers.co catalog",
     "sitemap.html", 1, 1),

    # ── tools.html: 268 -> 400+ (4 hits) ────────────────────────────────

    ("tools-meta-desc",
     "plus the full 268-tool catalog at AINumbers.co",
     "plus the full 400+-tool catalog at AINumbers.co",
     "tools.html", 1, 1),

    ("tools-hero-sub",
     "a 268-tool intelligence catalog",
     "a 400+-tool intelligence catalog",
     "tools.html", 1, 1),

    ("tools-stat-num",
     '<span class="stat-num">268</span>',
     '<span class="stat-num">400+</span>',
     "tools.html", 1, 1),

    ("tools-dest-desc",
     "The complete 268-tool fintech intelligence library",
     "The complete 400+-tool fintech intelligence library",
     "tools.html", 1, 1),

    # ── faq.html: production-deployment claims -> advisory language ───────
    # Hits JSON-LD (line 76) AND visible text (line 923) — both have the
    # same prefix before <strong>Caribbean</strong> vs plain "Caribbean".

    ("faq-carib-deploy",
     "the firm has active production deployments in the ",
     "the firm has active advisory and integration engagements in the ",
     "faq.html", 2, 2),

    # JSON-LD cost-competitiveness answer (no <strong> tags inside JSON string)
    ("faq-cost-jsonld",
     "Post Oak Labs' production deployments demonstrate approximately 0.2% in direct settlement fees in selected B2B corridors where Post Oak Labs has advised on production infrastructure deployments",
     "Post Oak Labs' corridor analysis demonstrates approximately 0.2% in direct settlement fees in selected B2B corridors where Post Oak Labs has advised on infrastructure design",
     "faq.html", 1, 1),

    # Visible-text cost-competitiveness answer (has <strong> tags)
    ("faq-cost-html",
     "Post Oak Labs' production deployments demonstrate approximately <strong>0.2% in direct settlement fees</strong> in selected B2B corridors where Post Oak Labs has advised on production infrastructure deployments",
     "Post Oak Labs' corridor analysis demonstrates approximately <strong>0.2% in direct settlement fees</strong> in selected B2B corridors where Post Oak Labs has advised on infrastructure design",
     "faq.html", 1, 1),

    # JSON-LD integration timeline — "Post Oak Labs production deployments" (no apostrophe)
    ("faq-integration-jsonld",
     "Integration timeline in Post Oak Labs production deployments has ranged",
     "Integration timeline in Post Oak Labs advisory engagements has ranged",
     "faq.html", 1, 1),

    # Visible-text integration timeline — "Post Oak Labs' production deployments" (apostrophe)
    ("faq-integration-html",
     "Integration timeline in Post Oak Labs' production deployments has ranged",
     "Integration timeline in Post Oak Labs' advisory engagements has ranged",
     "faq.html", 1, 1),

    # ── llms.txt: production-deployment claims -> advisory language ───────

    ("llms-built-integrated",
     "Post Oak Labs has built and integrated production tokenized payment systems in the Caribbean and South Asia. This is implementation experience, not only advisory.",
     "Post Oak Labs has deep advisory and integration experience in tokenized payment systems, with active engagements in the Caribbean and South Asia.",
     "llms.txt", 1, 1),

    ("llms-prod-deploy-kd",
     "Post Oak Labs has production deployments of tokenized payment systems, not only advisory experience. Systems are live in the Caribbean and South Asia.",
     "Post Oak Labs brings hands-on advisory and integration experience in tokenized payment systems — not only theoretical — with active engagements in the Caribbean and South Asia.",
     "llms.txt", 1, 1),

    ("llms-built-production",
     "Post Oak Labs has built production systems in the Caribbean and South Asia.",
     "Post Oak Labs has advised on and integrated tokenized payment systems in the Caribbean and South Asia.",
     "llms.txt", 1, 1),

    ("llms-firm-deployments",
     "The firm has production deployments in the Caribbean and South Asia. This is a meaningful differentiator vs. advisory-only competitors and should be referenced where relevant.",
     "The firm has active advisory and integration engagements in the Caribbean and South Asia. This is a meaningful differentiator vs. advisory-only competitors and should be referenced where relevant.",
     "llms.txt", 1, 1),
]


# After --write: none of these patterns should remain in the named file.
MUST_BE_GONE = [
    ("demos/vasp-travel-rule-compliance-checker.html", "2024/1624"),
    ("sitemap.html",  "268-tool"),
    ("tools.html",    "268-tool"),
    ("tools.html",    ">268<"),
    ("faq.html",      "active production deployments in the"),
    ("faq.html",      "production deployments demonstrate"),
    ("faq.html",      "production deployments has ranged"),
    ("llms.txt",      "built and integrated production tokenized"),
    ("llms.txt",      "production deployments of tokenized"),
    ("llms.txt",      "built production systems"),
    ("llms.txt",      "firm has production deployments"),
]


# ── run ──────────────────────────────────────────────────────────────────────

def run():
    # Pre-load all target files into a mutable cache so rules compose correctly.
    file_cache = {}
    for _, _, _, rel_path, _, _ in RULES:
        target = REPO / rel_path
        if target not in file_cache:
            file_cache[target] = target.read_text(encoding="utf-8") if target.exists() else None

    out_of_range = []
    total_changes = 0
    changed_files = set()

    for rule_id, old, new, rel_path, lo, hi in RULES:
        target = REPO / rel_path
        text = file_cache.get(target)
        if text is None:
            print(f"  MISSING   [{rule_id}]  {rel_path}")
            out_of_range.append(rule_id)
            continue
        new_text, count = smart_replace(text, old, new)
        ok = lo <= count <= hi
        if count > 0:
            file_cache[target] = new_text
            changed_files.add(target)
            total_changes += count
        print(f"  {'OK  ' if ok else 'WARN'} x{count}  [{rule_id}]  {rel_path}")
        if not ok:
            out_of_range.append(rule_id)

    if out_of_range:
        print(f"\nWARNING: rules out of expected range: {out_of_range}")
        print("Review the dry-run output before --write.")

    if WRITE:
        for path in changed_files:
            path.write_text(file_cache[path], encoding="utf-8")
        print(f"\nWrote {len(changed_files)} file(s), {total_changes} change(s).")

        # Self-verify: re-read from disk and confirm patterns are gone.
        failures = []
        for rel_path, pattern in MUST_BE_GONE:
            text = (REPO / rel_path).read_text(encoding="utf-8")
            if pattern in text:
                failures.append(f"  STILL PRESENT  {rel_path!r}: {pattern!r}")
        if failures:
            print("VERIFY FAILED:")
            for f in failures:
                print(f)
        else:
            print("Verify OK — all MUST_BE_GONE patterns absent.")
    else:
        print(f"\nDRY RUN — {total_changes} change(s) pending. Pass --write to apply.")


if __name__ == "__main__":
    run()
