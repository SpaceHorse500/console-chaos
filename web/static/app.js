const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const state = {
  history: [],
  historyIndex: 0,
  cwd: "~",
  resolutionMode: document.querySelector("#resolution-badge")?.classList.contains("restricted") ? "restricted" : "open",
  helpStages: new Set(),
  solved: false,
  dockCollapsed: false,
  dockHeight: null,
};

async function api(url, options = {}) {
  const response = await fetch(url, options);
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(`HTTP ${response.status}`);
  }
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || `HTTP ${response.status}`);
  }
  return data;
}

async function checkStatus() {
  const dot = $("#sandbox-dot");
  const label = $("#sandbox-status");
  try {
    const data = await api("/api/status");
    if (data.sandbox_ready) {
      dot.className = "dot ready";
      label.textContent = "Debian sandbox ready";
    } else {
      dot.className = "dot offline";
      label.textContent = "Sandbox unavailable";
    }
  } catch {
    dot.className = "dot offline";
    label.textContent = "Sandbox unavailable";
  }
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text ?? "";
  return div.innerHTML;
}


const LAYOUT_KEYS = {
  problemWidth: "consoleChaos.problemPaneWidth",
  answerHeight: "consoleChaos.answerDockHeight",
  answerCollapsed: "consoleChaos.answerDockCollapsed",
};

const DEFAULT_LAYOUT = {
  problemRatio: 0.40,
  answerHeight: 132,
};

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function desktopLayoutEnabled() {
  return window.matchMedia("(min-width: 901px)").matches;
}

function setProblemPaneWidth(width, persist = true) {
  if (!desktopLayoutEnabled()) return;
  const workspace = $(".practice-workspace");
  if (!workspace) return;
  const rect = workspace.getBoundingClientRect();
  const minLeft = 300;
  const minRight = 390;
  const maxLeft = Math.max(minLeft, rect.width - minRight - 8);
  const px = clamp(Number(width), minLeft, maxLeft);
  workspace.style.setProperty("--problem-pane-width", `${px}px`);
  if (persist) localStorage.setItem(LAYOUT_KEYS.problemWidth, String(Math.round(px)));
}

function setAnswerDockHeight(height, persist = true) {
  if (!desktopLayoutEnabled()) return;
  const dock = $("#answer-dock");
  if (!dock) return;
  const maxHeight = Math.min(440, Math.round(window.innerHeight * 0.48));
  const px = clamp(Number(height), 86, maxHeight);
  state.dockHeight = px;
  dock.style.setProperty("--answer-dock-height", `${px}px`);
  if (persist) localStorage.setItem(LAYOUT_KEYS.answerHeight, String(Math.round(px)));
}

function setDockCollapsed(collapsed, persist = true) {
  const dock = $("#answer-dock");
  const button = $("#dock-toggle-btn");
  if (!dock || !button) return;
  state.dockCollapsed = Boolean(collapsed);
  dock.classList.toggle("collapsed", state.dockCollapsed);
  button.textContent = state.dockCollapsed ? "Expand" : "Collapse";
  button.setAttribute("aria-expanded", String(!state.dockCollapsed));
  if (persist) localStorage.setItem(LAYOUT_KEYS.answerCollapsed, state.dockCollapsed ? "1" : "0");
}

function restoreLayout() {
  if (!desktopLayoutEnabled()) return;
  const workspace = $(".practice-workspace");
  const savedWidth = Number(localStorage.getItem(LAYOUT_KEYS.problemWidth));
  if (savedWidth > 0) {
    setProblemPaneWidth(savedWidth, false);
  } else if (workspace) {
    setProblemPaneWidth(workspace.getBoundingClientRect().width * DEFAULT_LAYOUT.problemRatio, false);
  }

  const savedHeight = Number(localStorage.getItem(LAYOUT_KEYS.answerHeight));
  setAnswerDockHeight(savedHeight > 0 ? savedHeight : DEFAULT_LAYOUT.answerHeight, false);
  setDockCollapsed(localStorage.getItem(LAYOUT_KEYS.answerCollapsed) === "1", false);
}

function resetLayout() {
  Object.values(LAYOUT_KEYS).forEach(key => localStorage.removeItem(key));
  const workspace = $(".practice-workspace");
  if (workspace && desktopLayoutEnabled()) {
    setProblemPaneWidth(workspace.getBoundingClientRect().width * DEFAULT_LAYOUT.problemRatio, false);
    setAnswerDockHeight(DEFAULT_LAYOUT.answerHeight, false);
  }
  setDockCollapsed(false, false);
}

function setupResizers() {
  const workspace = $(".practice-workspace");
  const vertical = $("#workspace-resizer");
  const horizontal = $("#answer-resizer");

  if (workspace && vertical) {
    vertical.addEventListener("pointerdown", event => {
      if (!desktopLayoutEnabled()) return;
      event.preventDefault();
      vertical.setPointerCapture(event.pointerId);
      document.body.classList.add("resizing-columns");

      const move = ev => {
        const rect = workspace.getBoundingClientRect();
        setProblemPaneWidth(ev.clientX - rect.left);
      };
      const stop = ev => {
        document.body.classList.remove("resizing-columns");
        try { vertical.releasePointerCapture(ev.pointerId); } catch {}
        vertical.removeEventListener("pointermove", move);
        vertical.removeEventListener("pointerup", stop);
        vertical.removeEventListener("pointercancel", stop);
      };
      vertical.addEventListener("pointermove", move);
      vertical.addEventListener("pointerup", stop);
      vertical.addEventListener("pointercancel", stop);
    });

    vertical.addEventListener("keydown", event => {
      if (!desktopLayoutEnabled() || !["ArrowLeft", "ArrowRight"].includes(event.key)) return;
      event.preventDefault();
      const left = $(".problem-pane").getBoundingClientRect().width;
      setProblemPaneWidth(left + (event.key === "ArrowRight" ? 24 : -24));
    });
  }

  if (horizontal) {
    horizontal.addEventListener("pointerdown", event => {
      if (!desktopLayoutEnabled()) return;
      event.preventDefault();
      if (state.dockCollapsed) setDockCollapsed(false);
      horizontal.setPointerCapture(event.pointerId);
      document.body.classList.add("resizing-rows");

      const move = ev => setAnswerDockHeight(window.innerHeight - ev.clientY);
      const stop = ev => {
        document.body.classList.remove("resizing-rows");
        try { horizontal.releasePointerCapture(ev.pointerId); } catch {}
        horizontal.removeEventListener("pointermove", move);
        horizontal.removeEventListener("pointerup", stop);
        horizontal.removeEventListener("pointercancel", stop);
      };
      horizontal.addEventListener("pointermove", move);
      horizontal.addEventListener("pointerup", stop);
      horizontal.addEventListener("pointercancel", stop);
    });

    horizontal.addEventListener("keydown", event => {
      if (!desktopLayoutEnabled() || !["ArrowUp", "ArrowDown"].includes(event.key)) return;
      event.preventDefault();
      if (state.dockCollapsed) setDockCollapsed(false);
      const current = state.dockHeight || DEFAULT_LAYOUT.answerHeight;
      setAnswerDockHeight(current + (event.key === "ArrowUp" ? 24 : -24));
    });
  }
}

function switchTab(name) {
  const button = document.querySelector(`.pane-tab[data-tab-target="${name}"]`);
  const panel = document.querySelector(`.pane-panel[data-tab-panel="${name}"]`);
  if (!button || !panel || button.classList.contains("hidden")) return;

  $$(".pane-tab").forEach(item => item.classList.remove("active"));
  $$(".pane-panel").forEach(item => item.classList.remove("active"));
  button.classList.add("active");
  panel.classList.add("active");
  $(".problem-pane-body")?.scrollTo({top: 0, behavior: "smooth"});
}

$$(".pane-tab").forEach(button => {
  button.addEventListener("click", () => switchTab(button.dataset.tabTarget));
});

function setReviewAvailable(available) {
  const button = $("#review-tab-button");
  state.solved = available;
  button.classList.toggle("hidden", !available);
  $("#next-btn").classList.toggle("hidden", !available);

  if (!available && button.classList.contains("active")) {
    switchTab("problem");
  }
}

function terminalAppend(kind, text) {
  if (!text) return;
  const line = document.createElement("div");
  line.className = `terminal-line ${kind}`;
  line.textContent = text.replace(/\n$/, "");
  $("#terminal-output").appendChild(line);
  $("#terminal").scrollTop = $("#terminal").scrollHeight;
}

function terminalPromptLine(command) {
  const line = document.createElement("div");
  line.className = "terminal-line command";
  line.innerHTML =
    `<span class="prompt-user">student@console-chaos</span>` +
    `:<span class="terminal-cwd-inline">${escapeHtml(state.cwd)}</span>` +
    `$ ${escapeHtml(command)}`;
  $("#terminal-output").appendChild(line);
}

async function runTerminal(command) {
  terminalPromptLine(command);
  if (command === "clear") {
    $("#terminal-output").innerHTML = "";
    return;
  }
  try {
    const data = await api("/api/terminal", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({command}),
    });
    state.cwd = data.cwd;
    $("#cwd").textContent = data.cwd;
    terminalAppend("stdout", data.stdout);
    terminalAppend("stderr", data.stderr);
  } catch (error) {
    terminalAppend("stderr", error.message);
  }
}

$("#terminal-input").addEventListener("keydown", async (event) => {
  const input = event.currentTarget;
  if (event.key === "Enter") {
    const command = input.value.trim();
    input.value = "";
    if (!command) return;
    state.history.push(command);
    state.historyIndex = state.history.length;
    input.disabled = true;
    await runTerminal(command);
    input.disabled = false;
    input.focus();
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    if (!state.history.length) return;
    state.historyIndex = Math.max(0, state.historyIndex - 1);
    input.value = state.history[state.historyIndex] || "";
    setTimeout(() => input.setSelectionRange(input.value.length, input.value.length));
  } else if (event.key === "ArrowDown") {
    event.preventDefault();
    if (!state.history.length) return;
    state.historyIndex = Math.min(state.history.length, state.historyIndex + 1);
    input.value = state.history[state.historyIndex] || "";
  }
});

$("#terminal").addEventListener("click", () => {
  const selection = window.getSelection();
  if (!selection || selection.isCollapsed) $("#terminal-input").focus();
});

$("#clear-terminal").addEventListener("click", () => {
  $("#terminal-output").innerHTML = "";
  $("#terminal-input").focus();
});

$("#dock-toggle-btn").addEventListener("click", () => {
  setDockCollapsed(!state.dockCollapsed);
});

$("#reset-layout-btn").addEventListener("click", () => {
  resetLayout();
});

function renderFiles(files) {
  const host = $("#files");
  host.innerHTML = "";
  let first = true;
  for (const [path, content] of Object.entries(files)) {
    const detail = document.createElement("details");
    detail.className = "file-block file-detail";
    detail.open = first;
    first = false;

    const summary = document.createElement("summary");
    summary.className = "filename";
    summary.textContent = path;

    const pre = document.createElement("pre");
    pre.textContent = content;

    detail.append(summary, pre);
    host.appendChild(detail);
  }
}

function renderOutputSpec(spec) {
  $("#output-label").textContent = spec.label;
  $("#output-example").textContent = spec.example;
  const rules = $("#output-rules");
  rules.innerHTML = "";
  for (const rule of spec.rules || []) {
    const li = document.createElement("li");
    li.textContent = rule;
    rules.appendChild(li);
  }
}

function renderResolution(exercise) {
  state.resolutionMode = exercise.resolution_mode;
  const restricted = exercise.resolution_mode === "restricted";
  const badge = $("#resolution-badge");
  badge.textContent = restricted ? "restricted" : "open";
  badge.className = `resolution-badge ${restricted ? "restricted" : "open"}`;
  $("#tools-heading").textContent = restricted ? "Allowed tools" : "Suggested tools";
  $("#resolution-note").textContent = restricted
    ? "Focused exercise: the final answer may only use the listed tools. Shell syntax such as pipes/redirection is still allowed when relevant."
    : "Open solution: these are suggestions. Any command producing the required stdout is valid.";
  $("#answer-mode-copy").textContent = restricted
    ? "Focused: stdout + target concept/tool restriction."
    : "Open: graded by stdout against a fresh copy of the files.";
}

function resetHelpPanel() {
  state.helpStages = new Set();
  $("#concept-help-panel").classList.add("hidden");
  $("#concept-help-content").innerHTML = "";
  $("#help-syntax-btn").classList.add("hidden");
  $("#help-hint-btn").classList.add("hidden");
  $("#concept-help-stage-title").textContent = "Concept";
}

function renderExercise(exercise) {
  $("#title").textContent = exercise.title;
  $("#prompt").textContent = exercise.prompt;
  $("#dataset-kind").textContent = exercise.dataset_kind;

  const style = $("#exercise-style");
  style.textContent = exercise.style;
  style.className = `style-badge style-${exercise.style}`;

  $("#tools").innerHTML = exercise.tools.map(tool => `<span>${escapeHtml(tool)}</span>`).join("");
  renderResolution(exercise);
  renderOutputSpec(exercise.output);
  renderFiles(exercise.files);

  $("#result").innerHTML = "";
  $("#answer-input").value = "";
  $("#terminal-output").innerHTML = "";
  $("#solution").textContent = "";
  $("#solution-explanation").textContent = "";
  $("#solution-panel").classList.add("hidden");
  $("#solved-terminal-history").innerHTML = "";
  $("#solved-submitted-answers").innerHTML = "";
  $("#solved-skills").innerHTML = "";
  $("#exercise-focus-skills").innerHTML = "";
  $("#help-used").innerHTML = "";
  $("#help-used-wrap").classList.add("hidden");

  resetHelpPanel();
  setReviewAvailable(false);
  switchTab("problem");

  state.cwd = "~";
  $("#cwd").textContent = "~";
  $("#terminal-input").focus();
}

async function loadNewExercise(triggerButton = null) {
  if (triggerButton) triggerButton.disabled = true;
  try {
    const data = await api("/api/exercise/new", {method: "POST"});
    renderExercise(data.exercise);
  } catch (error) {
    alert(error.message);
  } finally {
    if (triggerButton) triggerButton.disabled = false;
  }
}

$("#new-btn").addEventListener("click", event => loadNewExercise(event.currentTarget));
$("#next-btn").addEventListener("click", event => loadNewExercise(event.currentTarget));

$("#reset-btn").addEventListener("click", async () => {
  const btn = $("#reset-btn");
  btn.disabled = true;
  try {
    const data = await api("/api/exercise/reset", {method: "POST"});
    state.cwd = data.cwd;
    $("#cwd").textContent = data.cwd;
    $("#terminal-output").innerHTML = "";
    terminalAppend("stdout", "Exercise files restored.");
    $("#terminal-input").focus();
  } catch (error) {
    terminalAppend("stderr", error.message);
  } finally {
    btn.disabled = false;
  }
});

function renderHelpItems(stage, items) {
  const existing = document.querySelector(`[data-help-stage="${stage}"]`);
  if (existing) existing.remove();

  const section = document.createElement("section");
  section.className = "help-stage";
  section.dataset.helpStage = stage;
  const titles = {concept: "Concept", syntax: "Syntax & generic example", hint: "Stronger hint"};
  section.innerHTML = `<h4>${titles[stage]}</h4>`;

  for (const item of items || []) {
    const card = document.createElement("div");
    card.className = "help-concept-card";
    let body = `<div class="help-concept-name"><code>${escapeHtml(item.tool)}</code> ${escapeHtml(item.name)}</div>`;
    if (stage === "syntax") {
      body += `<pre>${escapeHtml(item.content)}</pre>`;
      if (item.example) body += `<div class="format-example-label">Generic example</div><pre>${escapeHtml(item.example)}</pre>`;
    } else {
      body += `<p>${escapeHtml(item.content)}</p>`;
    }
    card.innerHTML = body;
    section.appendChild(card);
  }

  $("#concept-help-content").appendChild(section);
  state.helpStages.add(stage);
  $("#concept-help-panel").classList.remove("hidden");
  $("#concept-help-stage-title").textContent = titles[stage];

  if (stage === "concept") $("#help-syntax-btn").classList.remove("hidden");
  if (stage === "syntax") $("#help-hint-btn").classList.remove("hidden");
}

async function loadHelp(stage) {
  try {
    const data = await api("/api/concept-help", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({stage}),
    });
    renderHelpItems(stage, data.items);
  } catch (error) {
    alert(error.message);
  }
}

$("#concept-help-btn").addEventListener("click", () => loadHelp("concept"));
$("#help-syntax-btn").addEventListener("click", () => loadHelp("syntax"));
$("#help-hint-btn").addEventListener("click", () => loadHelp("hint"));

function renderCommandList(targetSelector, items, answerMode = false) {
  const target = $(targetSelector);
  target.innerHTML = "";
  if (!items || !items.length) {
    target.innerHTML = `<div class="empty-small">No commands recorded.</div>`;
    return;
  }
  for (const item of items) {
    const row = document.createElement("div");
    row.className = "command-history-row";
    const passed = answerMode ? Boolean(item.passed) : Number(item.exit_code) === 0;
    const outputWorked = answerMode && Boolean(item.output_matches);
    const restricted = answerMode && Boolean(item.restriction_failed);
    const statusClass = passed ? "pass" : (outputWorked ? "partial" : "fail");
    const statusMark = passed ? "✓" : (outputWorked ? "◇" : "✗");
    let note = `exit ${item.exit_code}`;
    if (restricted && outputWorked) note += " · output correct, restricted";
    else if (restricted) note += " · restricted";
    else if (answerMode && item.reason === "focus_not_demonstrated" && outputWorked) note += " · output correct, focus missing";
    row.innerHTML =
      `<span class="${statusClass}">${statusMark}</span>` +
      `<code>$ ${escapeHtml(item.command)}</code>` +
      `<span class="exit-code">${escapeHtml(note)}</span>`;
    target.appendChild(row);
  }
}

function renderSkills(targetSelector, items) {
  const target = $(targetSelector);
  target.innerHTML = "";
  if (!items || !items.length) {
    target.innerHTML = `<div class="empty-small">No confidently detected concepts.</div>`;
    return;
  }
  for (const item of items) {
    const chip = document.createElement("div");
    chip.className = "concept-chip";
    chip.innerHTML =
      `<strong>${escapeHtml(item.tool)}</strong>` +
      `<span>${escapeHtml(item.name)}</span>` +
      `<small>${escapeHtml(item.role)}</small>`;
    target.appendChild(chip);
  }
}

function renderHelpUsed(stages) {
  const wrap = $("#help-used-wrap");
  const target = $("#help-used");
  target.innerHTML = "";
  if (!stages || !stages.length) {
    wrap.classList.add("hidden");
    return;
  }
  const names = {concept: "Concept", syntax: "Syntax", hint: "Stronger hint"};
  for (const stage of stages) {
    const span = document.createElement("span");
    span.textContent = `✓ ${names[stage] || stage}`;
    target.appendChild(span);
  }
  wrap.classList.remove("hidden");
}

async function submitAnswer() {
  const command = $("#answer-input").value.trim();
  if (!command) return;

  const btn = $("#submit-answer");
  const result = $("#result");
  btn.disabled = true;
  result.innerHTML = "";

  try {
    const data = await api("/api/answer", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({command}),
    });

    if (data.restriction_failed) {
      const worked = Boolean(data.output_matches);
      const headline = worked
        ? "✓ Your result is correct — but this method is restricted here."
        : "✗ This method is restricted here, and its output did not match.";
      const outputNote = worked
        ? "Console Chaos still ran the command against the fresh grading files, and its stdout matched the required output."
        : "Console Chaos still ran the command against the fresh grading files so you can tell whether the approach itself worked.";
      const runtime = [];
      if (!worked) {
        runtime.push(`exit: ${data.exit_code}`);
        if (data.stdout) runtime.push(`stdout:\n${data.stdout}`);
        if (data.stderr) runtime.push(`stderr:\n${data.stderr}`);
      }
      result.innerHTML =
        `<div class="result-focus">${headline}</div>` +
        `<div class="result-detail">${escapeHtml(outputNote)}\n\n` +
        `Allowed: ${escapeHtml((data.allowed_tools || []).join(", "))}\n` +
        `Detected: ${escapeHtml((data.detected_tools || []).join(", ") || "none")}\n` +
        `Not allowed here: ${escapeHtml((data.forbidden_tools || []).join(", "))}` +
        `${runtime.length ? `\n\n${escapeHtml(runtime.join("\n\n"))}` : ""}\n\n` +
        `Use the required tool/concept to complete this Focused exercise.</div>`;
      return;
    }

    if (data.focus_failed) {
      const missing = (data.missing_focus || []).map(item => `${item.tool}: ${item.name}`).join("\n");
      result.innerHTML =
        `<div class="result-focus">✓ Output is correct, but the focus concept was not demonstrated.</div>` +
        `<div class="result-detail">This Focused exercise is specifically practicing:\n${escapeHtml(missing)}\n\n` +
        `Try another solution using that concept. Your current approach would be acceptable in an open Integration/Challenge exercise.</div>`;
      return;
    }

    if (data.passed) {
      const review = data.history_id
        ? ` <a class="inline-link" href="/history/${data.history_id}">Saved review →</a>`
        : "";
      result.innerHTML = `<div class="result-good">✓ Correct${review}</div>`;

      renderSkills("#exercise-focus-skills", data.exercise_focus || []);
      renderSkills("#solved-skills", data.skills || []);
      renderHelpUsed(data.hints_used || []);
      renderCommandList("#solved-terminal-history", data.terminal_commands || [], false);
      renderCommandList("#solved-submitted-answers", data.submitted_answers || [], true);
      setReviewAvailable(true);
    } else {
      const parts = [`exit: ${data.exit_code}`];
      if (data.stdout) parts.push(`stdout:\n${data.stdout}`);
      if (data.stderr) parts.push(`stderr:\n${data.stderr}`);
      if (!data.stdout && !data.stderr) parts.push("(no output)");
      result.innerHTML =
        `<div class="result-bad">✗ Try again</div>` +
        `<div class="result-detail">${escapeHtml(parts.join("\n\n"))}</div>`;
    }
  } catch (error) {
    result.innerHTML = `<div class="result-bad">${escapeHtml(error.message)}</div>`;
  } finally {
    btn.disabled = false;
  }
}

$("#submit-answer").addEventListener("click", submitAnswer);
$("#answer-input").addEventListener("keydown", event => {
  if (event.key === "Enter") submitAnswer();
});

$("#solution-btn").addEventListener("click", async () => {
  try {
    const data = await api("/api/solution");
    $("#solution").textContent = data.solution;
    $("#solution-explanation").textContent = data.explanation;
    $("#solution-panel").classList.remove("hidden");
  } catch (error) {
    alert(error.message);
  }
});

setupResizers();
restoreLayout();
window.addEventListener("resize", () => {
  if (desktopLayoutEnabled()) restoreLayout();
});

checkStatus();
setInterval(checkStatus, 10000);
switchTab("problem");
$("#terminal-input").focus();
