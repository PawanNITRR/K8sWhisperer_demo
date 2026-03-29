#!/usr/bin/env python3
"""Test script for alert decision logic."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from agent.nodes.alert_decision import alert_decision_node

def test_alert_decision():
    # Mock state with critical anomaly
    critical_state = {
        "primary_anomaly": {
            "type": "crash_loop",
            "severity": "CRITICAL",
            "confidence": 0.9,
            "affected_resource": {"kind": "Pod", "name": "web-app", "namespace": "default"}
        },
        "diagnosis": "Pod is crashing due to out of memory",
        "plan": {"action": "restart", "confidence": 0.8},
        "result": "Successfully restarted pod",
        "should_auto_execute": True
    }

    print("Testing alert decision with critical anomaly...")
    try:
        result = alert_decision_node(critical_state)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")

    # Mock state with low severity
    low_state = {
        "primary_anomaly": {
            "type": "resource_usage",
            "severity": "LOW",
            "confidence": 0.5,
            "affected_resource": {"kind": "Pod", "name": "worker", "namespace": "default"}
        },
        "diagnosis": "Pod using slightly more CPU than usual",
        "plan": None,
        "result": "",
        "should_auto_execute": False
    }

    print("\nTesting alert decision with low severity anomaly...")
    try:
        result = alert_decision_node(low_state)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_alert_decision()