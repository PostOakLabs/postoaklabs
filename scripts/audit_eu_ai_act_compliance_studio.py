#!/usr/bin/env python3
"""audit_eu_ai_act_compliance_studio.py — dry-run by default.
python scripts/audit_eu_ai_act_compliance_studio.py --write  to apply.

Fixes for demos/eu-ai-act-compliance-studio.html:
  - SYS_PROFILES deadlines: all Annex III items say '2 August 2027'; correct to '2 August 2026'
    (hero already correctly says 'August 2026 readiness' — inconsistency in JS profiles)
  - Gap analysis dates: 'August 2027' / 'Aug 2027' references -> 'August 2026'
  - GPAI date in gap analysis: '2 August 2026 for GPAI' -> '2 August 2025 for GPAI'
  - Timeline steps: 'Aug 2026: GPAI obligations effective' -> 'Aug 2026: Annex III deadline'
                    'Aug 2027: Full Annex III compliance deadline' -> 'Aug 2027: Annex I product-embedded deadline'
  - Insurance underwriting: annexRef §5(b) -> §5(c)
  - Fraud/AML: add §5(b) statutory exception note
"""

import sys
from pathlib import Path

WRITE = "--write" in sys.argv
REPO  = Path(__file__).resolve().parent.parent
FILE  = "demos/eu-ai-act-compliance-studio.html"

_APOS_STRAIGHT = chr(0x0027)
_APOS_CURLY    = chr(0x2019)

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


RULES = [

    # ── SYS_PROFILES: all Annex III deadlines 2027 -> 2026 ───────────────
    # Chatbot (limited risk) already has '2 August 2026' — don't touch.
    # All high-risk Annex III entries have '2 August 2027' — change to 2026.
    ("profiles-annex3-deadlines",
     "deadline:'2 August 2027'",
     "deadline:'2 August 2026'",
     5, 8),   # credit, fraud, aml, underwriting, kyc, kycscore = 6 entries

    # ── Classification corrections ────────────────────────────────────────
    # Insurance underwriting: §5(b) -> §5(c)
    ("ins-underwriting-annexref",
     "underwriting: { risk:'high', annexRef:'Annex III §5(b)', articleRef:'Article 6(2)', deadline:'2 August 2026', label:'Insurance Underwriting & Pricing'",
     "underwriting: { risk:'high', annexRef:'Annex III §5(c)', articleRef:'Article 6(2)', deadline:'2 August 2026', label:'Insurance Underwriting & Pricing'",
     1, 1),

    # Fraud: add note about §5(b) exception (update annexRef)
    ("fraud-annexref",
     "fraud:        { risk:'high', annexRef:'Annex III §5(b)', articleRef:'Article 6(2)', deadline:'2 August 2026', label:'Fraud Detection — Automated Account Block'",
     "fraud:        { risk:'high', annexRef:'Annex III — §5(b) excepts fraud detection', articleRef:'Article 6(2)', deadline:'2 August 2026', label:'Fraud Detection — Automated Account Block'",
     1, 1),

    # AML: add note about §5(b) exception
    ("aml-annexref",
     "aml:          { risk:'high', annexRef:'Annex III §5(b)', articleRef:'Article 6(2)', deadline:'2 August 2026', label:'AML / Transaction Monitoring (Automated Restriction)'",
     "aml:          { risk:'high', annexRef:'Annex III — §5(b) excepts AML/fraud detection', articleRef:'Article 6(2)', deadline:'2 August 2026', label:'AML / Transaction Monitoring (Automated Restriction)'",
     1, 1),

    # ── Gap analysis text ─────────────────────────────────────────────────
    # GPAI date in Art. 9 gap item
    ("gap-gpai-date",
     "Art. 9 risk management system framework required before 2 August 2026 for GPAI obligations; full Art. 9 by 2 August 2027",
     "GPAI Art. 9 obligations in effect since 2 August 2025; full Annex III Art. 9 framework required before 2 August 2026",
     1, 1),

    # Dataset deadline in Art. 10 gap item
    ("gap-art10-deadline",
     "required before August 2027 deadline",
     "required before August 2026 deadline",
     1, 1),

    # Critical gap for human oversight — 'Aug 2027' -> 'Aug 2026'
    ("critical-gap-aug2027",
     "CRITICAL before Aug 2027",
     "CRITICAL before Aug 2026",
     1, 1),

    # ── Timeline steps ────────────────────────────────────────────────────
    # Step 2: was 'GPAI obligations effective'; correct — Aug 2025 was GPAI;
    # Aug 2026 is the Annex III deadline itself, so this step should reflect that.
    ("timeline-aug2026-step",
     "{date:'Aug 2026', action:'GPAI obligations effective — verify any GPAI components comply with Art. 53', priority:'HIGH'}",
     "{date:'Aug 2026', action:'Annex III high-risk compliance deadline — all Arts. 9-17 and 49 obligations must be met', priority:'HIGH'}",
     1, 1),

    # Step 5: was 'Full Annex III compliance deadline'; correct to Annex I (product-embedded)
    ("timeline-aug2027-step",
     "{date:'Aug 2027', action:'Full Annex III compliance deadline — all obligations must be met', priority:'HIGH'}",
     "{date:'Aug 2027', action:'Annex I (product-embedded) high-risk systems deadline — pre-existing Annex III systems should be well past compliance by this date', priority:'MED'}",
     1, 1),

    # Steps for high-risk preparation window — fix the interim step dates
    ("timeline-interim-prep",
     "{date:'Sep – Dec 2026', action:'Art. 11 technical documentation, Art. 12 logging, Art. 13 instructions for use', priority:'MED'}",
     "{date:'Sep – Dec 2026', action:'Post-deadline hardening: Art. 11 documentation audit, Art. 12 logging review, Art. 13 instructions for use — verify registration in EU AI database (Art. 49)', priority:'MED'}",
     1, 1),

    ("timeline-jan-jul",
     "{date:'Jan – Jul 2027', action:'Art. 14–17 obligations: human oversight, accuracy, QMS — prepare Art. 49 registration', priority:'MED'}",
     "{date:'Jan – Jul 2027', action:'Ongoing compliance: Art. 14–17 obligations (human oversight, accuracy, QMS, cybersecurity) — monitor EU AI Office guidance updates', priority:'LOW'}",
     1, 1),

]

MUST_BE_GONE = [
    "deadline:'2 August 2027'",
    "CRITICAL before Aug 2027",
    "required before August 2027 deadline",
    "GPAI obligations effective",
    "Full Annex III compliance deadline",
    "full Art. 9 by 2 August 2027",
]


def run():
    target = REPO / FILE
    if not target.exists():
        print(f"ERROR: file not found: {FILE}")
        return

    text = target.read_text(encoding="utf-8")
    out_of_range = []
    total = 0

    for rule_id, old, new, lo, hi in RULES:
        new_text, count = smart_replace(text, old, new)
        ok = lo <= count <= hi
        if count > 0:
            text = new_text
            total += count
        print(f"  {'OK  ' if ok else 'WARN'} x{count}  [{rule_id}]")
        if not ok:
            out_of_range.append(rule_id)

    if out_of_range:
        print(f"\nWARNING: rules out of expected range: {out_of_range}")
        print("Review before --write.")

    if WRITE:
        target.write_text(text, encoding="utf-8")
        print(f"\nWrote {FILE} ({total} changes).")
        failures = [p for p in MUST_BE_GONE if p in text]
        if failures:
            print("VERIFY FAILED — still present:")
            for f in failures:
                print(f"  {f!r}")
        else:
            print("Verify OK.")
    else:
        print(f"\nDRY RUN — {total} change(s) pending. Pass --write to apply.")


if __name__ == "__main__":
    run()
