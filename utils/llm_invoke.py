"""Retry LLM calls on transient provider errors (429, overload, brief 5xx, timeouts)."""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from typing import Any


def _retry_after_seconds(exc: BaseException) -> float | None:
    text = str(exc)
    m = re.search(r"retry in ([0-9]+(?:\.[0-9]+)?)\s*s", text, re.I)
    if m:
        return min(float(m.group(1)), 120.0)
    m = re.search(r"retryDelay['\"]:\s*['\"](\d+)s", text)
    if m:
        return min(float(m.group(1)), 120.0)
    return None


def _is_daily_or_hard_quota(exc: BaseException) -> bool:
    """Daily caps etc. — waiting seconds will not reset these."""
    text = str(exc)
    if "GenerateRequestsPerDay" in text or "PerDayPerProject" in text:
        return True
    tl = text.lower()
    if "quota exceeded" in tl and "per day" in tl:
        return True
    return False


def _is_retryable(exc: BaseException) -> bool:
    if _is_daily_or_hard_quota(exc):
        return False
    text = str(exc)
    tl = text.lower()
    if "401" in text or "400" in text or "invalid api key" in tl or "api key not valid" in tl or "expired" in tl:
        return False
    if "403" in text and "forbidden" in tl:
        return False
    return any(
        x in tl
        for x in (
            "429",
            "resource_exhausted",
            "503",
            "502",
            "500",
            "timeout",
            "timed out",
            "connection reset",
            "temporarily unavailable",
            "rate limit",
            "overloaded",
            "try again",
            "service unavailable",
            "deadline exceeded",
        )
    )


def invoke_with_retry(
    fn: Callable[[], T],
    *,
    log: Any,
    attempts: int = 8,
    operation: str = "llm",
) -> T:
    """
    Run `fn` and retry on transient errors with backoff.
    Respects server-suggested delay when present (e.g. Gemini \"retry in 27s\").
    """
    last: BaseException | None = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            last = e
            if i == attempts - 1 or not _is_retryable(e):
                raise
            delay = _retry_after_seconds(e)
            if delay is None:
                delay = min(2.0**i, 45.0)
            log.info(
                "%s: transient %s, retry %s/%s in %.1fs",
                operation,
                type(e).__name__,
                i + 1,
                attempts,
                delay,
            )
            time.sleep(delay)
    assert last is not None
    raise last
