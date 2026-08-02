#!/usr/bin/env node
/**
 * build-tickets.js
 *
 * Reads the Obsidian vault's flat Tickets/ folder, keeps only `visibility: public`
 * items, and writes public/tickets.json for the 3D site to render.
 *
 * The vault is the single source of truth. This script is the publish step:
 * private tickets never leave the machine because they are filtered out here,
 * before anything is written into the site's served directory.
 *
 * No dependencies. Run:  node scripts/build-tickets.js
 * Override the vault path with the VAULT env var if it moves.
 */

const fs = require('fs');
const path = require('path');

const VAULT =
  process.env.VAULT ||
  path.join(require('os').homedir(), 'Downloads', '2026');

const TICKETS_DIR = path.join(VAULT, 'Tickets');
const OUT_FILE = path.join(__dirname, '..', 'public', 'tickets.json');

// Fields we serialize. Anything else in the frontmatter stays private by omission.
const STRING_FIELDS = [
  'id', 'title', 'category', 'project', 'milestone',
  'status', 'visibility', 'done_when', 'created',
];

/**
 * Minimal YAML-frontmatter parser. We control the ticket schema (see the tickets
 * skill), so this only needs to handle `key: value` and `key: [a, b]` — not the
 * whole YAML spec. Keeping it tiny is deliberate: no dependency to audit.
 */
function parseFrontmatter(raw) {
  const match = raw.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;

  const data = {};
  for (const line of match[1].split('\n')) {
    const idx = line.indexOf(':');
    if (idx === -1) continue;

    const key = line.slice(0, idx).trim();
    let value = line.slice(idx + 1).trim();

    if (value.startsWith('[') && value.endsWith(']')) {
      value = value
        .slice(1, -1)
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
    } else if (value.startsWith('"') && value.endsWith('"')) {
      value = value.slice(1, -1);
    }

    data[key] = value;
  }
  return data;
}

function build() {
  if (!fs.existsSync(TICKETS_DIR)) {
    console.error(`No Tickets/ folder at ${TICKETS_DIR}. Set VAULT to your vault root.`);
    // Write an empty board rather than crashing the site build.
    fs.writeFileSync(OUT_FILE, JSON.stringify({ tickets: [], generated: new Date().toISOString() }, null, 2));
    return;
  }

  const files = fs.readdirSync(TICKETS_DIR).filter((f) => f.endsWith('.md'));
  const tickets = [];
  let skipped = 0;

  for (const file of files) {
    const raw = fs.readFileSync(path.join(TICKETS_DIR, file), 'utf8');
    const fm = parseFrontmatter(raw);
    if (!fm || !fm.id) continue;

    // The privacy mechanism, in one line: private tickets are dropped here.
    if (fm.visibility !== 'public') {
      skipped++;
      continue;
    }

    const ticket = {};
    for (const key of STRING_FIELDS) {
      if (fm[key] !== undefined) ticket[key] = fm[key];
    }
    if (fm.estimate !== undefined) ticket.estimate = Number(fm.estimate);
    if (Array.isArray(fm.blocks)) ticket.blocks = fm.blocks;

    // Pull the "closed by <sha>" line the post-commit hook appends, if present,
    // so the board can later show cycle time. Cheap to capture now.
    const closedMatch = raw.match(/closed by\s+([0-9a-f]{4,40})/i);
    if (closedMatch) ticket.closed_by = closedMatch[1];

    tickets.push(ticket);
  }

  // Stable order: by numeric id so the JSON diff is readable in git.
  tickets.sort((a, b) => {
    const na = Number(String(a.id).replace(/\D/g, ''));
    const nb = Number(String(b.id).replace(/\D/g, ''));
    return na - nb;
  });

  const payload = {
    generated: new Date().toISOString(),
    count: tickets.length,
    tickets,
  };

  fs.mkdirSync(path.dirname(OUT_FILE), { recursive: true });
  fs.writeFileSync(OUT_FILE, JSON.stringify(payload, null, 2));
  console.log(
    `Wrote ${tickets.length} public tickets to ${path.relative(process.cwd(), OUT_FILE)} (${skipped} private skipped).`
  );
}

build();
