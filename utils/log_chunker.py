from __future__ import annotations

import re

ERROR_HINTS = re.compile(
    r"(error|fatal|exception|oom|killed|panic|traceback|failed|denied|forbidden)",
    re.IGNORECASE,
)


def tail_lines(text: str, max_lines: int = 100) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[-max_lines:])


def trim_to_max_chars(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def extract_error_snippets(text: str, max_chunks: int = 20) -> list[str]:
    lines = text.splitlines()
    hits: list[str] = []
    for line in lines:
        if ERROR_HINTS.search(line):
            hits.append(line.strip())
        if len(hits) >= max_chunks:
            break
    return hits


def prepare_logs_for_llm(
    raw_logs: str,
    *,
    tail_line_count: int = 100,
    max_chars: int = 48_000,
) -> str:
    """
    Reduce kubectl log noise: last N lines, trim to max chars, prepend error-like lines.
    """
    tailed = tail_lines(raw_logs, tail_line_count)
    snippets = extract_error_snippets(tailed)
    body = trim_to_max_chars(tailed, max_chars)
    if snippets:
        header = "[Likely error lines]\n" + "\n".join(snippets[:30]) + "\n\n[Log tail]\n"
    else:
        header = "[Log tail]\n"
    return header + body
