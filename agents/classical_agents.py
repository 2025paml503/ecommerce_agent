from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

try:
    from .base import AgentDecision, Scenario, reports_not_received
except ImportError:  # pragma: no cover - direct-script compatibility
    from agents.base import AgentDecision, Scenario, reports_not_received


class SimpleReflexAgent:
    def decide(self, scenario: Scenario) -> AgentDecision:
        text = scenario.customer_message.lower()
        order = scenario.order_status.lower()
        refund = scenario.refund_status.lower()
        if reports_not_received(scenario) and "delivered" in order:
            recommendation = "Open a delivery verification case and investigate the courier proof before refunding."
            reasoning = "The system says the order was delivered, while the customer reports no receipt. This is a classic delivery-failure pattern that should be checked before any refund decision."
            action = "verify_delivery"
            confidence = 0.91
        elif scenario.inspection_status.lower() == "passed" and "pending" in refund:
            recommendation = "Escalate the refund workflow because the return has already passed inspection and is overdue."
            reasoning = "Inspection was successful and the refund remains pending beyond the expected window, which points to a processing bottleneck or status mismatch."
            action = "escalate_refund"
            confidence = 0.93
        elif "cancel" in order or "conflict" in scenario.notes.lower():
            recommendation = "Request clarification and review the order history before making a policy decision."
            reasoning = "The record is internally inconsistent or incomplete, so any action without additional evidence would be risky and potentially incorrect."
            action = "request_clarification"
            confidence = 0.88
        else:
            recommendation = "Check the operational record and policy rules before taking action."
            reasoning = "The combination of state and message does not point to a single risk pattern, so the case needs evidence review."
            action = "review_records"
            confidence = 0.72
        return AgentDecision(
            agent_name="Simple Reflex Agent",
            recommendation=recommendation,
            reasoning=reasoning,
            confidence=confidence,
            action=action,
            evidence={
                "order_status": scenario.order_status,
                "delivery_status": scenario.delivery_status,
                "refund_status": scenario.refund_status,
                "inspection_status": scenario.inspection_status,
            },
        )


class ModelBasedReflexAgent:
    def decide(self, scenario: Scenario) -> AgentDecision:
        customer_text = scenario.customer_message.lower()
        if reports_not_received(scenario) and "delivered" in scenario.order_status.lower():
            recommendation = "Model the situation as a likely delivery exception and verify handoff evidence."
            reasoning = "The delivery state suggests a possible lost parcel or misdelivery. The internal model predicts a high chance of delivery failure until evidence is checked."
            action = "verify_delivery"
            confidence = 0.92
        elif scenario.inspection_status.lower() == "passed" and "pending" in scenario.refund_status.lower():
            recommendation = "Model the failure as a refund-processing delay and escalate to finance."
            reasoning = "The model shows the return is accepted and the payment step is overdue, indicating a workflow failure rather than a policy dispute."
            action = "escalate_refund"
            confidence = 0.94
        elif "cancel" in scenario.order_status.lower() or "conflict" in scenario.notes.lower():
            recommendation = "Model the case as incomplete information and request clarification before any cash action."
            reasoning = "The known facts do not support a stable world state, so the correct next step is to gather more evidence."
            action = "request_clarification"
            confidence = 0.9
        else:
            recommendation = "Collect more evidence to update the model before deciding."
            reasoning = "The current state is uncertain, and the decision should only be made after the model can explain the missing facts."
            action = "review_records"
            confidence = 0.76
        return AgentDecision(
            agent_name="Model-Based Reflex Agent",
            recommendation=recommendation,
            reasoning=reasoning,
            confidence=confidence,
            action=action,
            evidence={
                "model_inference": "delivery_exception" if action == "verify_delivery" else "refund_delay" if action == "escalate_refund" else "incomplete_data",
                "order_status": scenario.order_status,
                "customer_claim": scenario.customer_message,
            },
        )


class GoalBasedAgent:
    def decide(self, scenario: Scenario) -> AgentDecision:
        goals = {
            "verify_delivery": 0.0,
            "escalate_refund": 0.0,
            "request_clarification": 0.0,
        }

        if reports_not_received(scenario) and "delivered" in scenario.order_status.lower():
            goals["verify_delivery"] = 0.95
        if scenario.inspection_status.lower() == "passed" and "pending" in scenario.refund_status.lower():
            goals["escalate_refund"] = 0.96
        if "cancel" in scenario.order_status.lower() or "conflict" in scenario.notes.lower():
            goals["request_clarification"] = 0.94

        best_action = max(goals, key=goals.get)
        if best_action == "verify_delivery":
            recommendation = "Verify the delivery chain and confirm whether the order was misdelivered or lost."
            reasoning = "Protecting the customer and resolving the mismatch between the status and the report is the highest-priority operational goal."
            confidence = 0.9
        elif best_action == "escalate_refund":
            recommendation = "Escalate the refund to the operations team without changing the order."
            reasoning = "The policy goal is to resolve the accepted return promptly and within the expected refund SLA."
            confidence = 0.95
        else:
            recommendation = "Clarify the customer message and the order record before any refund or replacement action."
            reasoning = "The primary goal is to avoid making a wrong decision from contradictory data."
            confidence = 0.89

        return AgentDecision(
            agent_name="Goal-Based Agent",
            recommendation=recommendation,
            reasoning=reasoning,
            confidence=confidence,
            action=best_action,
            evidence={"goal_scores": goals, "primary_goal": best_action},
        )


class UtilityBasedAgent:
    def decide(self, scenario: Scenario) -> AgentDecision:
        candidates = {
            "verify_delivery": 0.0,
            "escalate_refund": 0.0,
            "request_clarification": 0.0,
        }

        if reports_not_received(scenario) and "delivered" in scenario.order_status.lower():
            candidates["verify_delivery"] = 0.95
            candidates["request_clarification"] = 0.44
            candidates["escalate_refund"] = 0.21
        elif scenario.inspection_status.lower() == "passed" and "pending" in scenario.refund_status.lower():
            candidates["escalate_refund"] = 0.96
            candidates["verify_delivery"] = 0.31
            candidates["request_clarification"] = 0.19
        elif "cancel" in scenario.order_status.lower() or "conflict" in scenario.notes.lower():
            candidates["request_clarification"] = 0.97
            candidates["verify_delivery"] = 0.28
            candidates["escalate_refund"] = 0.1
        else:
            candidates["review_records"] = 0.6

        best_action = max(candidates, key=candidates.get)

        if best_action == "verify_delivery":
            recommendation = "Choose the action with the best expected value: confirm delivery evidence before refunding."
            reasoning = "The expected benefit of verifying the courier proof is higher than the cost of doing a broad refund or an immediate replacement."
            confidence = 0.91
        elif best_action == "escalate_refund":
            recommendation = "Choose the refund escalation path because the expected value of a fast resolution outweighs the cost of delay."
            reasoning = "The item has been inspected and approved, so the cost of waiting is higher than the cost of escalating."
            confidence = 0.93
        elif best_action == "request_clarification":
            recommendation = "Choose clarification because the cost of a wrong decision is higher than the cost of waiting for more evidence."
            reasoning = "The expected utility is highest when data quality is improved before any final action."
            confidence = 0.9
        else:
            recommendation = "Review additional records to estimate which action yields the best expected utility."
            reasoning = "There is no single high-confidence choice in the current state."
            confidence = 0.7

        return AgentDecision(
            agent_name="Utility-Based Agent",
            recommendation=recommendation,
            reasoning=reasoning,
            confidence=confidence,
            action=best_action,
            evidence={"utility_scores": candidates},
        )


class LearningAgent:
    def __init__(self, experience_path: str | None = None):
        base = Path(__file__).resolve().parents[1]
        self.experience_path = Path(experience_path) if experience_path else base / "experience" / "experience.json"
        self.experience_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.experience_path.exists():
            self.experience_path.write_text(json.dumps({"total_decisions": 0, "success_counts": {}, "failure_counts": {}, "scenario_history": {}}, indent=2), encoding="utf-8")

    def _load_experience(self) -> Dict[str, Any]:
        try:
            return json.loads(self.experience_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"total_decisions": 0, "success_counts": {}, "failure_counts": {}, "scenario_history": {}}

    def _save_experience(self, data: Dict[str, Any]) -> None:
        self.experience_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def decide(self, scenario: Scenario) -> AgentDecision:
        experience = self._load_experience()
        success_counts = experience.get("success_counts", {})
        failure_counts = experience.get("failure_counts", {})

        action_scores = {
            "verify_delivery": 0.35,
            "escalate_refund": 0.35,
            "request_clarification": 0.35,
        }

        for action, value in success_counts.items():
            action_scores[action] = action_scores.get(action, 0.35) + (value * 0.08)
        for action, value in failure_counts.items():
            action_scores[action] = action_scores.get(action, 0.35) - (value * 0.06)

        if reports_not_received(scenario) and "delivered" in scenario.order_status.lower():
            action_scores["verify_delivery"] += 0.75
        elif scenario.inspection_status.lower() == "passed" and "pending" in scenario.refund_status.lower():
            action_scores["escalate_refund"] += 0.75
        elif "cancel" in scenario.order_status.lower() or "conflict" in scenario.notes.lower():
            action_scores["request_clarification"] += 0.75

        best_action = max(action_scores, key=action_scores.get)
        if best_action == "verify_delivery":
            recommendation = "Use past experience to prioritize delivery verification because it has the strongest success rate in similar cases."
            reasoning = "The learning loop rates delivery verification highly in this pattern and improves the recommendation as more successful outcomes are recorded."
            confidence = 0.87
        elif best_action == "escalate_refund":
            recommendation = "Use the refund escalation pattern that has historically resolved overdue returns efficiently."
            reasoning = "Past resolution data for approved returns with delayed refunds creates a strong bias toward escalation."
            confidence = 0.9
        else:
            recommendation = "Use the clarification path because conflicting records have historically produced the lowest regret."
            reasoning = "When a case contains conflicts, prior fails show that clarifying first avoids the most expensive mistakes."
            confidence = 0.88

        outcome = "success" if best_action in {"verify_delivery", "escalate_refund", "request_clarification"} else "failure"
        success_counts[best_action] = success_counts.get(best_action, 0) + 1
        experience["success_counts"] = success_counts
        experience["total_decisions"] = experience.get("total_decisions", 0) + 1
        experience["scenario_history"].setdefault(scenario.scenario_id, []).append({"action": best_action, "outcome": outcome})
        self._save_experience(experience)

        return AgentDecision(
            agent_name="Learning Agent",
            recommendation=recommendation,
            reasoning=reasoning,
            confidence=confidence,
            action=best_action,
            evidence={
                "historical_success_counts": success_counts,
                "historical_failure_counts": failure_counts,
                "scenario_id": scenario.scenario_id,
                "experience_path": str(self.experience_path),
                "experience_basis": "Success/failure counts influence the action score; scenario outcomes are appended to history.",
                "limitation": "Experience is a small local simulation and is not evidence of real-world refund or delivery outcomes.",
            },
        )
