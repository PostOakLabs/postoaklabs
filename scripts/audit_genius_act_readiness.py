#!/usr/bin/env python3
"""
Fix invented terminology in genius-act-stablecoin-readiness.html.
Errors:
  - "$10B PPSI Threshold" mislabels threshold: all authorized issuers are
    PPSIs; $10B determines federal vs. state supervision, not PPSI status.
  - "Federal PMSA Charter" / "State PMSA Charter" are invented acronyms.
    Real terms: Federally Qualified Issuer (OCC) / State-Qualified Issuer.
  - "QFPSA" is an invented acronym. Real: foreign payment stablecoin issuer;
    Treasury Secretary determines comparable-regime; foreign issuers register
    with OCC (not Federal Reserve Board as the file claims).
Dry-run by default; pass --write to apply.
"""
import sys

FILE = (
    'C:/dev/Claude/Projects/Post Oak Labs/repo/demos/'
    'genius-act-stablecoin-readiness.html'
)


def smart_replace(html, old, new, tag):
    for o in [old, old.replace("'", '’')]:
        if o in html:
            return html.replace(o, new), True
    print(f'  WARNING: rule {tag!r} fired 0x (expected 1)')
    return html, False


with open(FILE, encoding='utf-8') as f:
    html = f.read()

applied = []


def fix(old, new, tag):
    global html
    html, ok = smart_replace(html, old, new, tag)
    if ok:
        applied.append(tag)


# ── A: Hero badge ─────────────────────────────────────────────────

fix(
    '$10B PPSI Threshold',
    '$10B Federal Supervision Threshold',
    'hero-badge',
)

# ── B: Entity-type select options ─────────────────────────────────

fix(
    'Non-Bank — Federal PMSA Charter',
    'Federally Qualified Issuer (OCC)',
    'opt-federal',
)

fix(
    'Non-Bank — State PMSA Charter',
    'State-Qualified Issuer',
    'opt-state',
)

# ── C: Total-assets select option ─────────────────────────────────

fix(
    '&gt; $10B (PPSI threshold)',
    '&gt; $10B (federal supervision threshold)',
    'opt-over10b',
)

# ── D: Regulator map in JS ────────────────────────────────────────

fix(
    '(Federal PMSA)',
    '(Federally Qualified Issuer)',
    'regmap-federal',
)

fix(
    'Federal Reserve Board (QFPSA determination required)',
    'OCC / Treasury (foreign issuer'
    ' — compatible-regime determination required)',
    'regmap-foreign',
)

# ── E: PPSI status chip in licensing result ───────────────────────

fix(
    "isPPSI?'PPSI — LARGE ISSUER REQUIREMENTS'"
    ":'Non-PPSI — Standard requirements'",
    "isPPSI?'Federal supervision required (>$10B)'"
    ":'State supervision available (≤$10B)'",
    'ppsi-chip',
)

# ── F: Qualification section header ──────────────────────────────

fix(
    'PPSI Qualification Analysis ($10B Threshold)',
    'Federal Supervision Analysis ($10B Threshold)',
    'qual-header',
)

# ── G: >$10B checklist text ───────────────────────────────────────

fix(
    'PPSI threshold met — enhanced requirements apply:'
    ' Federal Reserve Board oversight, enhanced capital standards,'
    ' enhanced liquidity requirements',
    '$10B threshold met — primary federal supervision required:'
    ' OCC / Federal Reserve / FDIC / NCUA as applicable',
    'over10b-text',
)

# ── H: <$10B checklist text ───────────────────────────────────────

fix(
    'Below $10B threshold — standard GENIUS Act requirements apply',
    'Below $10B — state supervision available'
    ' if state certified as substantially similar by Treasury',
    'under10b-text',
)

# ── I: Large-issuer approval requirement ─────────────────────────

fix(
    'PPSI issuers must obtain approval from primary federal'
    ' regulator before issuance',
    'Large issuers (>$10B) must obtain approval from primary'
    ' federal regulator before issuance',
    'large-issuer-approval',
)

# ── J: Foreign issuer / QFPSA text ───────────────────────────────

fix(
    'Federal Reserve Board must determine'
    ' Qualifying Foreign Payment Stablecoin (QFPSA)'
    ' — requires comparable regulatory treatment'
    ' in home jurisdiction',
    'Foreign payment stablecoin issuer — Treasury Secretary'
    ' must determine comparable regulatory regime'
    ' in home jurisdiction; register with OCC',
    'qfpsa-text',
)

# ── K: Attestation "PPSI status" phrase ──────────────────────────

fix(
    'depending on PPSI status',
    'depending on issuer size ($10B threshold)',
    'attest-ppsi',
)

# ── L: Examination label for large issuers ───────────────────────

fix(
    'PPSI: Annual examination by primary federal regulator'
    ' (OCC / Federal Reserve)',
    'Federal supervision (>$10B): Annual examination by'
    ' primary federal regulator (OCC / Federal Reserve)',
    'exam-label',
)

# ── M: Enhanced monitoring label for large issuers ───────────────

fix(
    'PPSI: enhanced transaction monitoring program required',
    'Federal supervision (>$10B):'
    ' enhanced transaction monitoring required',
    'monitoring-label',
)

# ── N: Roadmap QFPSA ─────────────────────────────────────────────

fix(
    'QFPSA determination required from Federal Reserve Board',
    'Foreign issuer — Treasury compatible-regime'
    ' determination required; register with OCC',
    'roadmap-qfpsa',
)

# ── O: Summary PPSI Status display ───────────────────────────────

fix(
    'PPSI — Large Issuer (>$10B)',
    'Federal supervision required (>$10B)',
    'summary-ppsi-large',
)

fix(
    'Standard issuer (below $10B PPSI threshold)',
    'State supervision available (below $10B threshold)',
    'summary-ppsi-small',
)

# ── P: Summary primary regulator foreign (display HTML) ──────────

fix(
    "foreign:'Federal Reserve Board'",
    "foreign:'OCC / Treasury'",
    'summary-regulator-foreign',
)

# ── Q: JSON export primary regulator foreign ─────────────────────

fix(
    "foreign:'FederalReserveBoard'",
    "foreign:'OCC/Treasury'",
    'json-regulator-foreign',
)

# ── R: JSON export key renames ────────────────────────────────────

fix(
    'ppsi_qualified:S.isPPSI',
    'federal_supervision_required:S.isPPSI',
    'json-ppsi-qualified',
)

fix(
    "foreign_qfpsa_required:S.entityType==='foreign'",
    "foreign_compatible_regime_required:S.entityType==='foreign'",
    'json-qfpsa-key',
)

# ── MUST_BE_GONE ──────────────────────────────────────────────────

MUST_BE_GONE = [
    'PPSI Threshold',
    'PMSA Charter',
    'PMSA)',
    'QFPSA',
    "PPSI — LARGE ISSUER REQUIREMENTS",
    'Non-PPSI — Standard requirements',
    'PPSI threshold met',
    'Federal Reserve Board (QFPSA',
    'Federal Reserve Board must determine',
    'ppsi_qualified',
    'foreign_qfpsa_required',
]

mbg_fails = [p for p in MUST_BE_GONE if p in html]
if mbg_fails:
    print('ERROR: MUST_BE_GONE patterns still present:')
    for p in mbg_fails:
        print(f'  {p!r}')
    sys.exit(1)

# ── Report ────────────────────────────────────────────────────────

n = len(applied)
mode = 'DRY RUN' if '--write' not in sys.argv else 'APPLIED'
print(f'{mode} — {n} change(s): {", ".join(applied)}')

if '--write' not in sys.argv:
    print('Pass --write to apply.')
    sys.exit(0)

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print('WRITTEN.')
