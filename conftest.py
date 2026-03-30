"""Pytest: deterministic settings (mock LLM, mock cluster) so tests do not require API keys."""

from __future__ import annotations

import os

os.environ["LLM_PROVIDER"] = "mock"
os.environ["MOCK_CLUSTER"] = "1"

import pytest

from config import get_settings


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
