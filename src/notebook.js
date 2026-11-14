// ---------------------------------------------------------------------------
// Notebook — "things I read and learn", opened by the notebook on the table.
//
// Each entry is a self-contained HTML page under public/learning/ (served at
// the root, so `file` is a root-relative path). Clicking a card opens it in an
// in-modal iframe reader; the back chip returns to the grid. To add an entry,
// drop the page in public/learning/ and append one object to NOTEBOOK_ENTRIES.
// Each entry has a `date` (YYYY-MM-DD); cards are shown newest first.
// ---------------------------------------------------------------------------

export const NOTEBOOK_ENTRIES = [
    {
        title: "From Neurons to Transformers",
        blurb: "Eighty years of one argument — should a network pass the signal straight through, or loop it back? From the perceptron to Mamba.",
        tags: ["deep learning", "history"],
        file: "learning/from-neurons-to-transformers.html",
        date: "2026-08-11",
    },
    {
        title: "Combinatorial Surfaces",
        blurb: "How to say \"surface\" using nothing but sets of vertices. Simplices, links, the manifold condition, and the halfedge mesh that stores it all.",
        tags: ["geometry", "discrete diff geo"],
        file: "learning/combinatorial-surfaces.html",
        date: "2026-09-08",
    },
    {
        title: "LoRA: Low-Rank Adaptation",
        blurb: "Fine-tune a giant language model by learning only a tiny low-rank correction to each weight matrix: 10,000× fewer trainable numbers, same accuracy.",
        tags: ["paper of the day", "fine-tuning"],
        file: "learning/paper-2026-11-10-lora-low-rank-adaptation-of-large-language-models.html",
        date: "2026-11-10",
    },
    {
        title: "Soft Actor-Critic",
        blurb: "A robot-learning method rewards the agent for keeping its actions as random as it can while still succeeding, and that makes learning from saved past experience both fast and reliable.",
        tags: ["paper of the day", "reinforcement-learning"],
        file: "learning/paper-2026-11-02-soft-actor-critic-off-policy-maximum-entropy-deep.html",
        date: "2026-11-02",
    },
    {
        title: "nnU-Net",
        blurb: "Instead of hand-designing a network for every medical image segmentation task, nnU-Net reads a dataset's properties and configures a standard U-Net pipeline by itself, and it won most of the benchmarks it entered.",
        tags: ["paper of the day", "medical imaging"],
        file: "learning/paper-2026-11-04-nnu-net-self-adapting-framework-for-u-net-based-me.html",
        date: "2026-11-04",
    },
    {
        title: "A3C: Asynchronous Methods for Deep RL",
        blurb: "Running sixteen game-playing agents in parallel on one CPU, all updating one shared neural network, makes their training data varied enough to learn stably without storing past experience, and beat GPU-trained agents on Atari games in half the time.",
        tags: ["paper of the day", "reinforcement-learning"],
        file: "learning/paper-2026-11-05-asynchronous-methods-for-deep-reinforcement-learni.html",
        date: "2026-11-05",
    },
    {
        title: "Mean Teacher",
        blurb: "For semi-supervised learning, a 'teacher' network whose weights are a running average of the student's supplies the targets on unlabeled images, beating the previous best while using a fraction of the labels.",
        tags: ["paper of the day", "semi-supervised"],
        file: "learning/paper-2026-11-08-weight-averaged-consistency-targets-improve-semi-s.html",
        date: "2026-11-08",
    },
    {
        title: "STGCN: Traffic Forecasting on Road Graphs",
        blurb: "Treating highway sensors as points on a road network and filtering their readings with simple matrix polynomials lets a model predict traffic speeds 45 minutes ahead more accurately than earlier methods, and train about 14 times faster.",
        tags: ["paper of the day", "graphs"],
        file: "learning/paper-2026-11-09-spatio-temporal-graph-convolutional-networks-a-dee.html",
        date: "2026-11-09",
    },
    {
        title: "Training image classifiers to resist adversarial attacks",
        blurb: "Image classifiers can be fooled by pixel changes too small to see, and this paper makes them much harder to fool by training them on the most damaging small change it can find for each training image.",
        tags: ["paper of the day", "robustness"],
        file: "learning/paper-2026-11-01-towards-deep-learning-models-resistant-to-adversar.html",
        date: "2026-11-01",
    },
    {
        title: "Deep learning reads diabetic eye photos",
        blurb: "A neural network trained on 128,000 photos of the back of the eye, each graded by ophthalmologists, picked out diabetic patients who need a specialist almost as reliably as a panel of those doctors.",
        tags: ["paper of the day", "medical-imaging"],
        file: "learning/paper-2026-11-07-development-and-validation-of-a-deep-learning-algo.html",
        date: "2026-11-07",
    },
    {
        title: "Image Data Augmentation",
        blurb: "A survey of the ways to turn a small set of training photos into a much larger one (mirroring, cropping, colour shifts, blanked-out patches, blended images and computer-generated fakes) and how much each one helps image-recognition networks.",
        tags: ["paper of the day", "computer-vision"],
        file: "learning/paper-2026-11-03-a-survey-on-image-data-augmentation-for-deep-learn.html",
        date: "2026-11-03",
    },
    {
        title: "Classifying brain signals for brain–computer interfaces",
        blurb: "A survey of ten years of methods for reading a user's intent from scalp brain recordings finds that classifiers which keep adapting during use, and ones that compare recordings through the geometry of their channel-to-channel covariance, work best, while deep learning had not yet beaten them.",
        tags: ["paper of the day", "brain-computer interfaces"],
        file: "learning/paper-2026-11-11-a-review-of-classification-algorithms-for-eeg-base.html",
        date: "2026-11-11",
    },
    {
        title: "Physics-informed machine learning",
        blurb: "A review of training neural networks to obey known physical laws as well as fit measurements, so one method can both simulate a system and recover its unknown parameters from scarce, noisy data.",
        tags: ["paper of the day", "scientific ml"],
        file: "learning/paper-2026-11-13-physics-informed-machine-learning.html",
        date: "2026-11-13",
    },
    {
        title: "Quantum machine learning",
        blurb: "A review of how quantum computers could speed up machine learning by holding a billion-entry data vector in about thirty quantum bits and doing linear algebra on it directly, and of the fine print (loading the data, reading out the answer) that decides whether the speedup survives.",
        tags: ["paper of the day", "quantum"],
        file: "learning/paper-2026-11-14-quantum-machine-learning.html",
        date: "2026-11-14",
    },
];

const SHOWN = [...NOTEBOOK_ENTRIES].sort((a, b) => (b.date || "").localeCompare(a.date || ""));

function formatDate(iso) {
    if (!iso) return "";
    const [y, m, d] = iso.split("-").map(Number);
    return new Date(y, m - 1, d).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

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
    grid.innerHTML = SHOWN.map((entry, i) => `
        <button class="notebook-card" type="button" data-entry="${i}">
            ${entry.date ? `<time class="notebook-card-date" datetime="${escapeHtml(entry.date)}">${escapeHtml(formatDate(entry.date))}</time>` : ""}
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
        openReader(SHOWN[Number(card.dataset.entry)]);
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
