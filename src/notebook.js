// ---------------------------------------------------------------------------
// Notebook — "things I read and learn", opened by the notebook on the table.
//
// Each entry is a self-contained HTML page under public/learning/ (served at
// the root, so `file` is a root-relative path). Clicking a card opens it in an
// in-modal iframe reader; the back chip returns to the grid. To add an entry,
// drop the page in public/learning/ and append one object to NOTEBOOK_ENTRIES.
// ---------------------------------------------------------------------------

export const NOTEBOOK_ENTRIES = [
    {
        title: "From Neurons to Transformers",
        blurb: "Eighty years of one argument — should a network pass the signal straight through, or loop it back? From the perceptron to Mamba.",
        tags: ["deep learning", "history"],
        file: "learning/from-neurons-to-transformers.html",
    },
];

function escapeHtml(str) {
    return String(str ?? "").replace(/[&<>"']/g, (c) => (
        { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
    ));
}

// Wires the Notebook modal once at startup. `modalEl` is `.modal.notebook`.
export function initNotebook(modalEl) {
    const home = modalEl.querySelector("#notebook-home");
    const reader = modalEl.querySelector("#notebook-reader");
    const grid = modalEl.querySelector("#notebook-grid");
    const frame = modalEl.querySelector("#notebook-frame");
    const readerTitle = modalEl.querySelector("#notebook-reader-title");
    const backBtn = modalEl.querySelector("#notebook-back");

    // ---- Card grid (entries + a ghost "more soon" placeholder) ----
    grid.innerHTML = NOTEBOOK_ENTRIES.map((entry, i) => `
        <button class="notebook-card" type="button" data-entry="${i}">
            <h4 class="notebook-card-title">${escapeHtml(entry.title)}</h4>
            <p class="notebook-card-blurb">${escapeHtml(entry.blurb)}</p>
            <div class="notebook-card-tags">
                ${entry.tags.map((t) => `<span class="notebook-tag">${escapeHtml(t)}</span>`).join("")}
            </div>
        </button>`).join("") + `
        <div class="notebook-card notebook-card-ghost" aria-hidden="true">
            <p class="notebook-ghost-text">More soon — the reading never stops.</p>
        </div>`;

    function openReader(entry) {
        readerTitle.textContent = entry.title;
        frame.src = entry.file; // lazy: only loaded when a card is opened
        home.hidden = true;
        reader.hidden = false;
        modalEl.classList.add("reading");
        // The hand-drawn page wants room — open the window maximized.
        modalEl.classList.add("maximized");
        modalEl.querySelector(".modal-content").scrollTop = 0;
    }

    function closeReader() {
        reader.hidden = true;
        home.hidden = false;
        modalEl.classList.remove("reading");
        frame.src = "about:blank"; // drop the page so reopening starts fresh
        readerTitle.textContent = "";
    }

    grid.addEventListener("click", (e) => {
        const card = e.target.closest(".notebook-card[data-entry]");
        if (!card) return;
        openReader(NOTEBOOK_ENTRIES[Number(card.dataset.entry)]);
    });

    backBtn.addEventListener("click", () => {
        closeReader();
        // Zoom the window back down with the grid; the green control re-toggles.
        modalEl.classList.remove("maximized");
    });

    // The generic close button in main.js only hides the modal (and removes
    // `maximized`). Watch for that hide and reset to the grid AFTER the fade,
    // so reopening always shows the cards and never a stale reader.
    new MutationObserver(() => {
        if (modalEl.style.display === "none" && !reader.hidden) closeReader();
    }).observe(modalEl, { attributes: true, attributeFilter: ["style"] });
}
