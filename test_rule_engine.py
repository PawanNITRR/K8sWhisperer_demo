#!/usr/bin/env python3
"""Test script for rule-based anomaly handling."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from agent.rule_engine import generate_plan_for_anomaly
from schemas.enums import AnomalyType, Severity

def test_rule_based_planning():
    # Test cases for different anomaly types
    test_cases = [
        {
            "type": AnomalyType.CRASH_LOOP_BACK_OFF.value,
            "severity": Severity.HIGH.value,
            "affected_resource": {"kind": "Pod", "namespace": "default", "name": "web-app"},
            "expected_action": "restart_pod"
        },
        {
            "type": AnomalyType.OOM_KILLED.value,
            "severity": Severity.HIGH.value,
            "affected_resource": {"kind": "Pod", "namespace": "default", "name": "worker"},
            "expected_action": "patch_resource_limits"
        },
        {
            "type": AnomalyType.IMAGE_PULL_BACK_OFF.value,
            "severity": Severity.MEDIUM.value,
            "affected_resource": {"kind": "Pod", "namespace": "default", "name": "api"},
            "expected_action": "alert_human"
        },
        {
            "type": AnomalyType.NODE_NOT_READY.value,
            "severity": Severity.CRITICAL.value,
            "affected_resource": {"kind": "Node", "namespace": "", "name": "node-1"},
            "expected_action": "alert_human"
        }
    ]

    print("Testing rule-based planning...")
    for i, test_case in enumerate(test_cases, 1):
        plan = generate_plan_for_anomaly(test_case)
        if plan:
            success = plan.action.value == test_case["expected_action"]
            status = "✓" if success else "✗"
            print(f"{status} Test {i}: {test_case['type']} -> {plan.action.value} (expected {test_case['expected_action']})")
        else:
            print(f"✗ Test {i}: {test_case['type']} -> No plan generated")

if __name__ == "__main__":
    test_rule_based_planning()