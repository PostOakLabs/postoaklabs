#!/usr/bin/env python3
"""audit_eu_ai_act_risk_mapper.py — dry-run by default.
python scripts/audit_eu_ai_act_risk_mapper.py --write  to apply.

Fixes for demos/eu-ai-act-financial-services-risk-mapper.html:
  - All EU AI Act deadlines shifted +1 year in the file; corrected here:
      Art. 5 prohibitions: Feb 2026 -> Feb 2025 (already in effect)
      GPAI obligations:    Aug 2026 -> Aug 2025 (already in effect)
      Annex III high-risk: Aug 2027 -> Aug 2026 (the actual enforcement deadline)
      Product-embedded:    Aug 2030 -> Aug 2027
  - VaR sidebar: wrong penalty tier for Annex III (35M/7% is prohibited-practices;
      Annex III non-compliance = 15M/3%)
  - Insurance annexRef: §5(b) -> §5(c) for life/health underwriting
  - Fraud/AML notes: add §5(b) statutory exception for financial fraud detection
  - Biometric note: clarify 1:1 verification vs 1:N identification
"""

import sys
from pathlib import Path

WRITE = "--write" in sys.argv
REPO  = Path(__file__).resolve().parent.parent
FILE  = "demos/eu-ai-act-financial-services-risk-mapper.html"

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


# (rule_id, old, new, min_expected, max_expected)
RULES = [

    # ── JSON-LD ──────────────────────────────────────────────────────────
    ("jsonld-countdown",
     "Live countdown to GPAI deadline (2 August 2026) and Annex III deadline (2 August 2027)",
     "Annex III enforcement deadline: 2 August 2026; GPAI obligations in effect since 2 August 2025",
     1, 1),

    # ── hero badges ───────────────────────────────────────────────────────
    ("hero-badge-gpai",
     "GPAI Deadline: 2 Aug 2026",
     "GPAI: Aug 2025 · In Effect",
     1, 1),

    # ── hero stats ────────────────────────────────────────────────────────
    # GPAI deadline value (the hstat-v warn box)
    ("hero-gpai-val",
     '<div class="hstat-l">GPAI Deadline</div>\n        <div class="hstat-v warn">2 Aug 2026</div>',
     '<div class="hstat-l">GPAI Deadline</div>\n        <div class="hstat-v warn">2 Aug 2025 (PAST)</div>',
     1, 1),

    # Annex III deadline value
    ("hero-annex3-val",
     '<div class="hstat-v gold">2 Aug 2027</div>',
     '<div class="hstat-v gold">2 Aug 2026</div>',
     1, 1),

    # ── VaR sidebar ───────────────────────────────────────────────────────
    # Wrong penalty tier: 35M/7% is Art. 5 prohibited practices; Annex III = 15M/3%
    ("var-penalty-figure",
     "Up to €35M or 7% of global turnover per violation",
     "Up to €15M or 3% of global annual turnover per violation (Annex III obligations; €35M/7% applies to Art. 5 prohibited practices)",
     1, 1),

    ("var-body-deadline",
     "before the August 2027 enforcement deadline",
     "before the August 2026 enforcement deadline",
     1, 1),

    # ── enforcement timeline grid (4 cells) ──────────────────────────────
    ("timeline-art5-date",
     "2 Feb 2026 · LIVE",
     "2 Feb 2025 · PAST",
     1, 1),

    # GPAI cell — remove the live countdown span; GPAI is past
    ("timeline-gpai-cell",
     '2 Aug 2026 · <span id="gpaiDaysLabel">—</span>',
     "2 Aug 2025 · PAST",
     1, 1),

    # Annex III cell
    ("timeline-annex3-cell",
     "2 Aug 2027 · 15 months",
     "2 Aug 2026 · ~2 months",
     1, 1),

    # Product-embedded / legacy GPAI cell
    ("timeline-legacy-cell",
     "2 Aug 2030 · 4+ years",
     "2 Aug 2027 · ~14 months",
     1, 1),

    # ── JS countdown — retarget to Annex III (2026) not GPAI (2025) ──────
    # The countdown now shows days until Annex III; GPAI stat shows static PAST.
    ("js-countdown-date",
     "daysUntil('2026-08-02')",
     "daysUntil('2026-08-02')",   # keep targeting Annex III date; just relabel below
     1, 1),

    # The countdown is displayed in id="gpaiCountdown" inside the GPAI hero stat.
    # Since GPAI is PAST, we want that box to say "PAST" — so redirect countdown to
    # display in Annex III context instead by renaming the element reference.
    # Simplest: change the JS to update a differently-named element.
    # (Alternative: leave countdown targeting 2026-08-02 but display in Annex III stat)
    # --> Change the stat-s element ID so it no longer hijacks the GPAI box.
    ("gpai-countdown-id",
     '<div class="hstat-s" id="gpaiCountdown">calculating…</div>',
     '<div class="hstat-s">In effect since Aug 2025</div>',
     1, 1),

    # ── GPAI use-case deadline fields ────────────────────────────────────
    # Match unique context (risk:'gpai') to avoid hitting limited-risk 2026 dates
    ("gpai-std-deadline",
     "risk:'gpai', annexRef:'Article 53', articleRef:'Chapter V',\n    deadline:'2 August 2026',\n    note:'General-purpose AI models must comply with transparency obligations (technical documentation, copyright compliance, summary of training data). Effective 2 August 2026.",
     "risk:'gpai', annexRef:'Article 53', articleRef:'Chapter V',\n    deadline:'2 August 2025',\n    note:'General-purpose AI models must comply with transparency obligations (technical documentation, copyright compliance, summary of training data). Effective 2 August 2025.",
     1, 1),

    ("gpai-systemic-deadline",
     "risk:'gpai_systemic', annexRef:'Article 55', articleRef:'Chapter V',\n    deadline:'2 August 2026',",
     "risk:'gpai_systemic', annexRef:'Article 55', articleRef:'Chapter V',\n    deadline:'2 August 2025',",
     1, 1),

    # ── All Annex III deadline:'2 August 2027' -> 2026 ──────────────────
    # Only Annex III high-risk items use this string; limited-risk use 2026, GPAI handled above.
    ("annex3-deadline-data",
     "deadline:'2 August 2027'",
     "deadline:'2 August 2026'",
     8, 16),  # multiple Annex III use case entries + HR items

    # ── RISK_META summary texts ───────────────────────────────────────────
    ("risk-meta-high-deadline",
     "(deadline: 2 August 2027)",
     "(deadline: 2 August 2026)",
     1, 1),

    ("risk-meta-gpai-date",
     "apply from 2 August 2026. If deployed in a high-risk FS use case",
     "apply from 2 August 2025. If deployed in a high-risk FS use case",
     1, 1),

    # Mandate export GPAI date reference
    ("mandate-gpai-date",
     "prioritise technical documentation and training data summary before 2 August 2026 deadline.",
     "GPAI obligations are in effect since 2 August 2025 — ensure technical documentation and training data summary are complete.",
     1, 1),

    # ── Classification corrections ────────────────────────────────────────
    # Insurance: life/health is Annex III §5(c), not §5(b)
    ("ins-life-annexref",
     "{ id:'ins_life_health', cat:'Insurance',\n    label:'Life / health insurance underwriting or pricing (natural persons)',\n    risk:'high', annexRef:'Annex III §5(b)'",
     "{ id:'ins_life_health', cat:'Insurance',\n    label:'Life / health insurance underwriting or pricing (natural persons)',\n    risk:'high', annexRef:'Annex III §5(c)'",
     1, 1),

    ("ins-life-note",
     "qualifying under Annex III §5(b).",
     "qualifying under Annex III §5(c).",
     1, 2),   # may appear in both ins_life_health and ins_claims notes

    ("ins-claims-annexref",
     "{ id:'ins_claims', cat:'Insurance',\n    label:'Automated insurance claims processing (natural persons)',\n    risk:'high', annexRef:'Annex III §5(b)'",
     "{ id:'ins_claims', cat:'Insurance',\n    label:'Automated insurance claims processing (natural persons)',\n    risk:'high', annexRef:'Annex III §5(c)'",
     1, 1),

    # Fraud detection: §5(b) exception applies; update annexRef and note
    ("fraud-auto-annexref",
     "{ id:'fraud_auto_block', cat:'Fraud Detection',\n    label:'Real-time payment fraud detection — automated block (no human gate)',\n    risk:'high', annexRef:'Annex III §5(b)', articleRef:'Article 6(2)',",
     "{ id:'fraud_auto_block', cat:'Fraud Detection',\n    label:'Real-time payment fraud detection — automated block (no human gate)',\n    risk:'high', annexRef:'Annex III — §5(b) excepts fraud detection; see note', articleRef:'Article 6(2)',",
     1, 1),

    ("fraud-auto-note",
     "Fully automated blocking of a natural person's access to payment services is a high-risk decision under Annex III §5. Human override capability must be designed in (Article 14).",
     "Fraud detection systems are explicitly excepted from Annex III §5(b) per the statutory fraud-detection carve-out. Whether automated payment blocking engages another Annex III provision is a fact-specific assessment; seek legal advice. If any Annex III obligation applies, Art. 14 human oversight must be designed in.",
     1, 1),

    # AML/TM: also excepted from §5(b) as financial fraud detection
    ("aml-auto-annexref",
     "{ id:'aml_auto', cat:'AML / Compliance',\n    label:'AML / transaction monitoring — automated account restriction / blocking',\n    risk:'high', annexRef:'Annex III §5(b)',",
     "{ id:'aml_auto', cat:'AML / Compliance',\n    label:'AML / transaction monitoring — automated account restriction / blocking',\n    risk:'high', annexRef:'Annex III — §5(b) excepts AML/fraud detection; see note',",
     1, 1),

    ("aml-auto-note",
     "Automated restrictions on access to financial accounts or payment services for natural persons constitute high-risk decisions under Annex III §5 (access to essential private services).",
     "AML and financial fraud detection systems are excepted from Annex III §5(b) by statute. Automated account restrictions may still engage other Annex III provisions depending on the specific decision; this requires a fact-specific legal assessment.",
     1, 1),

    # Biometric: 1:1 verification excluded; only 1:N identification is §1(a)
    ("kyc-biometric-note",
     "Remote biometric identification systems are explicitly high-risk under Annex III §1(a). Real-time remote biometric identification in publicly accessible spaces is prohibited (Article 5) with narrow law-enforcement exceptions.",
     "Remote biometric IDENTIFICATION (1:N matching) is explicitly high-risk under Annex III §1(a). Biometric VERIFICATION (1:1 confirmation that a person matches their claimed identity) is excluded from this classification. If this KYC system performs 1:1 verification only, Annex III §1(a) does not apply — seek legal confirmation on the specific architecture.",
     1, 1),
]

MUST_BE_GONE = [
    "2 Aug 2027 · 15 months",
    "2 Aug 2026 · <span",    # countdown span in timeline
    "August 2027 enforcement deadline",
    "(deadline: 2 August 2027)",
    "GPAI deadline (2 August 2026)",
    "apply from 2 August 2026. If deployed",
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
        if old == new:      # no-op rules (e.g. js-countdown-date kept same)
            continue
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
