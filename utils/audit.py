from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from pydantic import TypeAdapter

from schemas.models import LogEntry


class AuditLogger:
    """Append-only JSON list of LogEntry records (plain-English audit trail)."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = Lock()

    def append(self, entry: LogEntry) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            existing: list[dict] = []
            if self.path.exists():
                try:
                    existing = json.loads(self.path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    existing = []
            adapter = TypeAdapter(LogEntry)
            existing.append(adapter.dump_python(entry, mode="json"))
            self.path.write_text(json.dumps(existing, indent=2, default=str), encoding="utf-8")
