from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

HISTORY_FILE = Path(os.getenv("HISTORY_FILE", "/data/history.json"))
_LOCK = threading.Lock()


def _default() -> dict:
    return {"next_id": 1, "records": []}


def _load_unlocked() -> dict:
    if not HISTORY_FILE.exists():
        return _default()
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _default()
    if not isinstance(data, dict):
        return _default()
    data.setdefault("next_id", 1)
    data.setdefault("records", [])
    return data


def _save_unlocked(data: dict) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = HISTORY_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(HISTORY_FILE)


def add_record(record: dict) -> int:
    with _LOCK:
        data = _load_unlocked()
        record_id = int(data["next_id"])
        data["next_id"] = record_id + 1
        saved = {
            "id": record_id,
            "solved_at": datetime.now(timezone.utc).isoformat(),
            **record,
        }
        data["records"].append(saved)
        data["records"] = data["records"][-5000:]
        _save_unlocked(data)
        return record_id


def list_records() -> list[dict]:
    with _LOCK:
        return list(reversed(_load_unlocked()["records"]))


def get_record(record_id: int) -> dict | None:
    with _LOCK:
        for record in _load_unlocked()["records"]:
            if int(record.get("id", -1)) == record_id:
                return record
    return None
