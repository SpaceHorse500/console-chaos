from __future__ import annotations

import os
import pathlib
import shlex
import shutil
import uuid

from flask import Flask, abort, jsonify, render_template, request, session

from exercises.command_analysis import detect_command_skills, validate_allowed_tools
from exercises.concept_help import get_help
from exercises.engine import ExerciseEngine
from exercises.models import Exercise
from exercises.skills import SKILLS, record_skill_uses, skill_tree
from history_store import add_record, get_record, list_records
from sandbox_client import SandboxClient, SandboxError


APP_NAME = "Console Chaos"

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "console-chaos-local-dev")
app.config["JSON_SORT_KEYS"] = False

engine = ExerciseEngine()
sandbox = SandboxClient()

WORKSPACE_ROOT = pathlib.Path(os.getenv("WORKSPACE_ROOT", "/workspace"))
PLAY = WORKSPACE_ROOT / "play"
GRADE = WORKSPACE_ROOT / "grade"
STUDENT_UID = 1000
STUDENT_GID = 1000

# Local single-user trainer state. Persistent solved history lives in history.json.
EXERCISES: dict[str, Exercise] = {}
ACTIVE: dict[str, dict] = {}


def normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def safe_rel(path: str) -> pathlib.PurePosixPath:
    rel = pathlib.PurePosixPath(path)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise ValueError(f"Unsafe exercise path: {path}")
    return rel


def write_workspace(base: pathlib.Path, exercise: Exercise) -> None:
    if base.exists():
        shutil.rmtree(base)

    base.mkdir(parents=True, exist_ok=True)
    os.chown(base, STUDENT_UID, STUDENT_GID)

    for raw_path, content in exercise.files.items():
        rel = safe_rel(raw_path)
        target = base.joinpath(*rel.parts)
        target.parent.mkdir(parents=True, exist_ok=True)

        current = target.parent
        while current != base.parent:
            try:
                os.chown(current, STUDENT_UID, STUDENT_GID)
                os.chmod(current, 0o755)
            except PermissionError:
                pass
            if current == base:
                break
            current = current.parent

        target.write_text(content, encoding="utf-8")
        os.chown(target, STUDENT_UID, STUDENT_GID)
        os.chmod(target, 0o644)


def exercise_id() -> str | None:
    return session.get("exercise_id")


def current_exercise() -> Exercise | None:
    eid = exercise_id()
    return EXERCISES.get(eid) if eid else None


def current_state() -> dict | None:
    eid = exercise_id()
    return ACTIVE.get(eid) if eid else None


def create_exercise() -> Exercise:
    old_id = exercise_id()
    if old_id:
        EXERCISES.pop(old_id, None)
        ACTIVE.pop(old_id, None)

    # The selector learns from solved JSON history, but the concrete data remains random.
    exercise = engine.generate(list_records())
    eid = uuid.uuid4().hex
    EXERCISES[eid] = exercise
    ACTIVE[eid] = {
        "terminal_cwd": ".",
        "terminal_commands": [],
        "submitted_answers": [],
        "hints_used": [],
        "history_id": None,
    }
    session["exercise_id"] = eid

    write_workspace(PLAY, exercise)
    write_workspace(GRADE, exercise)
    return exercise


def human_output_label(label: str) -> str:
    acronyms = {"IP", "HTTP", "CPU", "PID", "JSON", "CSV", "URL", "ID"}
    if label.strip().upper() == "NUMBER":
        return "One number"
    words = label.strip().split()
    rendered = []
    for index, word in enumerate(words):
        upper = word.upper()
        if upper in acronyms:
            rendered.append(upper)
        elif index == 0:
            rendered.append(word.capitalize())
        else:
            rendered.append(word.lower())
    return " ".join(rendered)


def resolution_mode(exercise: Exercise) -> str:
    return "restricted" if exercise.style == "focused" else "open"


def output_payload(exercise: Exercise) -> dict:
    return {
        "label": human_output_label(exercise.output.label),
        "raw_label": exercise.output.label,
        "example": exercise.output.example,
        "rules": exercise.output.rules,
    }


def exercise_payload(exercise: Exercise) -> dict:
    # Exact target concepts stay hidden until the learner opens Concept help.
    mode = resolution_mode(exercise)
    return {
        "title": exercise.title,
        "prompt": exercise.prompt,
        "style": exercise.style,
        "tools": exercise.tools,
        "resolution_mode": mode,
        "allowed_tools": exercise.tools if mode == "restricted" else [],
        "output": output_payload(exercise),
        "dataset_kind": exercise.dataset_kind,
        "files": exercise.files,
    }


def _skill_detail(skill_id: str, role: str) -> dict:
    definition = SKILLS[skill_id]
    return {
        "skill_id": skill_id,
        "tool": definition.tool,
        "name": definition.name,
        "level": definition.level,
        "role": role,
    }


def exercise_skill_details(exercise: Exercise) -> list[dict]:
    return [_skill_detail(use.skill_id, use.role) for use in exercise.skills]


def target_skill_ids(exercise: Exercise) -> list[str]:
    targets = [use.skill_id for use in exercise.skills if use.role == "target"]
    return targets or [use.skill_id for use in exercise.skills]


def demonstrated_skill_details(exercise: Exercise, command: str) -> list[dict]:
    declared = {use.skill_id: use.role for use in exercise.skills}
    detected = sorted(
        skill_id for skill_id in detect_command_skills(command)
        if skill_id in SKILLS
    )
    return [
        _skill_detail(skill_id, declared.get(skill_id, "demonstrated"))
        for skill_id in detected
    ]


def record_focus_skill_details(record: dict) -> list[dict]:
    details = []
    for item in record.get("skills", []) or []:
        if not isinstance(item, dict):
            continue
        skill_id = item.get("skill_id") or item.get("id")
        if skill_id in SKILLS:
            details.append(_skill_detail(skill_id, item.get("role", "reinforcement")))
    return details


def record_skill_details(record: dict) -> list[dict]:
    return [
        _skill_detail(use["skill_id"], use.get("role", "demonstrated"))
        for use in record_skill_uses(record)
    ]


def display_cwd(cwd: str) -> str:
    return "~" if cwd == "." else "~/" + cwd


def resolve_cd(current: str, arg: str | None) -> tuple[bool, str, str | None]:
    base = PLAY.resolve()
    current_abs = (base / current).resolve()
    target_text = arg or "."

    if target_text == "~":
        target = base
    elif target_text.startswith("~/"):
        target = (base / target_text[2:]).resolve()
    else:
        target = (current_abs / target_text).resolve()

    if target != base and base not in target.parents:
        return False, current, "cd: outside the exercise workspace is not allowed"
    if not target.exists():
        return False, current, f"cd: {target_text}: No such file or directory"
    if not target.is_dir():
        return False, current, f"cd: {target_text}: Not a directory"

    rel = target.relative_to(base)
    return True, "." if str(rel) == "." else rel.as_posix(), None


def log_terminal(command: str, exit_code: int) -> None:
    state = current_state()
    if state is None:
        return
    state["terminal_commands"].append({
        "command": command,
        "exit_code": int(exit_code),
    })
    state["terminal_commands"] = state["terminal_commands"][-300:]


def log_submission(
    command: str,
    exit_code: int,
    passed: bool,
    reason: str | None = None,
    output_matches: bool | None = None,
    restriction_failed: bool = False,
) -> None:
    state = current_state()
    if state is None:
        return
    item = {
        "command": command,
        "exit_code": int(exit_code),
        "passed": bool(passed),
    }
    if reason:
        item["reason"] = reason
    if output_matches is not None:
        item["output_matches"] = bool(output_matches)
    if restriction_failed:
        item["restriction_failed"] = True
    state["submitted_answers"].append(item)
    state["submitted_answers"] = state["submitted_answers"][-100:]


@app.context_processor
def inject_globals():
    return {"app_name": APP_NAME, "human_output_label": human_output_label}


@app.get("/")
def index():
    exercise = current_exercise() or create_exercise()
    return render_template("index.html", exercise=exercise)


@app.get("/history")
def history():
    return render_template("history.html", records=list_records())


@app.get("/history/<int:record_id>")
def history_detail(record_id: int):
    record = get_record(record_id)
    if record is None:
        abort(404)
    return render_template(
        "history_detail.html",
        record=record,
        focus_skill_details=record_focus_skill_details(record),
        skill_details=record_skill_details(record),
    )


@app.get("/skills")
def skills():
    records = list_records()
    tree = skill_tree(records)
    for group in tree["tools"]:
        for node in group["nodes"]:
            help_item = get_help(node["skill_id"], node["name"], node["tool"])
            node["help"] = {
                "concept": help_item.concept,
                "syntax": help_item.syntax,
                "example": help_item.example,
                "hint": help_item.hint,
            }
    return render_template("skills.html", tree=tree)


@app.get("/api/status")
def status():
    return jsonify({"ok": True, "sandbox_ready": sandbox.ping()})


@app.post("/api/exercise/new")
def new_exercise():
    exercise = create_exercise()
    return jsonify({
        "ok": True,
        "exercise": exercise_payload(exercise),
        "cwd": "~",
    })


@app.post("/api/exercise/reset")
def reset_exercise():
    exercise = current_exercise()
    state = current_state()
    if exercise is None or state is None:
        return jsonify({"ok": False, "error": "No active exercise."}), 400

    write_workspace(PLAY, exercise)
    state["terminal_cwd"] = "."
    return jsonify({"ok": True, "cwd": "~"})


@app.post("/api/terminal")
def terminal():
    exercise = current_exercise()
    state = current_state()
    if exercise is None or state is None:
        return jsonify({"ok": False, "error": "No active exercise."}), 400

    data = request.get_json(silent=True) or {}
    command = str(data.get("command", "")).strip()
    cwd = state["terminal_cwd"]

    if not command:
        return jsonify({
            "ok": True,
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "cwd": display_cwd(cwd),
        })

    try:
        parts = shlex.split(command)
    except ValueError as exc:
        log_terminal(command, 2)
        return jsonify({
            "ok": True,
            "exit_code": 2,
            "stdout": "",
            "stderr": str(exc) + "\n",
            "cwd": display_cwd(cwd),
        })

    if parts and parts[0] == "cd" and len(parts) <= 2:
        ok, new_cwd, error = resolve_cd(
            cwd,
            parts[1] if len(parts) == 2 else None,
        )
        exit_code = 0 if ok else 1
        log_terminal(command, exit_code)

        if ok:
            state["terminal_cwd"] = new_cwd
            return jsonify({
                "ok": True,
                "exit_code": 0,
                "stdout": "",
                "stderr": "",
                "cwd": display_cwd(new_cwd),
            })

        return jsonify({
            "ok": True,
            "exit_code": 1,
            "stdout": "",
            "stderr": error + "\n",
            "cwd": display_cwd(cwd),
        })

    try:
        result = sandbox.exec(command, workspace="play", cwd=cwd)
    except SandboxError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 503

    log_terminal(command, result.exit_code)

    return jsonify({
        "ok": True,
        "exit_code": result.exit_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "cwd": display_cwd(cwd),
    })


@app.post("/api/concept-help")
def concept_help():
    exercise = current_exercise()
    state = current_state()
    if exercise is None or state is None:
        return jsonify({"ok": False, "error": "No active exercise."}), 400

    data = request.get_json(silent=True) or {}
    stage = str(data.get("stage", "concept")).strip().lower()
    if stage not in {"concept", "syntax", "hint"}:
        return jsonify({"ok": False, "error": "Unknown help stage."}), 400

    if stage not in state["hints_used"]:
        state["hints_used"].append(stage)

    items = []
    for skill_id in target_skill_ids(exercise):
        definition = SKILLS[skill_id]
        help_item = get_help(skill_id, definition.name, definition.tool)
        item = {
            "skill_id": skill_id,
            "tool": definition.tool,
            "name": definition.name,
        }
        if stage == "concept":
            item["content"] = help_item.concept
        elif stage == "syntax":
            item["content"] = help_item.syntax
            item["example"] = help_item.example
        else:
            item["content"] = help_item.hint
        items.append(item)

    return jsonify({
        "ok": True,
        "stage": stage,
        "items": items,
        "hints_used": list(state["hints_used"]),
    })


@app.post("/api/answer")
def answer():
    exercise = current_exercise()
    state = current_state()
    if exercise is None or state is None:
        return jsonify({"ok": False, "error": "No active exercise."}), 400

    data = request.get_json(silent=True) or {}
    command = str(data.get("command", "")).strip()
    if not command:
        return jsonify({"ok": False, "error": "Enter an answer command."}), 400

    mode = resolution_mode(exercise)
    tool_check = validate_allowed_tools(command, exercise.tools)
    restriction_failed = mode == "restricted" and not tool_check["ok"]

    # Always execute the submitted command against pristine files, even when a
    # Focused exercise forbids one of its tools. This lets the learner see the
    # important distinction between "the output worked" and "the technique is
    # allowed for this exercise".
    write_workspace(GRADE, exercise)

    try:
        result = sandbox.exec(command, workspace="grade", cwd=".")
    except SandboxError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 503

    output_matches = (
        result.exit_code == 0
        and normalize(result.stdout) == normalize(exercise.expected)
    )

    demonstrated = demonstrated_skill_details(exercise, command)
    demonstrated_ids = {item["skill_id"] for item in demonstrated}
    targets = target_skill_ids(exercise)
    missing_targets = [skill_id for skill_id in targets if skill_id not in demonstrated_ids]

    # Focused exercises require both the allowed tool set and the target
    # concept. Integration/challenge exercises remain open-ended.
    focus_met = mode != "restricted" or not missing_targets
    passed = output_matches and focus_met and not restriction_failed

    reason = None
    if restriction_failed:
        reason = "restricted_tools"
    elif output_matches and not focus_met:
        reason = "focus_not_demonstrated"
    elif not output_matches:
        reason = "output_mismatch"

    log_submission(
        command,
        result.exit_code,
        passed,
        reason,
        output_matches=output_matches,
        restriction_failed=restriction_failed,
    )

    if passed and state["history_id"] is None:
        declared_roles = {use.skill_id: use.role for use in exercise.skills}
        state["history_id"] = add_record({
            "template_id": exercise.template_id,
            "title": exercise.title,
            "prompt": exercise.prompt,
            "style": exercise.style,
            "resolution_mode": mode,
            "tools": exercise.tools,
            "skills": [
                {"skill_id": use.skill_id, "role": use.role}
                for use in exercise.skills
            ],
            "demonstrated_skills": [
                {
                    "skill_id": item["skill_id"],
                    "role": declared_roles.get(item["skill_id"], "demonstrated"),
                }
                for item in demonstrated
            ],
            "hints_used": list(state["hints_used"]),
            "output": output_payload(exercise),
            "dataset_kind": exercise.dataset_kind,
            "files": exercise.files,
            "terminal_commands": list(state["terminal_commands"]),
            "submitted_answers": list(state["submitted_answers"]),
            "accepted_answer": command,
            "reference_solution": exercise.solution,
            "explanation": exercise.explanation,
        })

    missing_details = [
        _skill_detail(skill_id, "target")
        for skill_id in missing_targets
    ]

    return jsonify({
        "ok": True,
        "passed": passed,
        "output_matches": output_matches,
        "restriction_failed": restriction_failed,
        "focus_failed": bool(output_matches and not focus_met and not restriction_failed),
        "resolution_mode": mode,
        "allowed_tools": tool_check["allowed_tools"],
        "detected_tools": tool_check["detected_tools"],
        "forbidden_tools": tool_check["forbidden_tools"],
        "exit_code": result.exit_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "history_id": state["history_id"],
        "terminal_commands": list(state["terminal_commands"]) if passed else None,
        "submitted_answers": list(state["submitted_answers"]) if passed else None,
        "exercise_focus": exercise_skill_details(exercise) if passed else None,
        "skills": demonstrated,
        "missing_focus": missing_details if output_matches and not focus_met else [],
        "hints_used": list(state["hints_used"]),
    })


@app.get("/api/solution")
def solution():
    exercise = current_exercise()
    if exercise is None:
        return jsonify({"ok": False, "error": "No active exercise."}), 400

    return jsonify({
        "ok": True,
        "solution": exercise.solution,
        "explanation": exercise.explanation,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
