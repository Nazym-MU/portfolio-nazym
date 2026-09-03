// ---------------------------------------------------------------------------
// Study plan grid (the "Study" tab on the ticket board)
//
// A GitHub-contributions-style grid over the study schedule. Reads
// public/study-plan.json, produced at build time from the Obsidian vault's
// `Study plan/` folder by scripts/build-study-plan.js.
//
// STRICTLY READ-ONLY. There is no edit affordance and no write path: notes are
// written in Obsidian, committed, and published by `npm run study:publish`.
//
// Cell states:
//   done     - a note exists for that date with `done: true`
//   missed   - a past date with no note, or `done: false`
//   future   - after today; visibly distinct from missed so a gap in the grid
//              reads as "not yet" rather than "failed"
//   rest     - Sunday; muted, no task, no popover
// ---------------------------------------------------------------------------

import katex from "katex";
import "katex/dist/katex.min.css";

const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const MONTH_LABELS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

let studyData = null;
let studyLoading = null;

function escapeHtml(str) {
    return String(str ?? "").replace(/[&<>"']/g, (c) => (
        { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
    ));
}

export function loadStudyData() {
    if (studyData) return Promise.resolve(studyData);
    if (studyLoading) return studyLoading;
    studyLoading = fetch("study-plan.json", { cache: "no-store" })
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status))))
        .then((data) => { studyData = data; return data; })
        .catch((err) => {
            console.error("Failed to load study-plan.json:", err);
            // Do not cache the failure, so reopening the tab retries.
            studyLoading = null;
            throw err;
        });
    return studyLoading;
}

export function getStudyData() {
    return studyData;
}

// ---- Date helpers ---------------------------------------------------------
// Everything is done in UTC on `YYYY-MM-DD` strings so the grid does not shift
// by a day depending on the viewer's timezone.

function parseISO(s) {
    return new Date(`${s}T00:00:00Z`);
}

function toISO(d) {
    return d.toISOString().slice(0, 10);
}

function addDays(d, n) {
    const x = new Date(d);
    x.setUTCDate(x.getUTCDate() + n);
    return x;
}

// Monday-first row index: JS getUTCDay() is 0=Sun..6=Sat, we want 0=Mon..6=Sun.
function rowIndex(d) {
    return (d.getUTCDay() + 6) % 7;
}

// Local calendar date, not UTC: "today" should mean the viewer's today.
function todayISO() {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, "0");
    const d = String(now.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
}

function formatDate(iso) {
    const d = parseISO(iso);
    return `${WEEKDAY_LABELS[rowIndex(d)]} ${d.getUTCDate()} ${MONTH_LABELS[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

// ---- Markdown + math rendering -------------------------------------------

/**
 * Render note markdown. Deliberately small: the notes are mine, the input is
 * escaped either way, and pulling in a full markdown library for headings,
 * lists, code and emphasis is not worth the bundle.
 *
 * Math is extracted BEFORE escaping and re-inserted after, so KaTeX sees the
 * raw TeX and the HTML escaper never mangles a `<` inside `$...$`.
 */
function renderMarkdown(src) {
    if (!src) return "";

    // 1. Pull math out, leaving placeholders that survive escaping untouched.
    const math = [];
    let text = src.replace(/\$\$([\s\S]+?)\$\$|\$([^$\n]+?)\$/g, (_, block, inline) => {
        math.push({ tex: block ?? inline, display: block !== undefined });
        return ` @@MATH${math.length - 1}@@ `;
    });

    // 2. Wikilinks: strip the brackets, keep the text (no resolution, by design).
    text = text.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (_, target, alias) => alias || target);

    text = escapeHtml(text);

    // 3. Inline code, then bold/italic. Code first so `*` inside code is literal.
    const code = [];
    text = text.replace(/`([^`\n]+)`/g, (_, c) => {
        code.push(c);
        return ` @@CODE${code.length - 1}@@ `;
    });
    text = text
        .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
        .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>");

    // 4. Block structure: headings, bullets, paragraphs.
    const blocks = text.split(/\n{2,}/).map((block) => {
        const lines = block.split("\n");

        const heading = lines[0].match(/^(#{1,4})\s+(.*)$/);
        if (heading && lines.length === 1) {
            const level = Math.min(heading[1].length + 2, 6);
            return `<h${level} class="study-note-h">${heading[2]}</h${level}>`;
        }

        if (lines.every((l) => /^\s*[-*]\s+/.test(l))) {
            const items = lines
                .map((l) => `<li>${l.replace(/^\s*[-*]\s+/, "")}</li>`)
                .join("");
            return `<ul class="study-note-list">${items}</ul>`;
        }

        return `<p>${lines.join("<br>")}</p>`;
    });

    let html = blocks.join("");

    html = html.replace(/@@CODE(\d+)@@/g, (_, i) => `<code>${escapeHtml(code[+i])}</code>`);

    // 5. Put the math back, now rendered by KaTeX.
    html = html.replace(/@@MATH(\d+)@@/g, (_, i) => {
        const { tex, display } = math[+i];
        try {
            return katex.renderToString(tex, { displayMode: display, throwOnError: false });
        } catch {
            // A malformed formula should show as source, not break the popover.
            return `<code>${escapeHtml(tex)}</code>`;
        }
    });

    return html;
}

// ---- Grid construction ----------------------------------------------------

/**
 * Lay the plan out into week columns. Column 0 is the week containing the first
 * planned day; leading days before the start are rendered as empty padding so
 * the first cell sits on its true weekday row, exactly like GitHub.
 */
function buildWeeks(days) {
    const byDate = new Map(days.map((d) => [d.date, d]));
    const start = parseISO(days[0].date);
    const end = parseISO(days[days.length - 1].date);

    // Back up to the Monday of the first week.
    let cursor = addDays(start, -rowIndex(start));

    const weeks = [];
    while (cursor <= end) {
        const week = { days: [] };
        for (let i = 0; i < 7; i++) {
            week.days.push(byDate.get(toISO(cursor)) || null); // null = padding
            cursor = addDays(cursor, 1);
        }
        weeks.push(week);
    }
    return weeks;
}

function cellState(day, today) {
    if (!day) return "pad";
    if (parseISO(day.date).getUTCDay() === 0) return "rest"; // Sunday
    if (day.done) return "done";
    if (day.date > today) return "future";
    return "missed";
}

/** Completed days, current streak, and days left - the summary line. */
function computeStats(days, today) {
    const completed = days.filter((d) => d.done).length;

    // Streak: walk backwards from today over days that had a task. Sundays are
    // rest days, so they are skipped rather than treated as a break.
    //
    // Today itself is skipped when it is not yet done: the day is still in
    // progress, and letting it break the streak would show 0 every morning
    // until the task is finished. An already-done today does count.
    let streak = 0;
    const past = days.filter((d) => d.date <= today);
    for (let i = past.length - 1; i >= 0; i--) {
        const d = past[i];
        if (parseISO(d.date).getUTCDay() === 0) continue;
        if (d.done) streak++;
        else if (d.date === today) continue;
        else break;
    }

    const remaining = days.filter(
        (d) => d.date > today && parseISO(d.date).getUTCDay() !== 0
    ).length;

    return { completed, streak, remaining };
}

// ---- Rendering ------------------------------------------------------------

export function renderStudyView(data) {
    const days = (data && data.days) || [];
    if (!days.length) {
        return `<div class="board-empty">No study plan yet.</div>`;
    }

    const today = todayISO();
    const weeks = buildWeeks(days);
    const { completed, streak, remaining } = computeStats(days, today);

    // Month labels sit above the column where a new month first appears.
    const monthCells = weeks.map((w, i) => {
        const first = w.days.find(Boolean);
        if (!first) return `<span class="study-month"></span>`;
        const d = parseISO(first.date);
        const prev = i > 0 ? weeks[i - 1].days.find(Boolean) : null;
        const isNew = !prev || parseISO(prev.date).getUTCMonth() !== d.getUTCMonth();
        return `<span class="study-month">${isNew ? MONTH_LABELS[d.getUTCMonth()] : ""}</span>`;
    }).join("");

    // A phase band above the columns: each week takes the phase of its first
    // planned day, so the boundary between phases is visible at a glance.
    const phases = [...new Set(days.map((d) => d.phase))];
    const phaseCells = weeks.map((w) => {
        const first = w.days.find(Boolean);
        const idx = first ? phases.indexOf(first.phase) : -1;
        return `<span class="study-phase-cell" data-phase="${idx}"></span>`;
    }).join("");

    const columns = weeks.map((w) => {
        const cells = w.days.map((day) => {
            const state = cellState(day, today);
            if (state === "pad") return `<span class="study-cell is-pad"></span>`;
            if (state === "rest") {
                return `<span class="study-cell is-rest" title="${day.date} - rest day"></span>`;
            }
            const impl = day.implement ? " has-impl" : "";
            const isToday = day.date === today ? " is-today" : "";
            return `<button type="button" class="study-cell is-${state}${impl}${isToday}" data-date="${day.date}" aria-label="${day.date}"></button>`;
        }).join("");
        return `<div class="study-week">${cells}</div>`;
    }).join("");

    const legendPhases = phases.map((p, i) =>
        `<span class="study-legend-phase"><i data-phase="${i}"></i>${escapeHtml(p)}</span>`
    ).join("");

    return `
        <div class="study">
            <div class="study-summary">
                <span><strong>${completed}</strong> days completed</span>
                <span><strong>${streak}</strong> day streak</span>
                <span><strong>${remaining}</strong> days remaining</span>
            </div>
            <div class="study-scroll">
                <div class="study-grid-wrap">
                    <div class="study-side">
                        <span class="study-corner"></span>
                        ${WEEKDAY_LABELS.map((l, i) =>
                            `<span class="study-weekday">${i % 2 === 0 ? l : ""}</span>`
                        ).join("")}
                    </div>
                    <div class="study-main">
                        <div class="study-phases">${phaseCells}</div>
                        <div class="study-months">${monthCells}</div>
                        <div class="study-weeks">${columns}</div>
                    </div>
                </div>
            </div>
            <div class="study-legend">
                ${legendPhases}
                <span class="study-legend-spacer"></span>
                <span class="study-legend-key"><i class="study-swatch is-missed"></i>Not done</span>
                <span class="study-legend-key"><i class="study-swatch is-future"></i>Upcoming</span>
                <span class="study-legend-key"><i class="study-swatch is-done"></i>Done</span>
            </div>
            <div class="study-popover" id="study-popover" hidden></div>
        </div>`;
}

// ---- Popover --------------------------------------------------------------

function closePopover() {
    const pop = document.getElementById("study-popover");
    if (!pop) return;
    pop.hidden = true;
    pop.innerHTML = "";
    document.querySelectorAll(".study-cell.is-open").forEach((c) => c.classList.remove("is-open"));
}

function openPopover(cell, day) {
    const pop = document.getElementById("study-popover");
    if (!pop) return;

    document.querySelectorAll(".study-cell.is-open").forEach((c) => c.classList.remove("is-open"));
    cell.classList.add("is-open");

    // No "no note yet" placeholder by design - an empty day shows just the task.
    const note = day.note
        ? `<div class="study-note">${renderMarkdown(day.note)}</div>`
        : "";

    pop.innerHTML = `
        <button type="button" class="study-pop-close" aria-label="Close">&times;</button>
        <div class="study-pop-date">${formatDate(day.date)}</div>
        <div class="study-pop-phase">${escapeHtml(day.phase)}${day.implement ? `<span class="study-pop-impl">implement</span>` : ""}</div>
        <div class="study-pop-task">${escapeHtml(day.task)}</div>
        ${note}`;

    // Measure before positioning: the popover must be laid out to have a size.
    pop.hidden = false;
    pop.style.left = "0px";
    pop.style.top = "0px";

    const wrap = pop.offsetParent || pop.parentElement;
    const wrapBox = wrap.getBoundingClientRect();
    const cellBox = cell.getBoundingClientRect();
    const popBox = pop.getBoundingClientRect();

    // Anchor to the cell, then nudge back inside the panel if it would overflow.
    let left = cellBox.left - wrapBox.left + cellBox.width / 2 - popBox.width / 2;
    left = Math.max(8, Math.min(left, wrapBox.width - popBox.width - 8));

    // Prefer below the cell; flip above when there is not enough room.
    let top = cellBox.bottom - wrapBox.top + 10;
    if (cellBox.bottom + popBox.height + 20 > window.innerHeight) {
        top = cellBox.top - wrapBox.top - popBox.height - 10;
    }

    pop.style.left = `${left}px`;
    pop.style.top = `${Math.max(8, top)}px`;
}

/**
 * One delegated listener for the whole tab. Safe to call after every render:
 * a dataset flag keeps repeated renders from stacking listeners.
 */
export function wireStudyInteractions(getData) {
    const viewEl = document.getElementById("board-view");
    if (!viewEl || viewEl.dataset.studyWired) return;
    viewEl.dataset.studyWired = "1";

    viewEl.addEventListener("click", (e) => {
        if (e.target.closest(".study-pop-close")) {
            closePopover();
            return;
        }
        // A click inside the popover should not close it.
        if (e.target.closest(".study-popover")) return;

        const cell = e.target.closest(".study-cell[data-date]");
        if (!cell) {
            closePopover();
            return;
        }
        if (cell.classList.contains("is-open")) {
            closePopover();
            return;
        }
        const day = (getData()?.days || []).find((d) => d.date === cell.dataset.date);
        if (day) openPopover(cell, day);
    });

    // Escape closes; only one popover is ever open, so this is unambiguous.
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") closePopover();
    });
}

export { closePopover as closeStudyPopover };
