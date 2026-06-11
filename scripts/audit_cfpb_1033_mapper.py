#!/usr/bin/env python3
"""audit_cfpb_1033_mapper.py — dry-run by default.
python scripts/audit_cfpb_1033_mapper.py --write  to apply.

Fixes for demos/cfpb-1033-financial-data-rights-mapper.html:
  - TIERS: T1 >$500B->>=250B; T2 $10B-$500B->$10B-$250B Oct->Apr 2027;
    T3 $1.5B-$10B->$3B-$10B Apr->2028; T4 <$1.5B->$1.5B-$3B Apr->2029;
    add T5 $850M-$1.5B Apr 2030; tppp deadline 2030->2027
  - CALENDAR: fix dates throughout; add Apr 2029 wave; add court-stay note to each
  - Select dropdown: fix all option labels+deadlines; add T5
  - Scenarios: neobank tier t4->tppp (neobanks are non-depositories)
  - JSON-LD featureList[0]: fix tier ranges
  - JSON-LD featureList[3]: fix calendar (Oct 2026 removed, Apr 2029 added)
  - JSON-LD description + meta description: "2025-2030" -> "2026-2030"
  - AP2 export: effective "2024-12-13" -> "2025-01-17" (actual effective date)
  - Sidebar: fix first-deadline and final-wave stats; replace non-compliance
    paragraph with court injunction / reconsideration notice
  - Hero: add STAYED badge; fix hero-sub (four-wave->five-tier + stayed note)
  - initCountdown: show "Stayed" instead of computed days/Passed
"""

import sys

FILE = 'demos/cfpb-1033-financial-data-rights-mapper.html'

def smart_replace(text, old, new):
    # Try straight apostrophe and curly apostrophe variants
    for variant in [old, old.replace("'", '’'), old.replace('’', "'")]:
        if variant in text:
            count = text.count(variant)
            return text.replace(variant, new), count
    return text, 0

# (tag, old, new, min_expected, max_expected)
RULES = [

    # 1. TIERS object — thresholds and deadlines entirely wrong
    ('tiers-obj',
     "const TIERS = {\n"
     "  t1:   { id: 't1',   label: 'Tier 1 — Large Depository', assets: '>$500B', deadline: '2026-04-01', wave: 1, cls: 't1', color: '#dc2626' },\n"
     "  t2:   { id: 't2',   label: 'Tier 2 — Mid-Size Depository', assets: '$10B–$500B', deadline: '2026-10-01', wave: 2, cls: 't2', color: '#f59e0b' },\n"
     "  t3:   { id: 't3',   label: 'Tier 3 — Smaller Depository', assets: '$1.5B–$10B', deadline: '2027-04-01', wave: 3, cls: 't3', color: '#2a7fc0' },\n"
     "  t4:   { id: 't4',   label: 'Tier 4 — Small Institution / Fintech', assets: '<$1.5B', deadline: '2028-04-01', wave: 4, cls: 't4', color: '#10b981' },\n"
     "  tppp: { id: 'tppp', label: 'TPPP / Data Aggregator', assets: 'N/A', deadline: '2030-04-01', wave: 5, cls: 'tppp', color: '#8b5cf6' },\n"
     "};",
     "const TIERS = {\n"
     "  t1:   { id: 't1',   label: 'Tier 1 — Largest Depositories (≥$250B)', assets: '≥$250B total assets', deadline: '2026-04-01', wave: 1, cls: 't1', color: '#dc2626' },\n"
     "  t2:   { id: 't2',   label: 'Tier 2 — Large Depositories ($10B–$250B)', assets: '$10B–$250B', deadline: '2027-04-01', wave: 2, cls: 't2', color: '#f59e0b' },\n"
     "  t3:   { id: 't3',   label: 'Tier 3 — Mid-Size Depositories ($3B–$10B)', assets: '$3B–$10B', deadline: '2028-04-01', wave: 3, cls: 't3', color: '#2a7fc0' },\n"
     "  t4:   { id: 't4',   label: 'Tier 4 — Community Depositories ($1.5B–$3B)', assets: '$1.5B–$3B', deadline: '2029-04-01', wave: 4, cls: 't4', color: '#10b981' },\n"
     "  t5:   { id: 't5',   label: 'Tier 5 — Small Depositories ($850M–$1.5B)', assets: '$850M–$1.5B', deadline: '2030-04-01', wave: 5, cls: 't4', color: '#059669' },\n"
     "  tppp: { id: 'tppp', label: 'Non-Depository / Non-Bank (≥$10B receipts)', assets: '≥$10B total receipts', deadline: '2027-04-01', wave: 2, cls: 'tppp', color: '#8b5cf6' },\n"
     "};",
     1, 1),

    # 2. CALENDAR array — Oct 2026 invented; all obligations wrong; missing Apr 2029
    ('calendar-arr',
     "const CALENDAR = [\n"
     "  { date: 'Apr 2026', iso: '2026-04-01', tiers: ['t1'], obligation: 'Tier 1 institutions must expose all 7 data categories via structured API. Screen-scraping must be deprecated for covered accounts.' },\n"
     "  { date: 'Oct 2026', iso: '2026-10-01', tiers: ['t2'], obligation: 'Tier 2 institutions (mid-size banks, large credit unions) come into scope. Same data category requirements as Tier 1.' },\n"
     "  { date: 'Apr 2027', iso: '2027-04-01', tiers: ['t3'], obligation: 'Tier 3 smaller depositories, community banks with >$1.5B assets, and qualifying credit unions must comply.' },\n"
     "  { date: 'Apr 2028', iso: '2028-04-01', tiers: ['t4'], obligation: 'Tier 4 small institutions and fintech account providers must expose data. Most neobanks and programme managers fall here.' },\n"
     "  { date: 'Apr 2030', iso: '2030-04-01', tiers: ['tppp'], obligation: 'Third-Party Payment Processors and data aggregators face specific authorisation, data retention, and consent management obligations.' },\n"
     "];",
     "const CALENDAR = [\n"
     "  { date: 'Apr 2026', iso: '2026-04-01', tiers: ['t1'], obligation: 'Tier 1 (≥$250B depositories) and qualifying non-banks (≥$10B receipts): compliance date per original rule. All §1033 compliance dates are currently STAYED by federal court injunction (E.D. Ky.); enforcement is suspended pending CFPB reconsideration rulemaking.' },\n"
     "  { date: 'Apr 2027', iso: '2027-04-01', tiers: ['t2','tppp'], obligation: 'Tier 2 ($10B–$250B depositories) and non-depositories with ≥$10B in total receipts: compliance date per original rule — subject to court stay.' },\n"
     "  { date: 'Apr 2028', iso: '2028-04-01', tiers: ['t3'], obligation: 'Tier 3 mid-size depositories ($3B–$10B assets): compliance date per original rule — subject to court stay.' },\n"
     "  { date: 'Apr 2029', iso: '2029-04-01', tiers: ['t4'], obligation: 'Tier 4 community depositories ($1.5B–$3B assets): compliance date per original rule — subject to court stay.' },\n"
     "  { date: 'Apr 2030', iso: '2030-04-01', tiers: ['t5'], obligation: 'Tier 5 small depositories ($850M–$1.5B assets): compliance date per original rule — subject to court stay. Depository institutions below $850M in assets (SBA size standard) are exempt from the rule.' },\n"
     "];",
     1, 1),

    # 3. Scenario neobank: t4 -> tppp (neobanks are non-depositories, not $1.5B-$3B community banks)
    ('scenario-neobank',
     "neobank:     { tier: 't4', products: ['checking','savings','digital'],  role: 'both',       techs: ['oauth','consent'] },",
     "neobank:     { tier: 'tppp', products: ['checking','savings','digital'],  role: 'both',       techs: ['oauth','consent'] },",
     1, 1),

    # 4. Select dropdown — wrong thresholds and deadlines; missing T5 option
    ('select-dropdown',
     '<select id="inp-tier" onchange="onTierChange()">\n'
     '              <option value="">— Select institution type —</option>\n'
     '              <option value="t1">Tier 1 — Large Depository (>$500B assets) · Deadline: Apr 2026</option>\n'
     '              <option value="t2">Tier 2 — Mid-Size Depository ($10B–$500B) · Deadline: Oct 2026</option>\n'
     '              <option value="t3">Tier 3 — Smaller Depository ($1.5B–$10B) · Deadline: Apr 2027</option>\n'
     '              <option value="t4">Tier 4 — Small Depository (&lt;$1.5B) / Fintech · Deadline: Apr 2028</option>\n'
     '              <option value="tppp">TPPP — Third-Party Payment Processor or Data Aggregator · Deadline: Apr 2030</option>\n'
     '            </select>',
     '<select id="inp-tier" onchange="onTierChange()">\n'
     '              <option value="">— Select institution type —</option>\n'
     '              <option value="t1">Tier 1 — Largest Depositories (≥$250B) · Apr 2026 (stayed)</option>\n'
     '              <option value="t2">Tier 2 — Large Depositories ($10B–$250B) · Apr 2027 (stayed)</option>\n'
     '              <option value="t3">Tier 3 — Mid-Size Depositories ($3B–$10B) · Apr 2028 (stayed)</option>\n'
     '              <option value="t4">Tier 4 — Community Depositories ($1.5B–$3B) · Apr 2029 (stayed)</option>\n'
     '              <option value="t5">Tier 5 — Small Depositories ($850M–$1.5B) · Apr 2030 (stayed)</option>\n'
     '              <option value="tppp">Non-Depository / Non-Bank (≥$10B receipts) · Apr 2027 (stayed)</option>\n'
     '            </select>',
     1, 1),

    # 5. JSON-LD featureList[0]: tier ranges wrong
    ('jsonld-feat-tiers',
     '"Institution classification: Tier 1 (>$500B), Tier 2 (>$10B), Tier 3 (>$1.5B), Tier 4 (<$1.5B), TPPP",',
     '"Institution classification: Tier 1 (≥$250B), Tier 2 ($10B–$250B), Tier 3 ($3B–$10B), Tier 4 ($1.5B–$3B), Tier 5 ($850M–$1.5B), Non-Depository (≥$10B receipts); <$850M exempt",',
     1, 1),

    # 6. JSON-LD featureList[3]: calendar has invented Oct 2026 step; missing Apr 2029
    ('jsonld-feat-cal',
     '"Phased compliance calendar: Apr 2026 → Oct 2026 → Apr 2027 → Apr 2028 → Apr 2030",',
     '"Phased compliance calendar: Apr 2026 → Apr 2027 → Apr 2028 → Apr 2029 → Apr 2030 (all dates subject to court stay; CFPB reconsidering rule)",',
     1, 1),

    # 7. JSON-LD description: "2025-2030" -> "2026-2030" (first wave is Apr 2026)
    ('jsonld-desc-dates',
     'surfaces the 2025–2030 phased compliance calendar',
     'surfaces the 2026–2030 phased compliance calendar (stayed pending CFPB rulemaking)',
     1, 1),

    # 8. Meta description: same 2025->2026 fix
    ('meta-desc-dates',
     'navigate the 2025–2030 compliance calendar',
     'navigate the 2026–2030 compliance calendar (stayed pending CFPB rulemaking)',
     1, 1),

    # 9. AP2 export: effective date wrong (rule effective Jan 17 2025, not Dec 13 2024)
    ('ap2-effective',
     '"effective": "2024-12-13",',
     '"effective": "2025-01-17",',
     1, 1),

    # 10. Sidebar first-deadline stat: Tier 1 threshold was >$500B not ≥$250B
    ('sidebar-first-deadline',
     '<div class="var-stat">\U0001f4c5 First deadline: Apr 2026 (Tier 1)</div>',
     '<div class="var-stat">\U0001f4c5 First deadline: Apr 2026 (T1, ≥$250B) — stayed</div>',
     1, 1),

    # 11. Sidebar final-wave stat: "TPPPs" is not the Tier 5 label
    ('sidebar-final-wave',
     '<div class="var-stat">\U0001f4c5 Final wave: Apr 2030 (TPPPs)</div>',
     '<div class="var-stat">\U0001f4c5 Final wave: Apr 2030 (T5, $850M–$1.5B)</div>',
     1, 1),

    # 12. Sidebar: replace non-compliance paragraph + UDAAP stat with injunction notice
    ('sidebar-injunction',
     '<p style="margin-top:1rem;">Non-compliance risk: CFPB can bring enforcement under Dodd-Frank UDAAP authority — potential for 7-figure civil money penalties and consent orders.</p>\n'
     '        <div class="var-stat">⚠️ UDAAP enforcement risk post-deadline</div>',
     '<p style="margin-top:1rem;"><strong style="color:#dc2626;">⚠ Rule Stayed:</strong> A federal court (E.D. Ky., 2025) enjoined CFPB enforcement of the §1033 rule. The CFPB issued an ANPRM in August 2025 initiating reconsideration and is expected to rewrite the rule. Compliance dates shown are from the original October 2024 rule text and may change materially.</p>\n'
     '        <div class="var-stat">⚖️ Court injunction in effect — enforcement suspended</div>',
     1, 1),

    # 13. Hero: add STAYED badge after CFPB §1033 badge
    ('hero-badge-stayed',
     '<span class="eyebrow-badge warn">CFPB §1033</span>',
     '<span class="eyebrow-badge warn">CFPB §1033</span>\n        <span class="eyebrow-badge" style="border-color:rgba(220,38,38,0.4);color:#dc2626;">⚠ RULE STAYED</span>',
     1, 1),

    # 14. Hero-sub: fix "four-wave" -> "five-tier"; add court-stay note
    ('hero-sub-cal',
     'navigate the four-wave compliance calendar from April 2026 through April 2030',
     'navigate the five-tier compliance calendar from April 2026 through April 2030 (enforcement stayed by court; CFPB reconsidering rule)',
     1, 1),

    # 15. initCountdown: shows computed "Passed"/"days" — replace with static "Stayed" message
    ('countdown-fn',
     "function initCountdown() {\n"
     "  const d = daysUntil('2026-04-01');\n"
     "  const el = document.getElementById('countdown-val');\n"
     "  const lb = document.getElementById('countdown-label');\n"
     "  if (!el) return;\n"
     "  if (d > 0) {\n"
     "    el.textContent = d + 'd';\n"
     "    lb.textContent = 'Until Tier 1 deadline';\n"
     "    el.classList.add('warn');\n"
     "  } else {\n"
     "    el.textContent = 'Passed';\n"
     "    lb.textContent = 'Tier 1 deadline';\n"
     "  }\n"
     "}",
     "function initCountdown() {\n"
     "  const el = document.getElementById('countdown-val');\n"
     "  const lb = document.getElementById('countdown-label');\n"
     "  if (!el) return;\n"
     "  el.textContent = 'Stayed';\n"
     "  lb.textContent = 'Enforcement enjoined (E.D. Ky. 2025)';\n"
     "  el.classList.add('warn');\n"
     "}",
     1, 1),
]

MUST_BE_GONE = [
    ">$500B",
    "'2026-10-01'",
    '"2024-12-13"',
    "Tier 1 — Large Depository'",
    "TPPP / Data Aggregator",
    "Tier 4 — Small Institution / Fintech",
    "four-wave compliance calendar",
    "Oct 2026",
    "UDAAP enforcement risk post-deadline",
    "Until Tier 1 deadline",
    "Tier 1 institutions must expose all 7",
    "Tier 2 institutions (mid-size banks",
    ">$1.5B assets, and qualifying credit unions",
    "Most neobanks and programme managers fall here",
    "2025–2030",
]

def main():
    write_mode = '--write' in sys.argv
    with open(FILE, encoding='utf-8') as f:
        original = f.read()

    text = original
    total_changes = 0
    warnings = []

    for rule in RULES:
        tag, old, new, mn, mx = rule
        if old == new:
            continue
        text, count = smart_replace(text, old, new)
        if count < mn or count > mx:
            warnings.append(f"WARNING: rule '{tag}' fired {count}x (expected {mn}-{mx})")
        else:
            total_changes += count

    if write_mode:
        # MUST_BE_GONE checks
        for pattern in MUST_BE_GONE:
            if pattern in text:
                print(f"ERROR: MUST_BE_GONE pattern still present: {pattern!r}")
                sys.exit(1)
        with open(FILE, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"WRITTEN — {total_changes} change(s) applied to {FILE}")
    else:
        diff_count = sum(1 for a, b in zip(original.splitlines(), text.splitlines()) if a != b)
        print(f"DRY RUN — {total_changes} change(s) pending. Pass --write to apply.")

    for w in warnings:
        print(w)

if __name__ == '__main__':
    main()
