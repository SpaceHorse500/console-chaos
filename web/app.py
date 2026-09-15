from __future__ import annotations

import os
import pathlib
import shlex
import shutil
import uuid

from flask import Flask, abort, jsonify, render_template, request, session

from exercises.engine import ExerciseEngine
from exercises.models import Exercise
from history_store import add_record, get_record, list_records
from sandbox_client import SandboxClient, SandboxError


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "shellgym-local-dev")
app.config["JSON_SORT_KEYS"] = False

engine = ExerciseEngine()
sandbox = SandboxClient()

WORKSPACE_ROOT = pathlib.Path(os.getenv("WORKSPACE_ROOT", "/workspace"))
PLAY = WORKSPACE_ROOT / "play"
GRADE = WORKSPACE_ROOT / "grade"
STUDENT_UID = 1000
STUDENT_GID = 1000

# Local single-user trainer state. Nothing large is stored in the browser cookie.
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

    exercise = engine.generate()
    eid = uuid.uuid4().hex
    EXERCISES[eid] = exercise
    ACTIVE[eid] = {
        "terminal_cwd": ".",
        "terminal_commands": [],
        "submitted_answers": [],
        "history_id": None,
    }
    session["exercise_id"] = eid

    write_workspace(PLAY, exercise)
    write_workspace(GRADE, exercise)
    return exercise


def exercise_payload(exercise: Exercise) -> dict:
    return {
        "title": exercise.title,
        "prompt": exercise.prompt,
        "difficulty": exercise.difficulty,
        "tools": exercise.tools,
        "dataset_kind": exercise.dataset_kind,
        "files": exercise.files,
    }


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


def log_submission(command: str, exit_code: int, passed: bool) -> None:
    state = current_state()
    if state is None:
        return
    state["submitted_answers"].append({
        "command": command,
        "exit_code": int(exit_code),
        "passed": bool(passed),
    })
    state["submitted_answers"] = state["submitted_answers"][-100:]


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
    return render_template("history_detail.html", record=record)


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

    # The final answer always runs against pristine exercise files.
    write_workspace(GRADE, exercise)

    try:
        result = sandbox.exec(command, workspace="grade", cwd=".")
    except SandboxError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 503

    passed = (
        result.exit_code == 0
        and normalize(result.stdout) == normalize(exercise.expected)
    )

    log_submission(command, result.exit_code, passed)

    if passed and state["history_id"] is None:
        state["history_id"] = add_record({
            "title": exercise.title,
            "prompt": exercise.prompt,
            "difficulty": exercise.difficulty,
            "tools": exercise.tools,
            "dataset_kind": exercise.dataset_kind,
            "files": exercise.files,
            "terminal_commands": list(state["terminal_commands"]),
            "submitted_answers": list(state["submitted_answers"]),
            "accepted_answer": command,
            "reference_solution": exercise.solution,
            "explanation": exercise.explanation,
        })

    return jsonify({
        "ok": True,
        "passed": passed,
        "exit_code": result.exit_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "history_id": state["history_id"],
        "terminal_commands": list(state["terminal_commands"]) if passed else None,
        "submitted_answers": list(state["submitted_answers"]) if passed else None,
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
