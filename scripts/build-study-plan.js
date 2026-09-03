#!/usr/bin/env node
/**
 * build-study-plan.js
 *
 * Reads the Obsidian vault's `Study plan/` folder and writes public/study-plan.json
 * for the site's Study tab to render.
 *
 * Same contract as build-tickets.js: the vault is the source of truth, this script
 * is the publish step, and ONLY `Study plan/` is ever read. No other vault folder
 * is touched, so nothing else can leak into the site.
 *
 * The site is read-only. Nothing here or in the browser ever writes to the vault.
 *
 * No dependencies. Run:  node scripts/build-study-plan.js
 * Override the vault path with the VAULT env var if it moves.
 */

const fs = require('fs');
const path = require('path');

const VAULT =
  process.env.VAULT ||
  path.join(require('os').homedir(), 'Downloads', '2026');

const PLAN_DIR = path.join(VAULT, 'Study plan');
const PLAN_FILE = path.join(PLAN_DIR, 'plan.md');
const NOTES_DIR = path.join(PLAN_DIR, 'notes');
const OUT_FILE = path.join(__dirname, '..', 'public', 'study-plan.json');

/**
 * Parse the pipe table in plan.md into {date, phase, task, implement} rows.
 * We control this file's shape (it is generated), so a full markdown parser
 * would be overkill — split on `|` and skip the header/separator rows.
 */
function parsePlan(raw) {
  const rows = [];
  for (const line of raw.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed.startsWith('|')) continue;

    const cells = trimmed.slice(1, -1).split('|').map((c) => c.trim());
    if (cells.length < 4) continue;

    const [date, phase, task, implement] = cells;
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) continue; // skips header + `---` row

    rows.push({
      date,
      phase,
      task,
      implement: /^y(es)?$/i.test(implement),
    });
  }
  return rows;
}

/**
 * A note is `notes/<date>.md` with frontmatter `date:` and `done:`.
 * Returns { done, body } — body is the raw markdown after the frontmatter,
 * rendered client-side (KaTeX for math, wikilink brackets stripped).
 */
function parseNote(raw) {
  const match = raw.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  if (!match) return { done: false, body: raw.trim() || null };

  let done = false;
  for (const line of match[1].split('\n')) {
    const idx = line.indexOf(':');
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    const value = line.slice(idx + 1).trim().replace(/^["']|["']$/g, '');
    if (key === 'done') done = /^(true|yes)$/i.test(value);
  }

  const body = match[2].trim();
  return { done, body: body || null };
}

function build() {
  if (!fs.existsSync(PLAN_FILE)) {
    // No vault here — normal on a deploy box, which has the repo but not the
    // Obsidian vault. The committed public/study-plan.json is the source of
    // truth in that case, so LEAVE IT ALONE rather than blanking the grid.
    console.warn(
      `No plan.md at ${PLAN_FILE}; keeping the committed public/study-plan.json as-is. ` +
      `(This is expected on a deploy box without the vault.)`
    );
    return;
  }

  const days = parsePlan(fs.readFileSync(PLAN_FILE, 'utf8'));

  let noteCount = 0;
  for (const day of days) {
    const noteFile = path.join(NOTES_DIR, `${day.date}.md`);
    if (fs.existsSync(noteFile)) {
      const { done, body } = parseNote(fs.readFileSync(noteFile, 'utf8'));
      day.done = done;
      day.note = body;
      noteCount++;
    } else {
      day.done = false;
      day.note = null;
    }
  }

  const payload = {
    generated: new Date().toISOString(),
    start: days.length ? days[0].date : null,
    end: days.length ? days[days.length - 1].date : null,
    count: days.length,
    days,
  };

  fs.mkdirSync(path.dirname(OUT_FILE), { recursive: true });
  fs.writeFileSync(OUT_FILE, JSON.stringify(payload, null, 2));
  console.log(
    `Wrote ${days.length} study-plan days (${noteCount} with notes, ` +
    `${days.filter((d) => d.done).length} done) to ${path.relative(process.cwd(), OUT_FILE)}.`
  );
}

build();
