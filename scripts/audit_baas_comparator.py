#!/usr/bin/env python3
"""
Anonymize named vendor data in baas-provider-economics-comparator.html.
Audit finding: Unit, Treasury Prime, Column, Synctera, Grasshopper pricing
is invented — replace with illustrative archetypes Provider A-E.
Dry-run by default; pass --write to apply.
"""
import sys

FILE = (
    'C:/dev/Claude/Projects/Post Oak Labs/repo/demos/'
    'baas-provider-economics-comparator.html'
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


# ── A: Provider A (was Unit) ──────────────────────────────────────

fix("id: 'unit',", "id: 'a',", 'id-unit')
fix("name: 'Unit',", "name: 'Provider A',", 'name-unit')

# ── B: Provider B (was Treasury Prime) ───────────────────────────

fix("id: 'treasury',", "id: 'b',", 'id-treasury')
fix("name: 'Treasury Prime',", "name: 'Provider B',", 'name-treasury')

# ── C: Provider C (was Column) ───────────────────────────────────

fix("id: 'column',", "id: 'c',", 'id-column')
fix("name: 'Column',", "name: 'Provider C',", 'name-column')

# ── D: Provider D (was Synctera) ─────────────────────────────────

fix("id: 'synctera',", "id: 'd',", 'id-synctera')
fix("name: 'Synctera',", "name: 'Provider D',", 'name-synctera')

# ── E: Provider E (was Grasshopper) ──────────────────────────────

fix("id: 'grasshopper',", "id: 'e',", 'id-grasshopper')
fix("name: 'Grasshopper',", "name: 'Provider E',", 'name-grasshopper')

# ── F: Meta description ───────────────────────────────────────────

fix(
    'across Unit, Treasury Prime, Column, Synctera,'
    ' and Grasshopper — at any volume tier.',
    'across five illustrative BaaS provider archetypes'
    ' (A–E) — at any volume tier.',
    'meta-desc',
)

# ── H: JSON-LD keywords ──────────────────────────────────────────

fix(
    'Treasury Prime, Unit Finance, Column, Synctera,'
    ' Grasshopper, break-even, BaaS comparison,',
    'break-even, BaaS comparison,',
    'jsonld-keywords',
)

# ── I: Hero paragraph ────────────────────────────────────────────

fix(
    'across Unit, Treasury Prime, Column, Synctera,'
    ' and Grasshopper — then export',
    'across five illustrative BaaS provider archetypes'
    ' (A–E) — then export',
    'hero-para',
)

# ── MUST_BE_GONE ──────────────────────────────────────────────────

MUST_BE_GONE = [
    "id: 'unit'",
    "id: 'treasury'",
    "id: 'column'",
    "id: 'synctera'",
    "id: 'grasshopper'",
    "name: 'Unit'",
    "name: 'Treasury Prime'",
    "name: 'Column'",
    "name: 'Synctera'",
    "name: 'Grasshopper'",
    'Unit, Treasury Prime',
    'Treasury Prime, Unit Finance',
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
