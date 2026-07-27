#!/usr/bin/env node
/**
 * check-copy-hallmarks.mjs — gate against AI-writing hallmarks in reader-facing copy.
 *
 * VENDORED from AINumbers repo/scripts/check-copy-hallmarks.mjs (canonical
 * source, commit 555a032f028be6f2e86e10579c253f552726aa5e, 2026-07-21) per
 * POL-COPY-GATE (CLAUDE.md) and the single-lineage rule: this file is a
 * straight copy plus one POL-specific deletion (the chaingraph.json block,
 * which has no POL equivalent — POL has no MCP chaingraph). Do not fork
 * further; if POL needs a new rule, add it upstream in AINumbers first, then
 * re-vendor here. Vendored 2026-07-27.
 *
 * Hard-fails on:
 *   1. Em-dashes (—) in the human-visible text of any public HTML page
 *      (script/style/pre/code/HTML-comments excluded).
 *   2. Internal build jargon in visible HTML text: "Wave N", "W-A".."W-F"
 *      badge codes, standalone "D0". (Kept for lineage parity; POL copy does
 *      not currently use these codes, so this category should stay empty.)
 *   3. ANTI-AI-TELL copy (Tim 2026-07-11, PERMANENT — memory
 *      `feedback-anti-ai-tell-copy-ban` / POL CLAUDE.md): italics-for-emphasis
 *      anywhere (including headings), "not just X but" / "isn't just" /
 *      "more than just", dramatic-fragment openers ("The result?"),
 *      validation-phrasing ("you're not alone"), two-tone constructions
 *      ("It is not X. It is Y." and the comma-pivot sibling), a filler-vocab
 *      denylist (delve, tapestry, testament to, quiet(ly) X, seamless,
 *      game-changer, elevate, unlock, "it's worth noting", "in today's
 *      fast-paced"), and decorative emoji in HEADERS.
 *
 * Baseline (scripts/copy-hallmarks-baseline.json) shields not-yet-swept files
 * for em-dash/jargon/bold ONLY: a file may carry at most its baselined count,
 * and files absent from the baseline must be clean there. The ANTI-AI-TELL
 * categories carry NO baseline — zero tolerance everywhere.
 *
 * Usage:
 *   node scripts/check-copy-hallmarks.mjs            # gate (preflight + CI)
 *   node scripts/check-copy-hallmarks.mjs --update   # regenerate the em-dash/jargon/bold baseline
 *
 * Style rule of record: CLAUDE.md ANTI-AI-TELL COPY BAN section.
 */
import { readFileSync, writeFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { resolve, dirname, relative, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const BASELINE_PATH = resolve(REPO, 'scripts', 'copy-hallmarks-baseline.json');
const UPDATE = process.argv.includes('--update');

const EMDASH = /—/g;
// Build jargon that must not reach readers. \b keeps ART-ids and W-8 (digit) safe.
const JARGON = [
  [/\bWave\s+\d+\b/g, 'Wave-N build code'],
  [/\bW-[A-F]\b/g, 'W-x badge code'],
  [/\bD0\b/g, 'D0 badge code'],
];
// Blocking, zero-tolerance, no baseline — HIGH-PRECISION twotone family.
const TWOTONE_HIGHPRECISION = /\b(?:is|are|was|were) not (?:a|an|the )?[\w-]+\.\s+(?:It|They|This|That) (?:is|are)\b/g;
// Advisory only, PERMANENTLY — heuristic, catches legitimate 3-item lists too often for a hard gate.
const TRIAD = /\b\w+,\s*\w+,\s*(?:and|&)\s*\w+\b/g;
// Structural UI chrome exempt from the bold count (not prose emphasis).
const STRUCTURAL_BOLD_EXEMPT = /<(th|dt|label|legend)\b[^>]*>[\s\S]*?<\/\1>/gi;
const BOLD = /<(b|strong)\b[^>]*>[^<]+<\/\1>/gi;

// --- ANTI-AI-TELL BAN (Tim 2026-07-11, PERMANENT — feedback-anti-ai-tell-copy-ban) ---
// Blocking, zero-tolerance, no baseline. Each entry: [regex, label].
const NOTJUSTBUT = [
  [/\bnot\s+just\b(?:(?!\bbut\b)[^.?!]){0,80}\bbut\b/gi, '"not just X but" construction'],
  [/\bisn['’]?t\s+just\b/gi, '"isn\'t just"'],
  [/\bmore\s+than\s+just\b/gi, '"more than just"'],
];
const DRAMATIC_FRAGMENT = /\bThe (?:result|catch|takeaway|verdict|kicker|bottom line)\?/gi;
const VALIDATION_PHRASING = /\byou['’]?re\s+not\s+(?:alone|imagining\s+(?:it|things))\b/gi;
// The comma-pivot two-tone cliché: "It's not X, it's Y" (and this/that/there +
// "it's/it is/it's about/they're" on the far side). Sibling to
// TWOTONE_HIGHPRECISION (the period-separated "It is not X. It is Y." form).
const TWOTONE_COMMA = /\b(?:it['’]?s|it is|this is|that['’]?s|there['’]?s)\s+not\s+[^,.!?]{1,70},\s+(?:it['’]?s\s+about|it['’]?s|it is|they['’]?re)\b/gi;
const FILLER_VOCAB = [
  [/\bdelv(?:e|es|ed|ing)\b/gi, 'delve'],
  [/\btapestr(?:y|ies)\b/gi, 'tapestry'],
  [/\btestament\s+to\b/gi, 'testament to'],
  [/\bquiet(?:ly)?\s+(?:revolution|shift|force|power|evolution)\b/gi, 'quiet(ly) X'],
  [/\bseamless(?:ly)?\b/gi, 'seamless'],
  [/\bgame[\s-]?chang(?:er|ing)\b/gi, 'game-changer'],
  [/\belevat(?:e|es|ed|ing)\s+(?:your|our|its|their)\s+\w+/gi, 'elevate your/our/its X'],
  [/\bunlock(?:s|ed|ing)?\s+(?:your\s+|the\s+full\s+|new\s+|greater\s+)?(?:potential|value|growth|opportunit(?:y|ies)|insight(?:s)?|power|possibilit(?:y|ies))\b/gi, 'unlock potential/value/growth (marketing sense)'],
  [/\bit['’]?s\s+worth\s+noting\b/gi, "it's worth noting"],
  [/\bin\s+today['’]?s\s+fast-paced\b/gi, "in today's fast-paced"],
];
// Overuse tells: individually legit words, but repeating them across a page reads
// as an AI hallmark. A file NOT in the baseline may use each at most OVERUSE_CAP
// times; legacy debt is shielded by the baseline (ratchet — counts only go down
// via --update), same design as the em-dash gate.
const OVERUSE_CAP = 1;
const OVERUSE_VOCAB = [
  [/\bhonest(?:ly|y)?\b/gi, 'honest'],
];
// Emoji ranges (misc symbols, emoticons, transport, supplemental, dingbats).
const EMOJI = /[\u{2600}-\u{27BF}\u{1F300}-\u{1FAFF}]/gu;
// Functional UI/status glyphs exempt from the ban.
const EMOJI_UI_EXEMPT = new Set(['✓', '✗', '✔', '✔️', '❌', '✅', '⚠', '⚠️', '🔒', '🔏', '🚫', '☑', '☑️', '➡', '➡️', '→', '⭐', '★', '☆', '❓', '❗', '‼', '⏳', '⏱', '⏱️']);
function nonExemptEmoji(text) {
  return (text.match(EMOJI) || []).filter((ch) => !EMOJI_UI_EXEMPT.has(ch));
}
// Elements exempt from the emoji ban — status/count badges/pills and interactive
// controls, not narrative copy.
const BADGE_ELEMENT = /<(span|div|a|p)\b[^>]*\bclass\s*=\s*["'][^"']*\b(?:badge|pill|chip)\b[^"']*["'][^>]*>[\s\S]*?<\/\1>/gi;
const CONTROL_ELEMENT = /<(button|div|span)\b[^>]*\bclass\s*=\s*["'][^"']*\b(?:btn|icon)\b[^"']*["'][^>]*>[\s\S]*?<\/\1>/gi;
const BUTTON_TAG = /<button\b[^>]*>[\s\S]*?<\/button>/gi;

const SKIP_DIRS = new Set(['.git', 'node_modules', '.github', 'scripts', '_archive']);

function htmlFiles(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    const st = statSync(p);
    if (st.isDirectory()) {
      if (!SKIP_DIRS.has(name)) htmlFiles(p, out);
    } else if (name.endsWith('.html')) {
      out.push(p);
    }
  }
  return out;
}

/** Strip script/style/pre/code bodies + HTML comments, keep other tags intact. */
function proseHtml(html) {
  return html
    .replace(/<script\b[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style\b[\s\S]*?<\/style>/gi, ' ')
    .replace(/<pre\b[\s\S]*?<\/pre>/gi, ' ')
    .replace(/<code\b[\s\S]*?<\/code>/gi, ' ')
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(BADGE_ELEMENT, ' ')
    .replace(BUTTON_TAG, ' ')
    .replace(CONTROL_ELEMENT, ' ');
}

/** Human-visible text: proseHtml() with all remaining tags stripped too. */
function visibleText(html) {
  return proseHtml(html).replace(/<[^>]+>/g, ' ');
}

/** Header-only visible text: content of <h1>-<h6>, tags stripped, badges already gone. */
function headerText(prose) {
  const out = [];
  const re = /<h[1-6]\b[^>]*>([\s\S]*?)<\/h[1-6]>/gi;
  let m;
  while ((m = re.exec(prose))) out.push(m[1].replace(/<[^>]+>/g, ' '));
  return out.join(' ');
}

const findings = {}; // rel path -> { emdash, jargon: [msg], twotone, hallmarks: [msg] }
for (const file of htmlFiles(REPO)) {
  const rel = relative(REPO, file).replace(/\\/g, '/');
  const raw = readFileSync(file, 'utf8');
  const prose = proseHtml(raw); // tags intact, badges/script/style/pre/code/comments gone
  const text = visibleText(raw); // fully tag-stripped

  const emdash = (text.match(EMDASH) || []).length;
  const jargon = [];
  for (const [re, label] of JARGON) {
    const m = text.match(re) || [];
    if (m.length) jargon.push(`${label} ×${m.length} (${[...new Set(m)].slice(0, 3).join(', ')})`);
  }
  const twotoneHP = (text.match(TWOTONE_HIGHPRECISION) || []).length;
  const triad = (text.match(TRIAD) || []).length;

  const hallmarks = [];
  const italics = (prose.match(/<(em|i)\b[^>]*>[^<]+<\/\1>/gi) || []).length;
  if (italics) hallmarks.push(`italics-for-emphasis ×${italics}`);
  const proseForBold = prose.replace(STRUCTURAL_BOLD_EXEMPT, ' ');
  const bold = (proseForBold.match(BOLD) || []).length;
  for (const [re, label] of NOTJUSTBUT) {
    const m = text.match(re) || [];
    if (m.length) hallmarks.push(`${label} ×${m.length}`);
  }
  const dramatic = (text.match(DRAMATIC_FRAGMENT) || []).length;
  if (dramatic) hallmarks.push(`dramatic-fragment ×${dramatic}`);
  const twotoneComma = (text.match(TWOTONE_COMMA) || []).length;
  if (twotoneComma) hallmarks.push(`"it's not X, it's Y" pivot ×${twotoneComma}`);
  const validation = (text.match(VALIDATION_PHRASING) || []).length;
  if (validation) hallmarks.push(`validation-phrasing ×${validation}`);
  for (const [re, label] of FILLER_VOCAB) {
    const m = text.match(re) || [];
    if (m.length) hallmarks.push(`filler-vocab "${label}" ×${m.length}`);
  }
  const emojiHeaders = nonExemptEmoji(headerText(prose)).length;
  if (emojiHeaders) hallmarks.push(`emoji-in-header ×${emojiHeaders}`);
  const emojiProse = nonExemptEmoji(text).length;

  // Overuse counts (visible text), reported per label when non-zero.
  const overuse = {};
  for (const [re, label] of OVERUSE_VOCAB) {
    const n = (text.match(re) || []).length;
    if (n) overuse[label] = n;
  }

  if (emdash || jargon.length || twotoneHP || triad || hallmarks.length || emojiProse || bold || Object.keys(overuse).length) {
    findings[rel] = { emdash, jargon, twotoneHP, triad, hallmarks, emojiProse, bold, overuse };
  }
}

if (UPDATE) {
  const baseline = {};
  for (const [rel, f] of Object.entries(findings)) {
    // Overuse debt: only counts that exceed the cap need shielding.
    const overDebt = {};
    for (const [k, v] of Object.entries(f.overuse || {})) if (v > OVERUSE_CAP) overDebt[k] = v;
    const debt = f.emdash + f.jargon.length + f.bold + Object.keys(overDebt).length;
    if (debt) {
      baseline[rel] = { emdash: f.emdash, jargon: f.jargon.length, bold: f.bold };
      if (Object.keys(overDebt).length) baseline[rel].overuse = overDebt;
    }
  }
  writeFileSync(BASELINE_PATH, JSON.stringify(baseline, null, 2) + '\n');
  console.log(`copy-hallmarks: baseline written for ${Object.keys(baseline).length} file(s).`);
  process.exit(0);
}

const baseline = existsSync(BASELINE_PATH) ? JSON.parse(readFileSync(BASELINE_PATH, 'utf8')) : {};
const failures = [];
const improvements = [];
const advisories = [];

for (const [rel, f] of Object.entries(findings)) {
  const b = baseline[rel] || { emdash: 0, jargon: 0, bold: 0 };
  const bBold = b.bold || 0;
  if (f.emdash > b.emdash) failures.push(`${rel}: ${f.emdash} em-dash(es) in visible text (baseline ${b.emdash})`);
  else if (f.emdash < b.emdash) improvements.push(`${rel}: em-dash ${b.emdash} -> ${f.emdash}`);
  if (f.jargon.length > b.jargon) failures.push(`${rel}: build jargon in visible text: ${f.jargon.join('; ')} (baseline ${b.jargon})`);
  if (f.bold > bBold) failures.push(`${rel}: ${f.bold} bold/strong hit(s) in visible text (baseline ${bBold})`);
  else if (f.bold < bBold) improvements.push(`${rel}: bold ${bBold} -> ${f.bold}`);
  // Overuse: allowed = baselined count if shielded, else OVERUSE_CAP. Ratchet down.
  const bOver = b.overuse || {};
  for (const [k, v] of Object.entries(f.overuse || {})) {
    const allowed = bOver[k] != null ? bOver[k] : OVERUSE_CAP;
    if (v > allowed) failures.push(`${rel}: "${k}" ×${v} in visible text — overused (max ${allowed})`);
    else if (bOver[k] != null && v < bOver[k]) improvements.push(`${rel}: "${k}" ${bOver[k]} -> ${v}`);
  }
  // ANTI-AI-TELL categories: zero-tolerance, no baseline, always fail if present.
  if (f.hallmarks.length) failures.push(`${rel}: ANTI-AI-TELL hit(s): ${f.hallmarks.join('; ')}`);
  // HIGH-PRECISION twotone: zero-tolerance, no baseline.
  if (f.twotoneHP) failures.push(`${rel}: ${f.twotoneHP} HIGH-PRECISION twotone construction(s) ("It is not X. It is Y." family) — rewrite as a direct statement`);
  if (f.triad) advisories.push(`${rel}: ${f.triad} possible rule-of-three triad(s)`);
  if (f.emojiProse) advisories.push(`${rel}: ${f.emojiProse} emoji glyph(s) in body text (advisory — see script header comment)`);
}
for (const rel of Object.keys(baseline)) {
  if (!findings[rel]) improvements.push(`${rel}: clean (baseline entry can be dropped)`);
}

if (advisories.length) {
  console.log(`copy-hallmarks ADVISORY (not failing):\n  ` + advisories.join('\n  '));
}
if (improvements.length) {
  console.log(`copy-hallmarks: ${improvements.length} file(s) beat the baseline — tighten with --update:\n  ` + improvements.slice(0, 10).join('\n  '));
}
if (failures.length) {
  console.error(`\ncopy-hallmarks: ${failures.length} FAILURE(s) — AI-writing hallmarks in reader-facing copy:\n  ` + failures.join('\n  '));
  console.error(`\nFix the copy (see CLAUDE.md ANTI-AI-TELL COPY BAN). Em-dashes/jargon/bold: baseline burns down with --update. ANTI-AI-TELL hits (italics-emphasis, "not just X but", "it's not X, it's Y" pivot, dramatic fragments, validation-phrasing, filler-vocab, emoji-in-headers): zero-tolerance, no baseline — rewrite the copy.`);
  process.exit(1);
}
console.log(`copy-hallmarks: OK (${Object.keys(baseline).length} baselined file(s) within budget, 0 ANTI-AI-TELL hits).`);
