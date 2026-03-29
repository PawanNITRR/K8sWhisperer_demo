from __future__ import annotations

import subprocess
from typing import Any

from utils.structured_logger import get_logger


class BaseMCP:
    def __init__(self, name: str):
        self.name = name
        self.log = get_logger(name)

    def run_cmd(self, cmd: list[str]) -> str:
        """
        Run a shell command safely and return stdout.
        Raises error if command fails.
        """
        try:
            self.log.info("Running command: %s", " ".join(cmd))
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return res.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.log.error("Command failed: %s", e.stderr)
            raise RuntimeError(e.stderr or str(e))

    def safe_call(self, fn, *args, **kwargs) -> Any:
        """
        Wrap function calls with logging + error handling.
        """
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            self.log.exception("MCP call failed")
            raise e