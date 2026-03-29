from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from agent.nodes.alert_decision import alert_decision_node
from agent.nodes.detect import detect_node
from agent.nodes.diagnose import diagnose_node
from agent.nodes.execute import execute_node
from agent.nodes.explain import explain_node
from agent.nodes.hitl import hitl_node
from agent.nodes.observe import observe_node
from agent.nodes.plan import plan_node
from agent.nodes.safety_gate import safety_gate_node
from agent.state import AgentState


def route_after_detect(state: AgentState) -> str:
    if state.get("primary_anomaly"):
        return "diagnose"
    return "explain"


def route_after_plan(state: AgentState) -> str:
    if state.get("plan"):
        return "safety_gate"
    return "explain"


def route_after_safety(state: AgentState) -> str:
    if state.get("should_auto_execute"):
        return "execute"
    return "hitl"


def route_after_hitl(state: AgentState) -> str:
    if state.get("approved"):
        return "execute"
    return "explain"


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("observe", observe_node)
    g.add_node("detect", detect_node)
    g.add_node("diagnose", diagnose_node)
    g.add_node("plan", plan_node)
    g.add_node("safety_gate", safety_gate_node)
    g.add_node("execute", execute_node)
    g.add_node("alert_decision", alert_decision_node)
    g.add_node("hitl", hitl_node)
    g.add_node("explain", explain_node)

    g.add_edge(START, "observe")
    g.add_edge("observe", "detect")
    g.add_conditional_edges("detect", route_after_detect, {"diagnose": "diagnose", "explain": "explain"})
    g.add_edge("diagnose", "plan")
    g.add_conditional_edges("plan", route_after_plan, {"safety_gate": "safety_gate", "explain": "explain"})
    g.add_conditional_edges("safety_gate", route_after_safety, {"execute": "execute", "hitl": "hitl"})
    g.add_conditional_edges("hitl", route_after_hitl, {"execute": "execute", "explain": "explain"})
    g.add_edge("execute", "alert_decision")
    g.add_edge("alert_decision", "explain")
    g.add_edge("explain", END)

    return g.compile(checkpointer=MemorySaver())
