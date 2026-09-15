const $ = (selector) => document.querySelector(selector);

const state = {
  history: [],
  historyIndex: 0,
  cwd: "~",
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
  div.textContent = text;
  return div.innerHTML;
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
    `:<span style="color:#7cb7ff">${escapeHtml(state.cwd)}</span>` +
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
  if (!selection || selection.isCollapsed) {
    $("#terminal-input").focus();
  }
});


$("#clear-terminal").addEventListener("click", () => {
  $("#terminal-output").innerHTML = "";
});


function renderFiles(files) {
  const host = $("#files");
  host.innerHTML = "";

  for (const [path, content] of Object.entries(files)) {
    const block = document.createElement("div");
    block.className = "file-block";

    const name = document.createElement("div");
    name.className = "filename";
    name.textContent = path;

    const pre = document.createElement("pre");
    pre.textContent = content;

    block.append(name, pre);
    host.appendChild(block);
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


function renderExercise(exercise) {
  $("#title").textContent = exercise.title;
  $("#prompt").textContent = exercise.prompt;
  $("#dataset-kind").textContent = exercise.dataset_kind;

  const style = $("#exercise-style");
  style.textContent = exercise.style;
  style.className = `style-badge style-${exercise.style}`;

  $("#tools").innerHTML = exercise.tools
    .map(tool => `<span>${escapeHtml(tool)}</span>`)
    .join("");

  renderOutputSpec(exercise.output);
  renderFiles(exercise.files);

  $("#result").innerHTML = "";
  $("#answer-input").value = "";
  $("#terminal-output").innerHTML = "";

  $("#solution").textContent = "";
  $("#solution-explanation").textContent = "";
  $("#solution-panel").classList.add("hidden");

  $("#solved-session").classList.add("hidden");
  $("#solved-terminal-history").innerHTML = "";
  $("#solved-submitted-answers").innerHTML = "";
  $("#solved-skills").innerHTML = "";

  state.cwd = "~";
  $("#cwd").textContent = "~";
}


$("#new-btn").addEventListener("click", async () => {
  const btn = $("#new-btn");
  btn.disabled = true;

  try {
    const data = await api("/api/exercise/new", {method: "POST"});
    renderExercise(data.exercise);
  } catch (error) {
    alert(error.message);
  } finally {
    btn.disabled = false;
  }
});


$("#reset-btn").addEventListener("click", async () => {
  const btn = $("#reset-btn");
  btn.disabled = true;

  try {
    const data = await api("/api/exercise/reset", {method: "POST"});
    state.cwd = data.cwd;
    $("#cwd").textContent = data.cwd;
    $("#terminal-output").innerHTML = "";
    terminalAppend("stdout", "Exercise files restored.");
  } catch (error) {
    terminalAppend("stderr", error.message);
  } finally {
    btn.disabled = false;
  }
});


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

    row.innerHTML =
      `<span class="${passed ? "pass" : "fail"}">${passed ? "✓" : "✗"}</span>` +
      `<code>$ ${escapeHtml(item.command)}</code>` +
      `<span class="exit-code">exit ${item.exit_code}</span>`;

    target.appendChild(row);
  }
}


function renderSkills(items) {
  const target = $("#solved-skills");
  target.innerHTML = "";

  for (const item of items || []) {
    const chip = document.createElement("div");
    chip.className = "concept-chip";
    chip.innerHTML =
      `<strong>${escapeHtml(item.tool)}</strong>` +
      `<span>${escapeHtml(item.name)}</span>` +
      `<small>${escapeHtml(item.role)}</small>`;
    target.appendChild(chip);
  }
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

    if (data.passed) {
      const review = data.history_id
        ? ` <a class="inline-link" href="/history/${data.history_id}">Open saved review →</a>`
        : "";

      result.innerHTML = `<div class="result-good">✓ Correct${review}</div>`;

      renderSkills(data.skills || []);
      renderCommandList("#solved-terminal-history", data.terminal_commands || [], false);
      renderCommandList("#solved-submitted-answers", data.submitted_answers || [], true);
      $("#solved-session").classList.remove("hidden");
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


checkStatus();
setInterval(checkStatus, 10000);
$("#terminal-input").focus();
