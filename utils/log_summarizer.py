"""
LLM-based log processing functions.
Separated to avoid circular imports.
"""

from typing import Any

from utils.llm_invoke import invoke_with_retry
from utils.structured_logger import get_logger

_log = get_logger(__name__)


def summarize_logs_plain_english(raw_logs: str) -> str:
    """
    Convert messy Kubernetes logs into simple plain English summary.
    Uses LLM to generate human-readable explanation of what happened.
    """
    if not raw_logs or raw_logs.strip() == "":
        return "No logs available."

    # Quick pattern-based analysis first
    lines = raw_logs.splitlines()
    error_lines = [line for line in lines if "error" in line.lower() or "fatal" in line.lower() or "exception" in line.lower()]

    # Categorize the type of issue
    issue_type = "unknown"
    if "crashloopbackoff" in raw_logs.lower() or "back-off restarting failed container" in raw_logs.lower():
        issue_type = "crash_loop"
    elif "outofmemory" in raw_logs.lower() or "oom" in raw_logs.lower() or "killed" in raw_logs.lower():
        issue_type = "out_of_memory"
    elif "imagepullbackoff" in raw_logs.lower() or "errimagepull" in raw_logs.lower():
        issue_type = "image_pull_failure"
    elif "connection refused" in raw_logs.lower() or "connection reset" in raw_logs.lower():
        issue_type = "network_issue"
    elif "readiness probe failed" in raw_logs.lower() or "liveness probe failed" in raw_logs.lower():
        issue_type = "startup_failure"

    # Prepare a focused summary for LLM
    sample_lines = lines[-20:] if len(lines) > 20 else lines  # Last 20 lines
    error_sample = error_lines[-10:] if len(error_lines) > 10 else error_lines  # Last 10 errors

    summary_input = f"""
Issue Type Detected: {issue_type}

Recent Log Lines:
{chr(10).join(sample_lines)}

Error Lines Found:
{chr(10).join(error_sample) if error_sample else "No obvious errors found"}

Total log lines: {len(lines)}
Error lines: {len(error_lines)}
"""

    try:
        # Import here to avoid circular imports
        from langchain_core.messages import HumanMessage, SystemMessage
        from agent.llm_factory import get_chat_model

        model = get_chat_model()
        system_prompt = """You are a Kubernetes expert. Convert these messy container logs into a simple, clear plain English explanation.

Focus on:
- What went wrong (if anything)
- Key events in chronological order
- Root cause indicators
- Keep it under 200 words
- Use simple language, avoid technical jargon unless necessary

If logs are normal/healthy, say so clearly."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=summary_input)
        ]

        response = invoke_with_retry(
            lambda: model.invoke(messages),
            log=_log,
            operation="log_summarize",
        )
        summary = str(response.content).strip()

        # Ensure it's not too long
        if len(summary) > 500:
            summary = summary[:500] + "..."

        return summary

    except Exception as e:
        # Fallback to pattern-based summary
        return _fallback_log_summary(raw_logs, issue_type)


def _fallback_log_summary(raw_logs: str, issue_type: str) -> str:
    """Fallback summary when LLM fails."""
    lines = raw_logs.splitlines()
    total_lines = len(lines)
    error_count = len([line for line in lines if "error" in line.lower() or "fatal" in line.lower() or "exception" in line.lower()])

    if issue_type == "crash_loop":
        return f"Container is crashing and restarting repeatedly. Found {error_count} error indications in {total_lines} total log lines. The application appears to be failing immediately after startup."
    elif issue_type == "out_of_memory":
        return f"Container is running out of memory. Found {error_count} error indications in {total_lines} total log lines. The application is being killed due to memory exhaustion."
    elif issue_type == "image_pull_failure":
        return f"Container image cannot be pulled. Found {error_count} error indications in {total_lines} total log lines. There are issues with accessing the container registry."
    elif issue_type == "network_issue":
        return f"Network connectivity problems detected. Found {error_count} error indications in {total_lines} total log lines. The application cannot connect to required services."
    elif issue_type == "startup_failure":
        return f"Container failing health checks during startup. Found {error_count} error indications in {total_lines} total log lines. Readiness or liveness probes are failing."
    else:
        if error_count > 0:
            return f"Application has encountered errors. Found {error_count} error indications in {total_lines} total log lines. The logs show various issues that need investigation."
        else:
            return f"Application appears to be running normally. No obvious errors found in {total_lines} log lines. The container seems healthy."