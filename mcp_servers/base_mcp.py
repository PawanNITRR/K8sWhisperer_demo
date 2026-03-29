from __future__ import annotations

from abc import ABC, abstractmethod


class BaseMCP(ABC):
    """Base type for MCP-style tool servers (in-process adapters)."""

    name: str = "base"

    @abstractmethod
    def health(self) -> dict:
        raise NotImplementedError
