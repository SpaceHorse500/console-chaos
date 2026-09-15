from __future__ import annotations

import json
import os
import socket
from dataclasses import dataclass


class SandboxError(RuntimeError):
    pass


@dataclass
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str


class SandboxClient:
    def __init__(self, socket_path: str | None = None, timeout: float = 7.0):
        self.socket_path = socket_path or os.getenv("SANDBOX_SOCKET", "/shared/sandbox.sock")
        self.timeout = timeout

    def _request(self, payload: dict) -> dict:
        data = (json.dumps(payload) + "\n").encode("utf-8")
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                sock.connect(self.socket_path)
                sock.sendall(data)

                chunks = []
                while True:
                    chunk = sock.recv(65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    if b"\n" in chunk:
                        break
        except (OSError, TimeoutError) as exc:
            raise SandboxError(f"Sandbox unavailable: {exc}") from exc

        raw = b"".join(chunks).split(b"\n", 1)[0]
        if not raw:
            raise SandboxError("Sandbox returned an empty response.")

        try:
            response = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise SandboxError("Sandbox returned an invalid response.") from exc

        if not response.get("ok", False):
            raise SandboxError(response.get("error", "Sandbox command failed."))

        return response

    def ping(self) -> bool:
        try:
            return bool(self._request({"op": "ping"}).get("pong"))
        except SandboxError:
            return False

    def exec(self, command: str, workspace: str, cwd: str = ".") -> SandboxResult:
        response = self._request({
            "op": "exec",
            "command": command,
            "workspace": workspace,
            "cwd": cwd,
        })
        return SandboxResult(
            exit_code=int(response["exit_code"]),
            stdout=response.get("stdout", ""),
            stderr=response.get("stderr", ""),
        )
