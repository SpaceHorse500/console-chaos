from __future__ import annotations

import json
import os
import pathlib
import socket
import subprocess
import threading


SOCKET_PATH = "/shared/sandbox.sock"
WORKSPACE_ROOT = pathlib.Path("/workspace").resolve()
ALLOWED_WORKSPACES = {"play", "grade"}
COMMAND_TIMEOUT = 8


def safe_cwd(workspace: str, cwd: str) -> pathlib.Path:
    if workspace not in ALLOWED_WORKSPACES:
        raise ValueError("Invalid workspace.")

    base = (WORKSPACE_ROOT / workspace).resolve()
    requested = (base / cwd).resolve()

    if requested != base and base not in requested.parents:
        raise ValueError("Working directory escapes the exercise workspace.")
    if not requested.exists():
        raise ValueError("Working directory does not exist.")
    if not requested.is_dir():
        raise ValueError("Working directory is not a directory.")

    return requested


def run_command(command: str, workspace: str, cwd: str) -> dict:
    if not isinstance(command, str) or not command.strip():
        return {
            "ok": True,
            "exit_code": 2,
            "stdout": "",
            "stderr": "No command provided.\n",
        }

    workdir = safe_cwd(workspace, cwd)

    try:
        proc = subprocess.run(
            ["bash", "--noprofile", "--norc", "-c", command],
            cwd=str(workdir),
            text=True,
            capture_output=True,
            timeout=COMMAND_TIMEOUT,
            env={
                "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                "HOME": "/home/student",
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                "TERM": "xterm-256color",
                "MANPAGER": "cat",
                "PAGER": "cat",
            },
        )
        return {
            "ok": True,
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        stderr += f"\nCommand exceeded {COMMAND_TIMEOUT}s timeout.\n"
        return {
            "ok": True,
            "exit_code": 124,
            "stdout": stdout,
            "stderr": stderr,
        }


def handle_connection(conn: socket.socket) -> None:
    try:
        raw = b""
        while b"\n" not in raw and len(raw) < 1_000_000:
            chunk = conn.recv(65536)
            if not chunk:
                break
            raw += chunk

        if not raw:
            response = {"ok": False, "error": "Empty request."}
        else:
            request_data = json.loads(raw.split(b"\n", 1)[0].decode("utf-8"))
            operation = request_data.get("op")

            if operation == "ping":
                response = {"ok": True, "pong": True}
            elif operation == "exec":
                response = run_command(
                    command=request_data.get("command", ""),
                    workspace=request_data.get("workspace", ""),
                    cwd=request_data.get("cwd", "."),
                )
            else:
                response = {"ok": False, "error": "Unknown sandbox operation."}
    except Exception as exc:
        response = {"ok": False, "error": str(exc)}

    try:
        conn.sendall((json.dumps(response) + "\n").encode("utf-8"))
    finally:
        conn.close()


def main() -> None:
    os.makedirs(os.path.dirname(SOCKET_PATH), exist_ok=True)

    try:
        os.unlink(SOCKET_PATH)
    except FileNotFoundError:
        pass

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    os.chmod(SOCKET_PATH, 0o666)
    server.listen(32)

    print(f"Console Chaos sandbox listening on {SOCKET_PATH}", flush=True)

    while True:
        conn, _ = server.accept()
        threading.Thread(
            target=handle_connection,
            args=(conn,),
            daemon=True,
        ).start()


if __name__ == "__main__":
    main()
