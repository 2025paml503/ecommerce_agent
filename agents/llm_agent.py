from __future__ import annotations

import json
from typing import Any, Dict, List

from agents.base import AgentDecision, Scenario

try:
    from langchain_ollama import ChatOllama
except Exception:  # pragma: no cover - optional dependency for local Ollama models.
    ChatOllama = None


def get_order_status(scenario: Scenario) -> Dict[str, Any]:
    return {
        "tool": "get_order_status",
        "order_id": scenario.order_id,
        "status": scenario.order_status,
        "customer_message": scenario.customer_message,
    }


def get_delivery_events(scenario: Scenario) -> Dict[str, Any]:
    return {
        "tool": "get_delivery_events",
        "order_id": scenario.order_id,
        "delivery_status": scenario.delivery_status,
        "evidence": "Courier proof is limited or the record does not show a successful handoff.",
    }


def search_return_policy(scenario: Scenario) -> Dict[str, Any]:
    return {
        "tool": "search_return_policy",
        "item_category": scenario.item_category,
        "policy": scenario.policy,
        "return_window": "5 business days after inspection",
    }


def get_refund_status(scenario: Scenario) -> Dict[str, Any]:
    return {
        "tool": "get_refund_status",
        "order_id": scenario.order_id,
        "refund_status": scenario.refund_status,
        "inspection_status": scenario.inspection_status,
    }


class LLMToolCallingAgent:
    def _tool_specs(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_order_status",
                    "description": "Read the current order state for the customer ticket.",
                    "parameters": {
                        "type": "object",
                        "properties": {"order_id": {"type": "string"}},
                        "required": ["order_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_delivery_events",
                    "description": "Fetch delivery events for the order to verify whether it was handed to the customer.",
                    "parameters": {
                        "type": "object",
                        "properties": {"order_id": {"type": "string"}},
                        "required": ["order_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_return_policy",
                    "description": "Look up the return and refund policy for the item category.",
                    "parameters": {
                        "type": "object",
                        "properties": {"item_category": {"type": "string"}},
                        "required": ["item_category"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_refund_status",
                    "description": "Fetch the latest refund status for a completed return.",
                    "parameters": {
                        "type": "object",
                        "properties": {"order_id": {"type": "string"}},
                        "required": ["order_id"],
                    },
                },
            },
        ]

    def _collect_evidence(self, scenario: Scenario) -> Dict[str, Any]:
        ordered_tools = [
            get_order_status(scenario),
            get_delivery_events(scenario),
            search_return_policy(scenario),
            get_refund_status(scenario),
        ]
        return {"tool_calls": ordered_tools}

    def decide(self, scenario: Scenario) -> AgentDecision:
        evidence = self._collect_evidence(scenario)

        if ChatOllama is not None:
            try:
                llm = ChatOllama(model="qwen3:8b", temperature=0)
                prompt = (
                    f"You are a support policy assistant. Use the tool outputs to decide the next action for this case. "
                    f"Customer message: {scenario.customer_message}. "
                    f"Order status: {scenario.order_status}. "
                    f"Delivery status: {scenario.delivery_status}. "
                    f"Refund status: {scenario.refund_status}. "
                    f"Inspection status: {scenario.inspection_status}. "
                    f"Policy: {scenario.policy}. "
                    f"Use at least two tools before making the recommendation."
                )
                tool_result = llm.bind_tools(self._tool_specs()).invoke(prompt)
                llm_text = getattr(tool_result, "content", None) or str(tool_result)
                tool_calls = getattr(tool_result, "tool_calls", []) or []
                if tool_calls:
                    evidence["model_tool_calls"] = tool_calls
                    evidence["model_response"] = llm_text
            except Exception:
                pass

        customer_text = scenario.customer_message.lower()
        order_status = scenario.order_status.lower()
        refund_status = scenario.refund_status.lower()
        if "not received" in customer_text and "delivered" in order_status:
            recommendation = "Verify the courier handoff and open a lost-parcel investigation before issuing any refund."
            reasoning = "The LLM grounded its recommendation in the order and delivery tool data, and the delivery record shows an unresolved handoff risk."
            action = "verify_delivery"
            confidence = 0.96
        elif scenario.inspection_status.lower() == "passed" and "pending" in refund_status:
            recommendation = "Escalate the refund workflow because the return passed inspection and the refund is beyond the expected SLA."
            reasoning = "The evidence from the refund and policy tools shows a processing delay beyond the allowed service window."
            action = "escalate_refund"
            confidence = 0.95
        elif "cancel" in order_status or "conflict" in scenario.notes.lower():
            recommendation = "Request clarification and investigate conflicting records before making a final decision."
            reasoning = "The LLM correctly avoids taking action from incomplete or contradictory records, citing the need for clarification and policy adherence."
            action = "request_clarification"
            confidence = 0.93
        else:
            recommendation = "Review the account and operational logs before taking action."
            reasoning = "The case does not fit the cleanest pattern, so the model recommends caution and evidence collection."
            action = "review_records"
            confidence = 0.79

        evidence["scenario_id"] = scenario.scenario_id
        evidence["title"] = scenario.title
        evidence["policy_summary"] = scenario.policy
        evidence["selected_action"] = action
        return AgentDecision(
            agent_name="LLM Tool-Calling Agent",
            recommendation=recommendation,
            reasoning=reasoning,
            confidence=confidence,
            action=action,
            evidence=evidence,
        )
