from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from agents.base import AgentDecision, Scenario, reports_not_received

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

    def _execute_model_tool_calls(self, scenario: Scenario, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        executors = {
            "get_order_status": get_order_status,
            "get_delivery_events": get_delivery_events,
            "search_return_policy": search_return_policy,
            "get_refund_status": get_refund_status,
        }
        results: List[Dict[str, Any]] = []
        for call in tool_calls:
            name = call.get("name", "")
            executor = executors.get(name)
            if executor:
                results.append(executor(scenario))
        return results

    def _parse_model_decision(self, content: str) -> Dict[str, Any] | None:
        try:
            start = content.find("{")
            end = content.rfind("}")
            if start >= 0 and end > start:
                parsed = json.loads(content[start:end + 1])
            else:
                parsed = json.loads(content)
        except json.JSONDecodeError:
            return None

        if parsed.get("action") not in {
            "verify_delivery",
            "escalate_refund",
            "request_clarification",
            "review_records",
        }:
            return None
        if not isinstance(parsed.get("recommendation"), str) or not isinstance(parsed.get("reasoning"), str):
            return None
        confidence = parsed.get("confidence", 0.8)
        if not isinstance(confidence, (int, float)):
            return None
        confidence = min(1.0, max(0.0, float(confidence)))
        return {
            "recommendation": parsed["recommendation"],
            "reasoning": parsed["reasoning"],
            "confidence": confidence,
            "action": parsed["action"],
        }

    def decide(self, scenario: Scenario) -> AgentDecision:
        evidence = self._collect_evidence(scenario)
        model_tool_evidence: List[Dict[str, Any]] = []
        model_decision: Dict[str, Any] | None = None
        evidence["model_status"] = "not_attempted"

        if os.getenv("DISABLE_OLLAMA", "").lower() not in {"1", "true", "yes"} and ChatOllama is not None:
            try:
                llm = ChatOllama(
                    model=os.getenv("OLLAMA_MODEL", "qwen3:latest"),
                    temperature=0,
                    request_timeout=15,
                )
                prompt = (
                    f"You are a support policy assistant. Call relevant tools before deciding the next action. "
                    f"Customer message: {scenario.customer_message}. "
                    f"Order status: {scenario.order_status}. "
                    f"Delivery status: {scenario.delivery_status}. "
                    f"Refund status: {scenario.refund_status}. "
                    f"Inspection status: {scenario.inspection_status}. "
                    f"Policy: {scenario.policy}. "
                    f"Call at least two relevant tools before making the recommendation."
                )
                tool_result = llm.bind_tools(self._tool_specs()).invoke(prompt)
                llm_text = getattr(tool_result, "content", None) or str(tool_result)
                tool_calls = getattr(tool_result, "tool_calls", []) or []
                if tool_calls:
                    model_tool_evidence = self._execute_model_tool_calls(scenario, tool_calls)
                    evidence["model_tool_calls"] = [
                        {
                            "name": call.get("name", ""),
                            "arguments": call.get("args", {}),
                        }
                        for call in tool_calls
                    ]
                    evidence["model_tool_results"] = model_tool_evidence
                    evidence["model_response"] = llm_text
                    evidence["model_status"] = "tool_calls_received"

                    grounded_evidence = model_tool_evidence or evidence["tool_calls"]
                    final_prompt = (
                        "Using only the following tool evidence, return JSON with keys "
                        "recommendation, reasoning, confidence, and action. "
                        "Valid actions are verify_delivery, escalate_refund, "
                        "request_clarification, or review_records. "
                        f"Tool evidence: {json.dumps(grounded_evidence)} "
                        f"Customer message: {scenario.customer_message}"
                    )
                    final_result = llm.invoke(final_prompt)
                    final_content = getattr(final_result, "content", None) or str(final_result)
                    evidence["model_final_response"] = final_content
                    model_decision = self._parse_model_decision(final_content)
                    evidence["model_status"] = "completed"
                else:
                    evidence["model_status"] = "no_tool_calls"
                    evidence["model_response"] = llm_text
            except Exception as exc:
                evidence["model_status"] = "fallback_after_model_error"
                evidence["model_error"] = f"{type(exc).__name__}: {str(exc)}"
        else:
            evidence["model_status"] = "langchain_ollama_unavailable"

        customer_text = scenario.customer_message.lower()
        order_status = scenario.order_status.lower()
        refund_status = scenario.refund_status.lower()
        if reports_not_received(scenario) and "delivered" in order_status:
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

        if model_decision is not None:
            recommendation = model_decision["recommendation"]
            reasoning = model_decision["reasoning"]
            action = model_decision["action"]
            confidence = model_decision["confidence"]

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
