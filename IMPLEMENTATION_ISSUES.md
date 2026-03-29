# Implementation Issues Found

## 🐛 Issue 1: Missing Method `post_hitl_message()` 

**File:** [agent/nodes/hitl.py](agent/nodes/hitl.py) line 69

**Problem:** 
```python
slack.post_hitl_message(  # ❌ This method doesn't exist!
    channel=settings.slack_channel_id,
    thread_ts=None,
    title="K8sWhisperer HITL",
    blocks=_slack_blocks(thread_id, plan, diagnosis),
)
```

**Reality in SlackMCP:** Only `post_plain_text(channel, text)` exists

**Impact:** HITL Slack messages will crash at runtime

**Fix:**
- Either implement `post_hitl_message()` in SlackMCP
- Or use the existing `post_plain_text()` with formatted message

---

## 🐛 Issue 2: PrometheusMCP Instantiated Per-Cycle

**File:** [agent/nodes/observe.py](agent/nodes/observe.py) line 30

**Problem:**
```python
pm = PrometheusMCP()  # New instance every cycle
if pm.health().get("ok"):
    prom["cpu_throttle_sample"] = pm.query(...)
```

**Better Practice:** Use singleton like kubectl

```python
from mcp_servers import PrometheusMCP
# Add to __init__.py if needed
pm = get_prometheus_client()  # Singleton
```

---

## 🐛 Issue 3: SlackMCP Instantiated Per-Call

**File:** [agent/nodes/explain.py](agent/nodes/explain.py) line 59, [agent/nodes/hitl.py](agent/nodes/hitl.py) line 66

**Problem:**
```python
slack = SlackMCP()  # New instance every time
slack.post_plain_text(...)

slack = SlackMCP()  # Another new instance
slack.post_hitl_message(...)  # Method doesn't exist anyway
```

**Better Practice:** Use singleton pattern

```python
def get_slack_client():
    global _slack_client
    if _slack_client is None:
        _slack_client = SlackMCP()
    return _slack_client
```

---

## 🐛 Issue 4: RBACChecker Instantiated Per-Call

**File:** [agent/nodes/execute.py](agent/nodes/execute.py) line 116

**Problem:**
```python
rbac = RBACChecker()  # New instance every execution
ok, msg = rbac.is_allowed(plan)
```

**Better Practice:** Singleton or module-level instance

```python
_rbac_checker = RBACChecker()

def execute_node(...):
    ok, msg = _rbac_checker.is_allowed(plan)
```

---

## Summary

| Issue | Severity | Type | 
|-------|----------|------|
| Missing `post_hitl_message()` | 🔴 Critical | Bug - Runtime crash |
| Multiple PrometheusMCP instances | 🟡 Medium | Performance - Wasteful |
| Multiple SlackMCP instances | 🟡 Medium | Performance - Wasteful |
| Multiple RBACChecker instances | 🟡 Low | Performance - Negligible |

---

## Verdict on "Correct MCP Implementation"

**What it actually is:**
- ✅ Works in-process for LangGraph
- ❌ Not actual MCP protocol
- ❌ Has 1 critical bug (missing method)
- ⚠️ Inefficient instantiation patterns

**These adapters work locally but are NOT production-ready MCP servers.**
