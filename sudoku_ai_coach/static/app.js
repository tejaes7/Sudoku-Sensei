/**
 * Sudoku Coach — Frontend Application Logic
 * Explainable, patient Sudoku tutor backed by the CSP coach API.
 */

const ROWS = "ABCDEFGHI";
const COLS = "123456789";

// =============================================================================
// User Profile & LocalStorage State
// =============================================================================
const PROFILE_KEY = "sudoku_coach_profile_v3";

const DEFAULT_PROFILE = {
  level: null,                // "beginner" | "intermediate" | "advanced" | null
  preference: "puzzles",      // "refresher" | "puzzles"
  currentLessonId: "lesson_1_intro",
  completedLessons: [],
  currentPuzzleId: null,
  generatedPuzzle: null,     // metadata of the last generated puzzle, so it can be restored
  solvedPuzzles: [],
  learnedTechniques: [],
  stats: { solved: 0, hints: 0, mistakes: 0 }
};

const ALL_TECHNIQUES = [
  "Full House", "Naked Single", "Hidden Single",
  "Naked Pair", "Hidden Pair", "Pointing Pair",
  "Box/Line Reduction", "Naked Triple", "X-Wing"
];

function freshProfile() {
  return JSON.parse(JSON.stringify(DEFAULT_PROFILE));
}

let userProfile = loadProfile();

function loadProfile() {
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    if (raw) {
      const saved = JSON.parse(raw);
      const base = freshProfile();
      return { ...base, ...saved, stats: { ...base.stats, ...(saved.stats || {}) } };
    }
  } catch (e) {
    console.warn("Could not load profile:", e);
  }
  return freshProfile();
}

function saveProfile() {
  try {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(userProfile));
  } catch (e) {
    console.warn("Could not save profile:", e);
  }
}

// =============================================================================
// Runtime State
// =============================================================================
let currentBoard = null;
let selectedCell = null;
let currentGridSize = 9;
let isPencilMode = false;
let cellPencilMarks = {}; // { "A1": Set([1, 4]) }
let mode = "none";        // "lesson" | "puzzle"
let wasComplete = false;

// Lesson State
let activeLesson = null;
let lessonsCatalog = [];

// Graded Puzzles State
let bankedPuzzles = [];

// Hint Ladder State
let currentHintStage = 0; // 0: idle, 1: nudge, 2: technique, 3: reveal
let activeHintData = null;
let currentWalkthroughIndex = 0;
let activeMistakeCell = null;

// Quiz State
let quizQuestions = [];
let quizCurrentIndex = 0;
let quizAnswers = {};

// =============================================================================
// DOM References
// =============================================================================
const $ = (id) => document.getElementById(id);

const screens = ["screen-welcome", "screen-level-select", "screen-skill-check", "screen-preference", "screen-workspace"].map($);

const navBrand = $("nav-brand");
const navWorkspaceControls = $("nav-workspace-controls");
const navLessonControls = $("nav-lesson-controls");
const navPuzzleControls = $("nav-puzzle-controls");
const lessonSelect = $("lesson-select");
const levelBadgeText = $("level-badge-text");
const puzzleSelect = $("puzzle-select");

const btnWelcomeStart = $("btn-welcome-start");
const welcomeReturningArea = $("welcome-returning-area");

const quizProgressText = $("quiz-progress-text");
const quizProgressBar = $("quiz-progress-bar");
const quizBody = $("quiz-body");
const quizQuestionTitle = $("quiz-question-title");
const quizOptionsList = $("quiz-options-list");
const quizResultArea = $("quiz-result-area");
const quizResultTitle = $("quiz-result-title");
const quizResultRationale = $("quiz-result-rationale");
const btnQuizAccept = $("btn-quiz-accept");

const workspaceModeTag = $("workspace-mode-tag");
const workspaceItemTitle = $("workspace-item-title");
const selectedCellInfo = $("selected-cell-info");
const statusLineEl = $("status-line");
const gridEl = $("sudoku-grid");
const toolbarRow = $("toolbar-row");
const btnTogglePencil = $("btn-toggle-pencil");
const pencilModeStatus = $("pencil-mode-status");
const numpadContainer = $("numpad-container");
const btnUndo = $("btn-undo");
const btnReset = $("btn-reset");
const btnSolve = $("btn-solve");
const btnGeneratePuzzle = $("btn-generate-puzzle");

const panelLessonView = $("panel-lesson-view");
const panelPuzzleView = $("panel-puzzle-view");
const coachWhatIfView = $("coach-what-if-view");

const lessonStepCounter = $("lesson-step-counter");
const lessonProgressFill = $("lesson-progress-fill");
const lessonTaskTitle = $("lesson-task-title");
const lessonTaskConcept = $("lesson-task-concept");
const lessonTaskPrompt = $("lesson-task-prompt");
const lessonFeedbackBox = $("lesson-feedback-box");
const lessonFeedbackText = $("lesson-feedback-text");
const btnLessonNext = $("btn-lesson-next");

const mistakeAlertCard = $("mistake-alert-card");
const mistakeTitle = $("mistake-title");
const mistakeMessage = $("mistake-message");
const btnClearMistake = $("btn-clear-mistake");

const coachMessage = $("coach-message");
const whyItWorksCard = $("why-it-works-card");
const btnWhyItWorks = $("btn-why-it-works");
const whyContent = $("why-content");

const btnHint = $("btn-hint");
const ladderDots = [$("ladder-dot-1"), $("ladder-dot-2"), $("ladder-dot-3")];
const ladderEmptyState = $("ladder-empty-state");
const ladderNudgeCard = $("ladder-nudge-card");
const ladderNudgeText = $("ladder-nudge-text");
const ladderTechCard = $("ladder-tech-card");
const ladderTechName = $("ladder-tech-name");
const ladderTechDef = $("ladder-tech-def");
const ladderTechMsg = $("ladder-tech-msg");
const ladderRevealCard = $("ladder-reveal-card");
const revealTargetCell = $("reveal-target-cell");
const revealTargetVal = $("reveal-target-val");
const btnApplyReveal = $("btn-apply-reveal");
const walkthroughStepText = $("walkthrough-step-text");
const walkthroughCounter = $("walkthrough-counter");
const btnStepPrev = $("btn-step-prev");
const btnStepNext = $("btn-step-next");

const whatIfCellInput = $("what-if-cell");
const whatIfValInput = $("what-if-val");
const whatIfForm = $("what-if-form");
const whatIfResultArea = $("what-if-result-area");
const whatIfResultText = $("what-if-result-text");

const progressModal = $("progress-modal");
const progCurrentLevel = $("prog-current-level");
const progTechniquesList = $("prog-techniques-list");
const progLessonsList = $("prog-lessons-list");
const statSolved = $("stat-solved");
const statHints = $("stat-hints");
const statMistakes = $("stat-mistakes");

const customModal = $("custom-modal");
const customPuzzleInput = $("custom-puzzle-input");
const customCharCount = $("custom-char-count");
const modalError = $("modal-error");

const confirmModal = $("confirm-modal");
const toastEl = $("toast");

// =============================================================================
// Small helpers
// =============================================================================
async function api(path, body) {
  const opts = body === undefined
    ? {}
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.detail || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return data;
}

function capitalize(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : "";
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function cellEl(id) {
  return $(`cell-${id}`);
}

function addClassToCells(cells, cls) {
  (cells || []).forEach(c => {
    const el = cellEl(c);
    if (el) el.classList.add(cls);
  });
}

function showToast(msg, kind = "") {
  toastEl.textContent = msg;
  toastEl.className = "toast" + (kind ? ` toast-${kind}` : "");
  toastEl.hidden = false;
  clearTimeout(toastEl._timer);
  toastEl._timer = setTimeout(() => { toastEl.hidden = true; }, 3000);
}

// --- Modals ------------------------------------------------------------------
function openModal(modal) {
  modal.hidden = false;
  const focusTarget = modal.querySelector("textarea, input, .btn-primary");
  if (focusTarget) setTimeout(() => focusTarget.focus(), 30);
}

function closeModal(modal) {
  modal.hidden = true;
}

function anyModalOpen() {
  return !progressModal.hidden || !customModal.hidden || !confirmModal.hidden;
}

let confirmResolver = null;

function confirmDialog(title, message, okLabel = "Confirm") {
  $("confirm-title").textContent = title;
  $("confirm-message").textContent = message;
  $("btn-confirm-ok").textContent = okLabel;
  $("btn-confirm-cancel").hidden = false;
  openModal(confirmModal);
  return new Promise(resolve => { confirmResolver = resolve; });
}

function infoDialog(title, message, okLabel = "Continue") {
  const p = confirmDialog(title, message, okLabel);
  $("btn-confirm-cancel").hidden = true;
  return p;
}

function settleConfirm(result) {
  closeModal(confirmModal);
  if (confirmResolver) {
    const r = confirmResolver;
    confirmResolver = null;
    r(result);
  }
}

// =============================================================================
// Initialization & Screen Flow
// =============================================================================
function setupApp() {
  attachEventListeners();
  setupAiTeacher();
  initFlow();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", setupApp);
} else {
  setupApp();
}

function initFlow() {
  const returning = !!(userProfile && userProfile.level);
  btnWelcomeStart.hidden = returning;
  welcomeReturningArea.hidden = !returning;
  showScreen("screen-welcome");
}

function showScreen(screenId) {
  screens.forEach(s => {
    const active = s.id === screenId;
    s.classList.toggle("active", active);
    s.hidden = !active;
  });

  navWorkspaceControls.hidden = screenId !== "screen-workspace";
  if (screenId === "screen-workspace") updateLevelBadge();
  window.scrollTo(0, 0);
}

function updateLevelBadge() {
  levelBadgeText.textContent = capitalize(userProfile.level) || "Beginner";
}

// =============================================================================
// Event Wiring
// =============================================================================
function attachEventListeners() {
  navBrand.addEventListener("click", initFlow);

  btnWelcomeStart.addEventListener("click", () => showScreen("screen-level-select"));
  $("btn-welcome-continue").addEventListener("click", launchUserPath);
  $("btn-welcome-change-level").addEventListener("click", () => showScreen("screen-level-select"));

  document.querySelectorAll(".level-card").forEach(card => {
    card.addEventListener("click", () => selectLevel(card.dataset.level));
  });

  $("btn-open-skill-check").addEventListener("click", startSkillCheck);
  $("btn-back-from-check").addEventListener("click", () => showScreen("screen-level-select"));
  $("btn-quiz-back").addEventListener("click", () => showScreen("screen-level-select"));
  btnQuizAccept.addEventListener("click", () => selectLevel(btnQuizAccept.dataset.level || "beginner"));

  document.querySelectorAll(".pref-option-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      userProfile.preference = btn.dataset.pref;
      saveProfile();
      if (userProfile.preference === "refresher") {
        startLessonTrack("lesson_1_intro");
      } else {
        startPuzzleTrack();
      }
    });
  });
  $("btn-pref-back").addEventListener("click", () => showScreen("screen-level-select"));

  // Progress modal
  $("btn-level-menu").addEventListener("click", openProgressModal);
  $("btn-nav-progress").addEventListener("click", openProgressModal);
  $("btn-close-progress").addEventListener("click", () => closeModal(progressModal));
  $("btn-done-progress").addEventListener("click", () => closeModal(progressModal));
  $("btn-prog-switch-level").addEventListener("click", () => {
    closeModal(progressModal);
    showScreen("screen-level-select");
  });
  $("btn-reset-progress").addEventListener("click", async () => {
    closeModal(progressModal);
    const ok = await confirmDialog("Reset all progress?", "Your level, completed lessons, learned techniques, and stats will be cleared.", "Reset everything");
    if (ok) {
      userProfile = freshProfile();
      saveProfile();
      initFlow();
      showToast("Progress reset.");
    }
  });

  // Confirm modal
  $("btn-confirm-ok").addEventListener("click", () => settleConfirm(true));
  $("btn-confirm-cancel").addEventListener("click", () => settleConfirm(false));

  // Close modals by clicking the backdrop
  [progressModal, customModal, confirmModal].forEach(m => {
    m.addEventListener("click", (e) => {
      if (e.target !== m) return;
      if (m === confirmModal) settleConfirm(false); else closeModal(m);
    });
  });

  lessonSelect.addEventListener("change", (e) => loadLesson(e.target.value));
  puzzleSelect.addEventListener("change", (e) => {
    const id = e.target.value;
    if (!id) return;
    const gen = userProfile.generatedPuzzle;
    if (id.startsWith("gen_")) {
      if (gen && gen.puzzle_id === id) {
        userProfile.currentPuzzleId = id;
        saveProfile();
        loadGeneratedPuzzle(gen);
      }
      return;
    }
    loadBankedPuzzleById(id);
  });

  btnTogglePencil.addEventListener("click", togglePencilMode);

  numpadContainer.querySelectorAll(".num-btn[data-num]").forEach(btn => {
    btn.addEventListener("click", () => handleDigitInput(parseInt(btn.dataset.num, 10)));
  });
  $("btn-clear-cell").addEventListener("click", () => handleDigitInput(0));

  document.addEventListener("keydown", handleKeyboardShortcuts);

  $("btn-check-move").addEventListener("click", handleCheckMove);
  $("btn-test-move").addEventListener("click", openWhatIfMode);
  whatIfForm.addEventListener("submit", (e) => { e.preventDefault(); runWhatIfSimulation(); });
  $("btn-what-if-cancel").addEventListener("click", closeWhatIfMode);
  $("btn-what-if-back").addEventListener("click", closeWhatIfMode);
  $("btn-what-if-again").addEventListener("click", () => {
    whatIfResultArea.hidden = true;
    whatIfForm.hidden = false;
    clearHighlights();
    whatIfValInput.focus();
  });

  btnHint.addEventListener("click", advanceHintLadder);
  btnClearMistake.addEventListener("click", eraseMistakeCell);
  $("btn-dismiss-mistake").addEventListener("click", () => {
    mistakeAlertCard.hidden = true;
    clearHighlights();
  });
  btnWhyItWorks.addEventListener("click", toggleWhyItWorks);
  btnStepPrev.addEventListener("click", () => navigateWalkthrough(-1));
  btnStepNext.addEventListener("click", () => navigateWalkthrough(1));
  btnApplyReveal.addEventListener("click", applyRevealedMove);

  $("btn-lesson-hint").addEventListener("click", showLessonHint);
  btnLessonNext.addEventListener("click", advanceToNextLesson);

  btnUndo.addEventListener("click", handleUndo);
  btnReset.addEventListener("click", handleReset);
  btnSolve.addEventListener("click", handleSolve);
  btnGeneratePuzzle.addEventListener("click", handleGeneratePuzzle);

  $("btn-custom-puzzle").addEventListener("click", () => {
    modalError.hidden = true;
    updateCustomCount();
    openModal(customModal);
  });
  $("btn-close-modal").addEventListener("click", () => closeModal(customModal));
  $("btn-cancel-modal").addEventListener("click", () => closeModal(customModal));
  $("btn-submit-modal").addEventListener("click", handleCustomPuzzleSubmit);
  customPuzzleInput.addEventListener("input", updateCustomCount);
}

// =============================================================================
// Level Selection Flow
// =============================================================================
function selectLevel(level) {
  const levelChanged = userProfile.level !== level;
  userProfile.level = level;
  if (levelChanged) userProfile.currentPuzzleId = null;
  saveProfile();

  if (level === "beginner") {
    userProfile.preference = "refresher";
    saveProfile();
    startLessonTrack(userProfile.currentLessonId || "lesson_1_intro");
  } else {
    showScreen("screen-preference");
  }
}

function launchUserPath() {
  if (userProfile.level === "beginner" && userProfile.preference !== "puzzles") {
    startLessonTrack(userProfile.currentLessonId || "lesson_1_intro");
  } else {
    startPuzzleTrack();
  }
}

// =============================================================================
// 2-Minute Skill Check Assessment
// =============================================================================
async function startSkillCheck() {
  showScreen("screen-skill-check");
  quizCurrentIndex = 0;
  quizAnswers = {};
  quizResultArea.hidden = true;
  quizBody.hidden = false;
  quizQuestionTitle.textContent = "Loading questions…";
  quizOptionsList.innerHTML = "";

  try {
    const data = await api("/api/teacher/skill-check");
    quizQuestions = data.questions || [];
    renderQuizQuestion();
  } catch (e) {
    showToast("Could not load the skill check.", "error");
  }
}

function renderQuizQuestion() {
  if (quizCurrentIndex >= quizQuestions.length) {
    evaluateQuiz();
    return;
  }

  const q = quizQuestions[quizCurrentIndex];
  const total = quizQuestions.length;
  const currentNum = quizCurrentIndex + 1;

  quizProgressText.textContent = `Question ${currentNum} of ${total}`;
  quizProgressBar.style.width = `${Math.round((quizCurrentIndex / total) * 100) || 4}%`;
  quizQuestionTitle.textContent = q.question;

  quizOptionsList.innerHTML = "";
  q.options.forEach((opt, idx) => {
    const btn = document.createElement("button");
    btn.className = "quiz-option-card";
    btn.style.animationDelay = `${idx * 50}ms`;
    btn.innerHTML = `
      <span class="quiz-opt-letter">${"ABCD"[idx] || idx + 1}</span>
      <span class="quiz-opt-text">${escapeHtml(opt.text)}</span>
    `;
    btn.addEventListener("click", () => {
      quizAnswers[q.id] = opt.id;
      quizCurrentIndex++;
      renderQuizQuestion();
    });
    quizOptionsList.appendChild(btn);
  });
}

async function evaluateQuiz() {
  quizBody.hidden = true;
  quizResultArea.hidden = false;
  quizProgressText.textContent = "Check complete";
  quizProgressBar.style.width = "100%";

  let title = "Beginner Track";
  let rationale = "Start with our guided interactive lessons to build confidence.";
  let level = "beginner";

  try {
    const result = await api("/api/teacher/skill-check", { answers: quizAnswers });
    title = result.recommended_title || title;
    rationale = result.rationale || rationale;
    level = result.recommended_level || level;
  } catch (e) {
    console.warn("Skill check evaluation failed:", e);
  }

  quizResultTitle.textContent = title;
  quizResultRationale.textContent = rationale;
  btnQuizAccept.innerHTML = `Start ${escapeHtml(title)} <span class="btn-arrow">→</span>`;
  btnQuizAccept.dataset.level = level;
}

// =============================================================================
// Workspace mode switching
// =============================================================================
function setWorkspaceMode(newMode) {
  mode = newMode;
  const isLesson = newMode === "lesson";

  panelLessonView.hidden = !isLesson;
  panelPuzzleView.hidden = isLesson;
  coachWhatIfView.hidden = true;

  navLessonControls.hidden = !isLesson;
  navPuzzleControls.hidden = isLesson;
  btnUndo.hidden = isLesson;
  btnSolve.hidden = isLesson;
  btnReset.title = isLesson ? "Restart this lesson" : "Start this puzzle over";
  toolbarRow.hidden = isLesson;
  statusLineEl.hidden = isLesson;

  workspaceModeTag.classList.toggle("tag-lesson", isLesson);
  if (isPencilMode) togglePencilMode(true);
}

// =============================================================================
// Lesson Engine Track (Beginner Curriculum)
// =============================================================================
async function startLessonTrack(lessonId = "lesson_1_intro") {
  showScreen("screen-workspace");
  setWorkspaceMode("lesson");
  workspaceModeTag.textContent = "Guided Lesson";

  try {
    const catData = await api("/api/teacher/lessons");
    lessonsCatalog = (catData.lessons || []).sort((a, b) => a.order - b.order);

    lessonSelect.innerHTML = "";
    lessonsCatalog.forEach(l => {
      const opt = document.createElement("option");
      opt.value = l.lesson_id;
      const done = userProfile.completedLessons.includes(l.lesson_id);
      opt.textContent = `${done ? "✓ " : ""}${l.title}`;
      lessonSelect.appendChild(opt);
    });

    if (!lessonsCatalog.some(l => l.lesson_id === lessonId) && lessonsCatalog.length) {
      lessonId = lessonsCatalog[0].lesson_id;
    }
    await loadLesson(lessonId);
  } catch (e) {
    showToast("Failed to load lessons. Is the server running?", "error");
  }
}

async function loadLesson(lessonId) {
  try {
    const data = await api(`/api/teacher/lesson/${encodeURIComponent(lessonId)}`);
    activeLesson = data.lesson;
    userProfile.currentLessonId = lessonId;
    saveProfile();

    lessonSelect.value = lessonId;

    const total = lessonsCatalog.length || 7;
    workspaceItemTitle.textContent = activeLesson.title;
    lessonStepCounter.textContent = `Lesson ${activeLesson.order} of ${total}`;
    lessonProgressFill.style.width = `${(activeLesson.order / total) * 100}%`;
    lessonTaskTitle.textContent = activeLesson.title;
    lessonTaskConcept.textContent = activeLesson.concept_summary;
    lessonTaskPrompt.textContent = activeLesson.instruction;
    lessonFeedbackBox.hidden = true;
    lessonFeedbackBox.classList.remove("lesson-feedback-success", "lesson-feedback-hint");
    btnLessonNext.hidden = true;
    btnLessonNext.classList.remove("btn-pulse");

    currentGridSize = activeLesson.grid_size;
    selectedCell = null;
    buildGridDOM(currentGridSize);
    populateLessonGrid(activeLesson.initial_grid, activeLesson.clues_mask);
    applyLessonHighlights();

    lessonPencilMarks = new Set();
    if (activeLesson.target_cell) selectCell(activeLesson.target_cell, { silent: true });

    if (activeLesson.lesson_id === "lesson_7_first_puzzle") {
      markLessonComplete();
      btnLessonNext.textContent = "Start my first puzzle →";
      btnLessonNext.hidden = false;
      btnLessonNext.classList.add("btn-pulse");
    }
  } catch (e) {
    showToast("Error loading lesson.", "error");
  }
}

function applyLessonHighlights() {
  clearHighlights();
  if (!activeLesson) return;
  addClassToCells(activeLesson.highlight_cells, "highlight-cause");
  if (activeLesson.target_cell && activeLesson.lesson_id !== "lesson_2_grid") {
    const el = cellEl(activeLesson.target_cell);
    if (el) {
      el.classList.remove("highlight-cause");
      el.classList.add("highlight-target");
    }
  }
}

function populateLessonGrid(gridStr, cluesMask) {
  const size = currentGridSize;
  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      const cellId = ROWS[r] + COLS[c];
      const val = parseInt(gridStr[r * size + c] || "0", 10) || 0;
      const el = cellEl(cellId);
      if (!el) continue;
      el.querySelector(".cell-val").textContent = val !== 0 ? val : "";
      el.classList.toggle("clue", val !== 0);
    }
  }
}

function showLessonHint() {
  if (activeLesson && activeLesson.hint_text) {
    lessonFeedbackBox.hidden = false;
    lessonFeedbackBox.classList.remove("lesson-feedback-success");
    lessonFeedbackBox.classList.add("lesson-feedback-hint");
    lessonFeedbackText.textContent = `💡 ${activeLesson.hint_text}`;
  }
}

let lessonPencilMarks = new Set();

function markLessonComplete() {
  if (!userProfile.completedLessons.includes(activeLesson.lesson_id)) {
    userProfile.completedLessons.push(activeLesson.lesson_id);
    saveProfile();
    const opt = lessonSelect.querySelector(`option[value="${activeLesson.lesson_id}"]`);
    if (opt && !opt.textContent.startsWith("✓")) opt.textContent = `✓ ${opt.textContent}`;
  }
}

async function verifyPencilLesson(cell, val) {
  const result = await api("/api/teacher/lesson/verify", { lesson_id: activeLesson.lesson_id, cell, value: val });
  lessonFeedbackBox.hidden = false;
  lessonFeedbackBox.classList.remove("lesson-feedback-hint", "lesson-feedback-success");
  lessonFeedbackText.textContent = result.message;

  if (result.is_candidate) {
    lessonPencilMarks.add(val);
    cellPencilMarks[cell] = new Set(lessonPencilMarks);
    renderPencilMarks(cell);
  } else if (result.is_candidate === false) {
    const el = cellEl(cell);
    if (el) {
      el.classList.remove("highlight-elimination");
      void el.offsetWidth;
      el.classList.add("highlight-elimination");
      setTimeout(() => el.classList.remove("highlight-elimination"), 900);
    }
  }

  const all = result.candidates || [];
  if (all.length && all.every(d => lessonPencilMarks.has(d))) {
    lessonFeedbackText.textContent = `Perfect — ${cell} can only be ${all.join(" or ")}. ${activeLesson.success_feedback}`;
    lessonFeedbackBox.classList.add("lesson-feedback-success");
    markLessonComplete();
    btnLessonNext.textContent = "Next lesson →";
    btnLessonNext.hidden = false;
    btnLessonNext.classList.add("btn-pulse");
  } else if (result.is_candidate && all.length) {
    lessonFeedbackText.textContent += ` (${lessonPencilMarks.size} of ${all.length} candidates found)`;
  }
}

async function verifyLessonMove(cell, val) {
  if (!activeLesson) return;
  if (activeLesson.lesson_id === "lesson_6_pencil_marks" && val) {
    try { await verifyPencilLesson(cell, val); } catch (e) { showToast("Error checking your note.", "error"); }
    return;
  }

  try {
    const result = await api("/api/teacher/lesson/verify", {
      lesson_id: activeLesson.lesson_id,
      cell,
      value: val
    });

    lessonFeedbackBox.hidden = false;
    lessonFeedbackBox.classList.remove("lesson-feedback-hint");
    lessonFeedbackText.textContent = result.message;

    if (result.completed) {
      if (val) {
        const el = cellEl(cell);
        if (el) {
          el.querySelector(".cell-val").textContent = val;
          el.classList.add("user-move", "just-placed");
          el.classList.remove("highlight-cause");
          el.classList.add("highlight-target");
        }
      }

      markLessonComplete();

      lessonFeedbackBox.classList.add("lesson-feedback-success");
      const isLast = !lessonsCatalog.some(l => l.order === activeLesson.order + 1);
      btnLessonNext.textContent = isLast ? "Start real puzzles →" : "Next lesson →";
      btnLessonNext.hidden = false;
      btnLessonNext.classList.add("btn-pulse");
    } else {
      lessonFeedbackBox.classList.remove("lesson-feedback-success");
      if (val) {
        const el = cellEl(cell);
        if (el) {
          el.classList.remove("highlight-elimination");
          void el.offsetWidth;
          el.classList.add("highlight-elimination");
          setTimeout(() => { el.classList.remove("highlight-elimination"); }, 900);
        }
      }
    }
  } catch (e) {
    showToast("Error checking your answer.", "error");
  }
}

async function advanceToNextLesson() {
  if (!activeLesson) return;
  const nextLesson = lessonsCatalog.find(l => l.order === activeLesson.order + 1);

  if (nextLesson) {
    loadLesson(nextLesson.lesson_id);
  } else {
    await infoDialog(
      "🎉 Foundations complete!",
      "Brilliant — you've finished every beginner lesson. Next up: real graded puzzles, with the hint ladder whenever you need it.",
      "Let's go"
    );
    userProfile.preference = "puzzles";
    userProfile.currentPuzzleId = "beg_1";
    saveProfile();
    startPuzzleTrack();
  }
}

// =============================================================================
// Graded Puzzle Track
// =============================================================================
async function startPuzzleTrack() {
  showScreen("screen-workspace");
  setWorkspaceMode("puzzle");
  activeLesson = null;
  workspaceModeTag.textContent = `${capitalize(userProfile.level || "intermediate")} path`;

  currentGridSize = 9;
  selectedCell = null;
  buildGridDOM(9);
  await loadGradedPuzzlesForLevel(userProfile.level || "intermediate");
}

async function loadGradedPuzzlesForLevel(level) {
  try {
    const data = await api(`/api/teacher/puzzles?level=${encodeURIComponent(level)}`);
    bankedPuzzles = data.puzzles || [];

    puzzleSelect.innerHTML = "";
    bankedPuzzles.forEach((p, i) => {
      const opt = document.createElement("option");
      opt.value = p.puzzle_id;
      const solved = userProfile.solvedPuzzles.includes(p.puzzle_id);
      opt.textContent = `${solved ? "✓ " : ""}${i + 1}. ${p.title} · ${p.clue_count} clues`;
      puzzleSelect.appendChild(opt);
    });

    // Restore the last generated puzzle for this level, if that's where the learner left off
    const gen = userProfile.generatedPuzzle;
    if (gen && gen.puzzle_id === userProfile.currentPuzzleId && gen.difficulty === level) {
      await loadGeneratedPuzzle(gen);
      return;
    }

    // Fall back to the first puzzle if the saved id is not in this level's bank
    const saved = userProfile.currentPuzzleId;
    const targetId = bankedPuzzles.some(p => p.puzzle_id === saved) ? saved : bankedPuzzles[0]?.puzzle_id;
    if (targetId) {
      puzzleSelect.value = targetId;
      await loadBankedPuzzleById(targetId);
    } else {
      workspaceItemTitle.textContent = "No puzzles available";
    }
  } catch (e) {
    showToast("Could not load the puzzle bank.", "error");
  }
}

async function loadBankedPuzzleById(puzzleId) {
  try {
    const data = await api("/api/teacher/load-banked-puzzle", { puzzle_id: puzzleId, session_id: "default" });
    if (data.success) {
      userProfile.currentPuzzleId = puzzleId;
      saveProfile();

      workspaceItemTitle.textContent = data.title || "Puzzle";
      startFreshBoard("New puzzle loaded. Start by scanning for rows, columns, or boxes that are almost full.");
      await refreshBoardState();
    }
  } catch (e) {
    showToast("Error loading puzzle.", "error");
  }
}

function startFreshBoard(message) {
  resetHintLadderUI();
  cellPencilMarks = {};
  selectedCell = null;
  wasComplete = false;
  gridEl.classList.remove("solved");
  document.querySelectorAll(".sudoku-cell").forEach(el => el.classList.remove("selected", "peer", "same-value"));
  selectedCellInfo.textContent = "No square selected";
  coachMessage.textContent = message;
}

// =============================================================================
// Grid Rendering & Selection
// =============================================================================
function buildGridDOM(size = 9) {
  gridEl.innerHTML = "";
  gridEl.classList.toggle("mini-4x4", size === 4);
  gridEl.classList.remove("solved");

  numpadContainer.querySelectorAll(".num-btn[data-num]").forEach(btn => {
    const num = parseInt(btn.dataset.num, 10);
    btn.disabled = size === 4 && num > 4;
    btn.classList.remove("complete");
    const badge = btn.querySelector(".num-remaining");
    if (badge) badge.remove();
  });

  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      const cellId = ROWS[r] + COLS[c];
      const el = document.createElement("div");
      el.className = "sudoku-cell";
      el.id = `cell-${cellId}`;
      el.dataset.cell = cellId;
      el.dataset.row = r;
      el.dataset.col = c;
      el.setAttribute("role", "gridcell");
      el.setAttribute("aria-label", cellId);

      const coordLabel = document.createElement("span");
      coordLabel.className = "cell-coord-label";
      coordLabel.textContent = cellId;
      el.appendChild(coordLabel);

      const pencilGrid = document.createElement("div");
      pencilGrid.className = "cell-pencil-grid";
      pencilGrid.id = `pencil-${cellId}`;
      for (let n = 1; n <= 9; n++) {
        const pNum = document.createElement("span");
        pNum.className = "pencil-num";
        pNum.dataset.num = n;
        pencilGrid.appendChild(pNum);
      }
      el.appendChild(pencilGrid);

      const valSpan = document.createElement("span");
      valSpan.className = "cell-val";
      el.appendChild(valSpan);

      el.addEventListener("click", () => selectCell(cellId));
      gridEl.appendChild(el);
    }
  }
}

function getCellValue(cellId) {
  const el = cellEl(cellId);
  if (!el) return 0;
  return parseInt(el.querySelector(".cell-val").textContent, 10) || 0;
}

function isClueCell(cellId) {
  const el = cellEl(cellId);
  return !!(el && el.classList.contains("clue"));
}

function selectCell(cellId, { silent = false } = {}) {
  selectedCell = cellId;
  const size = currentGridSize;
  const box = Math.sqrt(size);
  const r = ROWS.indexOf(cellId[0]);
  const c = COLS.indexOf(cellId[1]);
  const val = getCellValue(cellId);

  document.querySelectorAll(".sudoku-cell").forEach(el => {
    const er = +el.dataset.row;
    const ec = +el.dataset.col;
    const isPeer = er === r || ec === c ||
      (Math.floor(er / box) === Math.floor(r / box) && Math.floor(ec / box) === Math.floor(c / box));
    el.classList.toggle("selected", el.dataset.cell === cellId);
    el.classList.toggle("peer", isPeer && el.dataset.cell !== cellId);
    const ev = parseInt(el.querySelector(".cell-val").textContent, 10) || 0;
    el.classList.toggle("same-value", val !== 0 && ev === val && el.dataset.cell !== cellId);
  });

  const clueNote = isClueCell(cellId) ? " · clue" : "";
  selectedCellInfo.textContent = `Square ${cellId}${clueNote}`;

  if (!silent && activeLesson && activeLesson.lesson_id === "lesson_2_grid") {
    verifyLessonMove(cellId, null);
  }
}

// =============================================================================
// Digit Entry, Pencil Marks, and Move Execution
// =============================================================================
function togglePencilMode(silent = false) {
  isPencilMode = !isPencilMode;
  btnTogglePencil.classList.toggle("active", isPencilMode);
  btnTogglePencil.setAttribute("aria-pressed", String(isPencilMode));
  pencilModeStatus.textContent = isPencilMode ? "On" : "Off";
  if (silent !== true) showToast(`Pencil marks ${isPencilMode ? "on — digits add notes" : "off"}`);
}

async function handleDigitInput(val) {
  if (!selectedCell) {
    showToast("Pick a square on the board first.");
    return;
  }
  if (val > currentGridSize) return;

  if (mode === "lesson") {
    if (val === 0) return;
    verifyLessonMove(selectedCell, val);
    return;
  }

  if (isClueCell(selectedCell)) {
    showToast(`${selectedCell} is a starting clue and can't be changed.`);
    return;
  }

  if (isPencilMode && val >= 1 && val <= 9) {
    if (getCellValue(selectedCell) !== 0) {
      showToast("Erase the number first to add pencil marks.");
      return;
    }
    togglePencilMark(selectedCell, val);
    return;
  }

  if (val === 0 && getCellValue(selectedCell) === 0) {
    if (cellPencilMarks[selectedCell]) {
      delete cellPencilMarks[selectedCell];
      renderPencilMarks(selectedCell);
    }
    return;
  }

  await executeUserMove(selectedCell, val);
}

function togglePencilMark(cellId, digit) {
  if (!cellPencilMarks[cellId]) cellPencilMarks[cellId] = new Set();
  const marks = cellPencilMarks[cellId];
  if (marks.has(digit)) marks.delete(digit); else marks.add(digit);
  renderPencilMarks(cellId);
}

function renderPencilMarks(cellId) {
  const pencilGrid = $(`pencil-${cellId}`);
  if (!pencilGrid) return;
  const marks = cellPencilMarks[cellId] || new Set();
  pencilGrid.querySelectorAll(".pencil-num").forEach(span => {
    const d = parseInt(span.dataset.num, 10);
    span.textContent = marks.has(d) ? d : "";
  });
}

// Remove a placed digit from the pencil marks of every peer
function prunePeerPencilMarks(cell, val) {
  const r = ROWS.indexOf(cell[0]);
  const c = COLS.indexOf(cell[1]);
  Object.keys(cellPencilMarks).forEach(id => {
    const ir = ROWS.indexOf(id[0]);
    const ic = COLS.indexOf(id[1]);
    const peer = ir === r || ic === c || (Math.floor(ir / 3) === Math.floor(r / 3) && Math.floor(ic / 3) === Math.floor(c / 3));
    if (peer && cellPencilMarks[id].delete(val)) renderPencilMarks(id);
  });
}

async function executeUserMove(cell, val) {
  try {
    let checkData = null;

    if (val !== 0) {
      checkData = await api("/api/teacher/check-move", { cell, value: val });

      if (!checkData.valid) {
        userProfile.stats.mistakes++;
        saveProfile();

        if (checkData.case === "A") {
          showMistakeAlert(cell, checkData.message, checkData.conflict_cell, {
            title: checkData.title || "Rule conflict",
            canErase: false
          });
          coachMessage.textContent = "That number already appears in the same row, column, or box. Take another look at the highlighted squares.";
          return;
        }
        if (checkData.case === "B") {
          showMistakeAlert(cell, checkData.message, null, {
            title: checkData.title || "A gentle dead end",
            canErase: false
          });
          coachMessage.textContent = "Not quite — that number doesn't break a rule yet, but it can't be right. Want a nudge from the hint ladder?";
          return;
        }
        showToast(checkData.message || "That move isn't allowed.", "error");
        return;
      }
    }

    const data = await api("/api/move", { cell, value: val, session_id: "default" });
    if (!data.success) {
      showToast(data.message || "Move not applied.", "error");
      return;
    }

    if (cellPencilMarks[cell]) {
      delete cellPencilMarks[cell];
      renderPencilMarks(cell);
    }
    if (val !== 0) prunePeerPencilMarks(cell, val);

    resetHintLadderUI();
    await refreshBoardState();

    const el = cellEl(cell);
    if (el && val !== 0) {
      el.classList.add("just-placed");
      setTimeout(() => el.classList.remove("just-placed"), 400);
    }

    if (val !== 0 && checkData && checkData.valid) {
      coachMessage.textContent = checkData.message || `Nice — ${cell} is ${val}.`;
      showWhyItWorks(checkData.why_it_works);
    } else if (val === 0) {
      coachMessage.textContent = `${cell} erased.`;
    }
    selectCell(cell, { silent: true });
  } catch (e) {
    showToast(e.message || "Error processing move.", "error");
  }
}

let activeWhyData = null;

function showWhyItWorks(whyData) {
  if (!whyData || !whyData.steps || whyData.steps.length === 0) return;
  activeWhyData = whyData;
  whyItWorksCard.querySelector(".why-badge").textContent = whyData.forced === false
    ? "✓ Correct — not forced yet"
    : `✓ Correct${whyData.technique ? ` · ${whyData.technique}` : ""}`;
  whyContent.innerHTML = `<ol>${whyData.steps.map(s => `<li>${escapeHtml(s)}</li>`).join("")}</ol>`;
  whyContent.hidden = true;
  btnWhyItWorks.textContent = "Why does this work?";
  whyItWorksCard.hidden = false;
}

function toggleWhyItWorks() {
  whyContent.hidden = !whyContent.hidden;
  btnWhyItWorks.textContent = whyContent.hidden ? "Why does this work?" : "Hide explanation";
  clearHighlights();
  if (!whyContent.hidden && activeWhyData) {
    addClassToCells(activeWhyData.cause_cells, "highlight-cause");
    addClassToCells([activeWhyData.cell], "highlight-target");
  }
}

// =============================================================================
// Hint Ladder: Nudge -> Technique -> Reveal
// =============================================================================
async function advanceHintLadder() {
  const nextStage = Math.min(currentHintStage + 1, 3);
  btnHint.disabled = true;

  try {
    const data = await api("/api/teacher/hint-ladder", {
      stage: nextStage,
      user_level: userProfile.level || "intermediate",
      session_id: "default"
    });

    if (data.has_user_mistake && data.mistake) {
      showMistakeAlert(data.mistake.mistake_cell, data.mistake.explanation, data.mistake.conflicting_cell, {
        title: "Let's fix this first",
        canErase: true
      });
      coachMessage.textContent = "Before the next hint, there's a square that needs another look.";
      return;
    }

    if (data.is_solved) {
      coachMessage.textContent = "The puzzle is completely solved! Outstanding deduction.";
      return;
    }

    currentHintStage = nextStage;
    userProfile.stats.hints++;
    saveProfile();
    activeHintData = data;
    renderHintLadderStage(data);
  } catch (e) {
    showToast("Could not retrieve a hint.", "error");
  } finally {
    btnHint.disabled = false;
  }
}

function showLadderCard(card) {
  ladderEmptyState.hidden = true;
  [ladderNudgeCard, ladderTechCard, ladderRevealCard].forEach(c => { c.hidden = c !== card; });
}

function renderHintLadderStage(data) {
  clearHighlights();
  mistakeAlertCard.hidden = true;
  whyItWorksCard.hidden = true;
  updateLadderDots(data.stage);

  if (data.stage === 1 && data.nudge) {
    showLadderCard(ladderNudgeCard);
    ladderNudgeText.textContent = data.nudge.message;
    coachMessage.textContent = "Here's where I'd look first. The amber squares are worth studying.";
    btnHint.textContent = "Show me the technique";
    addClassToCells(data.nudge.highlight_cells, "highlight-cause");
  } else if (data.stage === 2 && data.technique_card) {
    showLadderCard(ladderTechCard);
    ladderTechName.textContent = data.technique_card.name;
    ladderTechDef.textContent = data.technique_card.definition;
    ladderTechMsg.textContent = data.technique_card.message;
    coachMessage.textContent = `This step uses a technique called ${data.technique_card.name}.`;
    btnHint.textContent = "Reveal the answer";

    if (data.technique_name && !userProfile.learnedTechniques.includes(data.technique_name)) {
      userProfile.learnedTechniques.push(data.technique_name);
      saveProfile();
    }
    addClassToCells(data.technique_card.highlight_cause_cells, "highlight-cause");
    addClassToCells(data.technique_card.highlight_target_cells, "highlight-target");
  } else if (data.stage === 3 && data.reveal) {
    showLadderCard(ladderRevealCard);
    const targets = data.reveal.target_cells || [];
    const value = data.reveal.target_value;
    revealTargetCell.textContent = targets.join(", ");
    revealTargetVal.textContent = value || "elimination";
    btnApplyReveal.hidden = !(value && targets.length === 1);
    coachMessage.textContent = "Here's the full deduction. Step through it, then place the number yourself or let me do it.";
    btnHint.textContent = "Hint for the next step";
    currentHintStage = 0;

    currentWalkthroughIndex = 0;
    updateWalkthroughStep();

    addClassToCells(data.reveal.cause_cells, "highlight-cause");
    addClassToCells(targets, "highlight-target");
  }
}

async function applyRevealedMove() {
  if (!activeHintData || !activeHintData.reveal) return;
  const cell = (activeHintData.reveal.target_cells || [])[0];
  const value = activeHintData.reveal.target_value;
  if (!cell || !value) return;
  const reveal = activeHintData.reveal;
  const techniqueName = activeHintData.technique_name;
  selectCell(cell, { silent: true });
  await executeUserMove(cell, value);
  // Explain the placement with the deduction chain the coach just taught
  if (getCellValue(cell) === value && (reveal.walkthrough_steps || []).length) {
    showWhyItWorks({
      cell, value, forced: true, technique: techniqueName,
      steps: reveal.walkthrough_steps, cause_cells: reveal.cause_cells || []
    });
  }
}

function updateWalkthroughStep() {
  if (!activeHintData || !activeHintData.reveal) return;
  const steps = activeHintData.reveal.walkthrough_steps || [];
  if (steps.length === 0) {
    walkthroughStepText.textContent = "";
    walkthroughCounter.textContent = "";
    return;
  }

  walkthroughStepText.textContent = steps[currentWalkthroughIndex];
  walkthroughCounter.textContent = `${currentWalkthroughIndex + 1} / ${steps.length}`;
  btnStepPrev.disabled = currentWalkthroughIndex === 0;
  btnStepNext.disabled = currentWalkthroughIndex === steps.length - 1;
}

function navigateWalkthrough(delta) {
  if (!activeHintData || !activeHintData.reveal) return;
  const steps = activeHintData.reveal.walkthrough_steps || [];
  currentWalkthroughIndex = Math.max(0, Math.min(steps.length - 1, currentWalkthroughIndex + delta));
  updateWalkthroughStep();
}

function updateLadderDots(stage) {
  ladderDots.forEach((dot, i) => dot.classList.toggle("active", stage >= i + 1));
}

function resetHintLadderUI() {
  currentHintStage = 0;
  activeHintData = null;
  updateLadderDots(0);
  ladderNudgeCard.hidden = true;
  ladderTechCard.hidden = true;
  ladderRevealCard.hidden = true;
  ladderEmptyState.hidden = false;
  btnHint.textContent = "💡 Ask for a hint";
  btnHint.disabled = false;
  mistakeAlertCard.hidden = true;
  whyItWorksCard.hidden = true;
  clearHighlights();
}

// =============================================================================
// Mistake Detection
// =============================================================================
function showMistakeAlert(cell, message, conflictCell = null, { title = "Let's look at that again", canErase = true } = {}) {
  activeMistakeCell = cell;
  mistakeTitle.textContent = title;
  mistakeMessage.textContent = message;
  btnClearMistake.hidden = !(canErase && getCellValue(cell) !== 0);
  whyItWorksCard.hidden = true;
  mistakeAlertCard.hidden = false;

  clearHighlights();
  addClassToCells([cell], "highlight-elimination");
  if (conflictCell) addClassToCells([conflictCell], "highlight-elimination");
}

async function eraseMistakeCell() {
  if (!activeMistakeCell) return;
  const cell = activeMistakeCell;
  activeMistakeCell = null;
  await executeUserMove(cell, 0);
  mistakeAlertCard.hidden = true;
  coachMessage.textContent = "Mistake cleared — the board is consistent again.";
}

// =============================================================================
// Board State Refresh
// =============================================================================
async function refreshBoardState() {
  try {
    currentBoard = await api("/api/board");
    renderBoard(currentBoard);
    btnUndo.disabled = !currentBoard.move_count;
    if (selectedCell) selectCell(selectedCell, { silent: true });
    checkForCompletion(currentBoard);
  } catch (e) {
    console.error("Failed to refresh board state:", e);
  }
}

function renderBoard(b) {
  if (!b || !Array.isArray(b.grid)) return;

  const counts = Array(10).fill(0);
  for (let r = 0; r < 9; r++) {
    for (let c = 0; c < 9; c++) {
      const cellId = ROWS[r] + COLS[c];
      const val = (b.grid[r] && b.grid[r][c]) || 0;
      const isClue = !!(b.clues && b.clues[r] && b.clues[r][c]);
      const el = cellEl(cellId);
      if (!el) continue;

      el.querySelector(".cell-val").textContent = val !== 0 ? val : "";
      el.classList.toggle("clue", isClue);
      el.classList.toggle("user-move", !isClue && val !== 0);
      if (val === 0) renderPencilMarks(cellId);
      counts[val]++;
    }
  }

  // Numpad: show how many of each digit remain and fade completed digits
  numpadContainer.querySelectorAll(".num-btn[data-num]").forEach(btn => {
    const n = parseInt(btn.dataset.num, 10);
    const remaining = Math.max(0, 9 - counts[n]);
    let badge = btn.querySelector(".num-remaining");
    if (!badge) {
      badge = document.createElement("span");
      badge.className = "num-remaining";
      btn.appendChild(badge);
    }
    badge.textContent = remaining || "";
    btn.classList.toggle("complete", remaining === 0);
  });

  const empty = b.empty_count ?? b.unassigned_count ?? 0;
  const moves = b.move_count || 0;
  statusLineEl.textContent = `${empty} empty · ${moves} move${moves === 1 ? "" : "s"}`;
}

async function checkForCompletion(b) {
  if (!b || !b.is_complete) {
    wasComplete = false;
    return;
  }
  if (wasComplete) return;
  wasComplete = true;
  gridEl.classList.remove("solved");
  void gridEl.offsetWidth;
  gridEl.classList.add("solved");
  clearHighlights();

  const id = userProfile.currentPuzzleId;
  if (id && !userProfile.solvedPuzzles.includes(id)) userProfile.solvedPuzzles.push(id);
  userProfile.stats.solved++;
  saveProfile();
  markPuzzleOptionSolved(id);
  coachMessage.textContent = "You solved it! Every square was filled with pure logic. Tap “✦ New puzzle” for a fresh one at your level, or pick one from the menu.";
  showToast("🎉 Puzzle solved — great work!", "success");
}

function markPuzzleOptionSolved(id) {
  if (!id) return;
  const opt = puzzleSelect.querySelector(`option[value="${id}"]`);
  if (opt && !opt.textContent.startsWith("✓")) opt.textContent = `✓ ${opt.textContent}`;
}

function clearHighlights() {
  document.querySelectorAll(".sudoku-cell").forEach(el => {
    el.classList.remove("highlight-target", "highlight-cause", "highlight-elimination");
  });
}

// =============================================================================
// AI Teacher Chat (CSP engine grounds + verifies, LLM explains)
// =============================================================================
let aiChatHistory = [];
const aiChatLog = $("ai-chat-log");
const aiChatForm = $("ai-chat-form");
const aiChatInput = $("ai-chat-input");
const btnAiSend = $("btn-ai-send");

async function setupAiTeacher() {
  aiChatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    sendAiTeacherMessage(aiChatInput.value);
  });
  document.querySelectorAll(".ai-quick-btn").forEach(btn => {
    btn.addEventListener("click", () => sendAiTeacherMessage(btn.dataset.q));
  });
  try {
    const status = await api("/api/teacher/ai-status");
    const pill = $("ai-teacher-mode");
    pill.textContent = status.llm_enabled ? `CSP + ${status.model}` : "CSP engine";
    pill.title = status.mode;
    pill.classList.toggle("ai-mode-llm", status.llm_enabled);
  } catch (e) { /* status pill stays neutral */ }
}

function appendAiMessage(role, text, meta) {
  const el = document.createElement("div");
  el.className = `ai-msg ${role === "user" ? "ai-msg-user" : "ai-msg-teacher"}`;
  el.textContent = text;
  if (meta) {
    const tag = document.createElement("span");
    tag.className = "ai-msg-meta";
    tag.textContent = meta;
    el.appendChild(tag);
  }
  aiChatLog.appendChild(el);
  aiChatLog.scrollTop = aiChatLog.scrollHeight;
  return el;
}

async function sendAiTeacherMessage(raw) {
  let message = (raw || "").trim();
  if (!message) return;
  if (message === "What can the selected square be?") {
    if (!selectedCell) { showToast("Select a square on the board first."); return; }
    message = `What can ${selectedCell} be?`;
  }
  aiChatInput.value = "";
  appendAiMessage("user", message);
  const pending = appendAiMessage("teacher", "Thinking…");
  pending.classList.add("ai-msg-pending");
  btnAiSend.disabled = true;

  try {
    const data = await api("/api/teacher/chat", {
      message,
      history: aiChatHistory,
      selected_cell: selectedCell,
      user_level: userProfile.level || "intermediate"
    });
    pending.remove();
    let meta;
    if (data.source === "llm") {
      const n = data.verification ? data.verification.claims_checked : 0;
      meta = `${data.model} · verified by CSP engine${n ? ` (${n} claim${n > 1 ? "s" : ""} checked)` : ""}`;
    } else {
      meta = data.llm_rejected ? "CSP engine · LLM reply rejected by verifier" : "CSP engine";
    }
    appendAiMessage("teacher", data.reply, meta);
    aiChatHistory.push({ role: "user", content: message }, { role: "assistant", content: data.reply });
    aiChatHistory = aiChatHistory.slice(-8);

    clearHighlights();
    addClassToCells(data.highlight_cause_cells, "highlight-cause");
    addClassToCells(data.highlight_target_cells, "highlight-target");
  } catch (e) {
    pending.remove();
    appendAiMessage("teacher", "Sorry, I couldn't reach the engine. Is the server running?");
  } finally {
    btnAiSend.disabled = false;
  }
}

// =============================================================================
// Keyboard Shortcuts
// =============================================================================
function handleKeyboardShortcuts(e) {
  if (e.key === "Escape") {
    if (!confirmModal.hidden) settleConfirm(false);
    else if (!customModal.hidden) closeModal(customModal);
    else if (!progressModal.hidden) closeModal(progressModal);
    return;
  }

  if (anyModalOpen()) {
    if (e.key === "Enter" && !confirmModal.hidden) { e.preventDefault(); settleConfirm(true); }
    return;
  }
  if (!screens[4].classList.contains("active")) return;
  const tag = e.target.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
    if (mode === "puzzle" && !btnUndo.disabled) { e.preventDefault(); handleUndo(); }
    return;
  }
  if (e.ctrlKey || e.metaKey || e.altKey) return;

  if (e.key >= "1" && e.key <= "9") {
    handleDigitInput(parseInt(e.key, 10));
    return;
  }
  if (e.key === "0" || e.key === "Backspace" || e.key === "Delete") {
    e.preventDefault();
    handleDigitInput(0);
    return;
  }
  if (e.key.toLowerCase() === "p" && mode === "puzzle") {
    togglePencilMode();
    return;
  }

  const moves = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] };
  if (moves[e.key]) {
    e.preventDefault();
    const max = currentGridSize - 1;
    if (!selectedCell) { selectCell("A1"); return; }
    const [dr, dc] = moves[e.key];
    const r = Math.max(0, Math.min(max, ROWS.indexOf(selectedCell[0]) + dr));
    const c = Math.max(0, Math.min(max, COLS.indexOf(selectedCell[1]) + dc));
    selectCell(ROWS[r] + COLS[c]);
  }
}

// =============================================================================
// What-If Sandbox
// =============================================================================
function openWhatIfMode() {
  coachWhatIfView.hidden = false;
  panelPuzzleView.hidden = true;
  whatIfForm.hidden = false;
  whatIfResultArea.hidden = true;
  whatIfCellInput.value = selectedCell || "";
  whatIfValInput.value = "";
  (selectedCell ? whatIfValInput : whatIfCellInput).focus();
}

function closeWhatIfMode() {
  coachWhatIfView.hidden = true;
  panelPuzzleView.hidden = false;
  clearHighlights();
}

async function runWhatIfSimulation() {
  const cell = (whatIfCellInput.value || "").trim().toUpperCase();
  const val = parseInt(whatIfValInput.value, 10);

  if (!/^[A-I][1-9]$/.test(cell)) {
    showToast("Enter a square like D7 (row A–I, column 1–9).");
    whatIfCellInput.focus();
    return;
  }
  if (!(val >= 1 && val <= 9)) {
    showToast("Enter a number from 1 to 9.");
    whatIfValInput.focus();
    return;
  }
  if (isClueCell(cell) || getCellValue(cell) !== 0) {
    showToast(`${cell} already has a number. Pick an empty square.`);
    return;
  }

  try {
    const data = await api("/api/what-if", { cell, value: val });
    const ok = !!data.success && !data.contradiction;
    const steps = data.cascade_steps || [];

    let html = `<span class="result-head">${ok ? "✓ Consistent so far" : "✗ Leads to a contradiction"}</span>${escapeHtml(data.conclusion || "")}`;
    if (steps.length) {
      const shown = steps.slice(0, 12).map(s => `<li>${escapeHtml(describeCascadeStep(s))}</li>`).join("");
      const more = steps.length > 12 ? `<li>…and ${steps.length - 12} more</li>` : "";
      html += `<ol class="cascade-list">${shown}${more}</ol>`;
    }

    whatIfResultText.className = `what-if-result ${ok ? "is-ok" : "is-bad"}`;
    whatIfResultText.innerHTML = html;
    whatIfForm.hidden = true;
    whatIfResultArea.hidden = false;

    clearHighlights();
    addClassToCells(steps.filter(s => !s.contradiction && s.cell).slice(0, 12).map(s => s.cell), "highlight-cause");
    addClassToCells([cell], "highlight-target");
    if (data.culprit_cell && data.culprit_cell !== cell) addClassToCells([data.culprit_cell], "highlight-elimination");
  } catch (e) {
    showToast(e.message || "Simulation error.", "error");
  }
}

function describeCascadeStep(s) {
  if (typeof s === "string") return s;
  return s.explanation || s.reason || s.message ||
    [s.cell, s.step_type && s.step_type.replace(/_/g, " "), s.value].filter(Boolean).join(" · ");
}

// =============================================================================
// Progress Modal
// =============================================================================
function openProgressModal() {
  progCurrentLevel.textContent = capitalize(userProfile.level) || "Not chosen yet";
  statSolved.textContent = userProfile.stats.solved;
  statHints.textContent = userProfile.stats.hints;
  statMistakes.textContent = userProfile.stats.mistakes;

  progTechniquesList.innerHTML = "";
  ALL_TECHNIQUES.forEach(t => {
    const badge = document.createElement("span");
    const learned = userProfile.learnedTechniques.includes(t);
    badge.className = `tech-tag-badge${learned ? " learned" : ""}`;
    badge.textContent = `${learned ? "✓ " : ""}${t}`;
    progTechniquesList.appendChild(badge);
  });

  progLessonsList.innerHTML = "";
  const lessons = lessonsCatalog.length > 0 ? lessonsCatalog : [
    { lesson_id: "lesson_1_intro", title: "1. What Sudoku Is (The One Rule)" },
    { lesson_id: "lesson_2_grid", title: "2. Reading the Grid" },
    { lesson_id: "lesson_3_full_house", title: "3. The Easiest Win: Full House" },
    { lesson_id: "lesson_4_hidden_single", title: "4. Scanning: Hidden Single" },
    { lesson_id: "lesson_5_naked_single", title: "5. Cell Elimination: Naked Single" },
    { lesson_id: "lesson_6_pencil_marks", title: "6. Pencil Marks" },
    { lesson_id: "lesson_7_first_puzzle", title: "7. First Full Puzzle" }
  ];

  lessons.forEach(l => {
    const done = userProfile.completedLessons.includes(l.lesson_id);
    const item = document.createElement("div");
    item.className = `lesson-check-item${done ? " done" : ""}`;
    item.innerHTML = `<span class="check-mark">✓</span><span>${escapeHtml(l.title)}</span>`;
    progLessonsList.appendChild(item);
  });

  openModal(progressModal);
}

// =============================================================================
// Helper Controls (Check, Undo, Reset, Solve, Custom)
// =============================================================================
async function handleCheckMove() {
  if (!selectedCell) {
    showToast("Select a square first.");
    return;
  }
  if (isClueCell(selectedCell)) {
    showToast(`${selectedCell} is a starting clue — it's always correct.`);
    return;
  }
  const val = getCellValue(selectedCell);
  if (val === 0) {
    showToast("That square is empty — place a number first.");
    return;
  }
  try {
    const data = await api("/api/teacher/check-move", { cell: selectedCell, value: val });
    coachMessage.textContent = data.message;
    if (data.valid) {
      showToast(`✓ ${selectedCell} = ${val} is correct.`, "success");
    } else {
      showMistakeAlert(selectedCell, data.message, data.conflict_cell, { title: data.title || "Not quite", canErase: true });
    }
  } catch (e) {
    showToast("Could not check that square.", "error");
  }
}

async function handleUndo() {
  try {
    const data = await api("/api/undo", {});
    if (data.success) {
      resetHintLadderUI();
      await refreshBoardState();
      if (selectedCell) selectCell(selectedCell, { silent: true });
    } else {
      showToast("Nothing to undo.");
    }
  } catch (e) {
    showToast("Undo failed.", "error");
  }
}

async function handleReset() {
  if (mode === "lesson") {
    if (activeLesson) loadLesson(activeLesson.lesson_id);
    return;
  }
  const ok = await confirmDialog("Start this puzzle over?", "All your placed numbers and pencil marks will be cleared. Starting clues stay.", "Reset puzzle");
  if (!ok) return;
  try {
    const data = await api("/api/reset", {});
    if (data.success) {
      startFreshBoard("Fresh start! Scan for the most constrained rows, columns, and boxes.");
      await refreshBoardState();
    }
  } catch (e) {
    showToast("Reset failed.", "error");
  }
}

async function handleSolve() {
  const ok = await confirmDialog("Let the solver finish?", "The CSP solver (constraint propagation + search) will fill in every remaining square. This won't count as a puzzle you solved.", "Solve it");
  if (!ok) return;
  try {
    const data = await api("/api/solve", {});
    if (data.success) {
      wasComplete = true; // don't count solver completions as user solves
      resetHintLadderUI();
      cellPencilMarks = {};
      await refreshBoardState();
      gridEl.classList.remove("solved");
      void gridEl.offsetWidth;
      gridEl.classList.add("solved");
      const ms = typeof data.runtime_ms === "number" ? data.runtime_ms.toFixed(1) : "?";
      const nodes = data.nodes_expanded != null ? `, ${data.nodes_expanded} nodes expanded` : "";
      coachMessage.textContent = `Solved by the CSP engine in ${ms} ms${nodes}. Try the next puzzle on your own!`;
      showToast(`Solved in ${ms} ms`, "success");
    } else {
      showToast(data.message || "The solver couldn't find a solution.", "error");
    }
  } catch (e) {
    showToast("Solver error.", "error");
  }
}

function normalizedCustomInput() {
  return (customPuzzleInput.value || "").replace(/\s+/g, "").replace(/[.\-_*]/g, "0");
}

function updateCustomCount() {
  const len = normalizedCustomInput().length;
  customCharCount.textContent = len;
  customCharCount.parentElement.classList.toggle("ok", len === 81);
}

async function handleCustomPuzzleSubmit() {
  const val = normalizedCustomInput();
  modalError.hidden = true;

  if (!/^\d+$/.test(val)) {
    modalError.hidden = false;
    modalError.textContent = "Only digits 0–9 and '.' are allowed.";
    return;
  }
  if (val.length !== 81) {
    modalError.hidden = false;
    modalError.textContent = `Must be exactly 81 characters (got ${val.length}).`;
    return;
  }

  try {
    await api("/api/load-puzzle", { puzzle: val, difficulty: "custom" });
    closeModal(customModal);
    customPuzzleInput.value = "";
    userProfile.currentPuzzleId = null;
    saveProfile();
    workspaceItemTitle.textContent = "Custom puzzle";
    const customOpt = document.createElement("option");
    customOpt.value = "";
    customOpt.textContent = "Custom puzzle";
    removeExtraPuzzleOptions();
    puzzleSelect.prepend(customOpt);
    puzzleSelect.value = "";
    startFreshBoard("Custom puzzle loaded. I'll coach you through it the same way.");
    await refreshBoardState();
    showToast("Custom puzzle loaded.", "success");
  } catch (e) {
    modalError.hidden = false;
    modalError.textContent = e.message || "Invalid puzzle string.";
  }
}

// =============================================================================
// Puzzle Generator (fresh puzzles graded to the learner's level)
// =============================================================================
function removeExtraPuzzleOptions() {
  puzzleSelect.querySelectorAll("option").forEach(opt => {
    if (opt.value === "" || opt.value.startsWith("gen_")) opt.remove();
  });
}

function showGeneratedOption(meta) {
  removeExtraPuzzleOptions();
  const opt = document.createElement("option");
  opt.value = meta.puzzle_id;
  const solved = userProfile.solvedPuzzles.includes(meta.puzzle_id);
  opt.textContent = `${solved ? "✓ " : ""}✦ ${meta.title} · ${meta.clue_count} clues`;
  puzzleSelect.prepend(opt);
  puzzleSelect.value = meta.puzzle_id;
}

function describeGeneratedPuzzle(meta) {
  if (meta.difficulty === "beginner") {
    return `Here's a fresh ${meta.clue_count}-clue puzzle. Everything can be solved with Full House and Singles — no guessing needed.`;
  }
  const label = meta.hardest_technique_label || meta.hardest_technique;
  if (meta.meets_level) {
    return `Here's a fresh ${meta.clue_count}-clue puzzle made for your level. At some point you'll need a ${label} — ask for a hint if you get stuck.`;
  }
  return `Here's a fresh ${meta.clue_count}-clue puzzle. I couldn't find one needing a true ${meta.difficulty}-only technique quickly, so this is the toughest close match (it needs a ${label}). Tap “New puzzle” again later — I keep a few ready in the background.`;
}

async function handleGeneratePuzzle() {
  const level = userProfile.level || "intermediate";
  btnGeneratePuzzle.classList.add("is-loading");
  btnGeneratePuzzle.textContent = "Generating…";
  coachMessage.textContent = level === "advanced"
    ? "Building a fresh advanced puzzle and checking it can be solved without guessing — this can take a few seconds…"
    : "Building a fresh puzzle for your level…";

  try {
    const data = await api("/api/teacher/generate-puzzle", { level, session_id: "default" });
    const meta = data.puzzle_meta;
    userProfile.generatedPuzzle = meta;
    userProfile.currentPuzzleId = meta.puzzle_id;
    saveProfile();

    showGeneratedOption(meta);
    workspaceItemTitle.textContent = meta.title;
    startFreshBoard(describeGeneratedPuzzle(meta));
    await refreshBoardState();
    showToast(meta.meets_level ? `New ${level} puzzle ready` : "New puzzle ready (closest match)", meta.meets_level ? "success" : "");
  } catch (e) {
    coachMessage.textContent = "I couldn't generate a puzzle just now. Try again, or pick one from the menu.";
    showToast(e.message || "Could not generate a puzzle.", "error");
  } finally {
    btnGeneratePuzzle.classList.remove("is-loading");
    btnGeneratePuzzle.textContent = "✦ New puzzle";
  }
}

async function loadGeneratedPuzzle(meta) {
  try {
    await api("/api/load-puzzle", { puzzle: meta.puzzle, difficulty: meta.difficulty, session_id: "default" });
    showGeneratedOption(meta);
    workspaceItemTitle.textContent = meta.title;
    startFreshBoard(describeGeneratedPuzzle(meta));
    await refreshBoardState();
  } catch (e) {
    showToast("Couldn't restore your generated puzzle.", "error");
  }
}
