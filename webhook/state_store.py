from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from config import get_settings


class StateStore:
    """
    Persists processed Slack action IDs to avoid duplicate resumes (Slack retries).
    Also stores optional metadata (thread_id -> last action).
    """

    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or get_settings().state_store_path)
        self._lock = Lock()

    def _read(self) -> dict:
        if not self.path.exists():
            return {"processed_action_ids": [], "meta": {}}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"processed_action_ids": [], "meta": {}}

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def seen_action(self, action_id: str) -> bool:
        with self._lock:
            data = self._read()
            seen = set(data.get("processed_action_ids") or [])
            return action_id in seen

    def mark_action(self, action_id: str) -> None:
        with self._lock:
            data = self._read()
            ids = list(data.get("processed_action_ids") or [])
            if action_id not in ids:
                ids.append(action_id)
            data["processed_action_ids"] = ids[-5000:]
            self._write(data)
