from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


def sleep_with_backoff(attempt: int, base: float = 0.5, cap: float = 8.0) -> None:
    delay = min(cap, base * (2**attempt))
    jitter = random.uniform(0, delay * 0.1)
    time.sleep(delay + jitter)


async def async_sleep_with_backoff(attempt: int, base: float = 0.5, cap: float = 8.0) -> None:
    delay = min(cap, base * (2**attempt))
    jitter = random.uniform(0, delay * 0.1)
    await asyncio.sleep(delay + jitter)


def retry_call(
    fn: Callable[[], T],
    *,
    attempts: int = 4,
    on_error: Callable[[Exception, int], None] | None = None,
) -> T:
    last: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            last = e
            if on_error:
                on_error(e, i)
            if i == attempts - 1:
                break
            sleep_with_backoff(i)
    assert last is not None
    raise last


async def retry_async(
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int = 4,
) -> T:
    last: Exception | None = None
    for i in range(attempts):
        try:
            return await fn()
        except Exception as e:
            last = e
            if i == attempts - 1:
                break
            await async_sleep_with_backoff(i)
    assert last is not None
    raise last
