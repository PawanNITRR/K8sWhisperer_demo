"""Quick sanity check: LangGraph imports and optional graph compile. Run from repo root."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> int:
    os.environ.setdefault("MOCK_CLUSTER", "1")
    os.environ.setdefault("LLM_PROVIDER", "mock")
    try:
        from langgraph.types import Command, interrupt  # noqa: F401
    except ImportError as e:
        print("FAIL: langgraph.types missing — run: pip install -r requirements.txt", e, file=sys.stderr)
        return 1
    try:
        from agent.graph import build_graph

        build_graph()
    except Exception as e:
        print("FAIL: build_graph()", e, file=sys.stderr)
        return 1
    print("OK: langgraph.types + build_graph()")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
