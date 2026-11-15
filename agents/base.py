from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Scenario:
    scenario_id: str
    title: str
    order_id: str
    customer_message: str
    order_status: str
    delivery_status: str
    refund_status: str
    inspection_status: str
    item_category: str
    notes: str = ""
    policy: str = ""
    expected_next_action: str = ""


@dataclass
class AgentDecision:
    agent_name: str
    recommendation: str
    reasoning: str
    confidence: float
    evidence: Dict[str, Any] = field(default_factory=dict)
    action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "recommendation": self.recommendation,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "action": self.action,
            "evidence": self.evidence,
        }
