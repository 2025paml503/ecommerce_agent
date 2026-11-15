from __future__ import annotations

from typing import List

try:
    from assignment1.agents.base import Scenario
except ModuleNotFoundError:  # pragma: no cover - script execution path fallback
    from agents.base import Scenario

SCENARIOS: List[Scenario] = [
    Scenario(
        scenario_id="A",
        title="Delivered but not received",
        order_id="ORD-1001",
        customer_message="The package was marked delivered yesterday, but I never received it. The delivery driver did not leave a parcel or leave any message.",
        order_status="Delivered",
        delivery_status="Delivered to address; no proof of handoff recorded",
        refund_status="Not requested",
        inspection_status="Not applicable",
        item_category="Electronics",
        notes="Customer reports a failed delivery or possible misdelivery. Order status and customer evidence do not match.",
        policy="If a customer reports a package not received after delivery, verify delivery events, check courier proof, and investigate before issuing a refund.",
        expected_next_action="Verify delivery evidence and initiate investigation before refunding.",
    ),
    Scenario(
        scenario_id="B",
        title="Refund overdue after return inspection",
        order_id="ORD-2007",
        customer_message="I returned the item last week. It passed inspection, but my refund still has not been issued even though the expected refund date has passed.",
        order_status="Returned",
        delivery_status="Return receipt scanned and logged",
        refund_status="Pending beyond SLA",
        inspection_status="Passed",
        item_category="Home Goods",
        notes="Return inspection passed, but refund is still pending beyond policy SLA. That suggests a processing delay or internal status mismatch.",
        policy="Approved returns should be refunded within 5 business days after inspection. Delayed refunds should be escalated to finance or support operations.",
        expected_next_action="Escalate refund workflow and verify finance status.",
    ),
    Scenario(
        scenario_id="C",
        title="Conflicting or incomplete records",
        order_id="ORD-3004",
        customer_message="I never got the order, but the system shows it was cancelled. I am not sure if the item was sent or not.",
        order_status="Cancelled",
        delivery_status="No delivery event available",
        refund_status="NA",
        inspection_status="Not applicable",
        item_category="Accessories",
        notes="Order status and customer claim conflict; historic data is incomplete. Need clarification before policy action.",
        policy="When the order record and the customer account contain conflicting or incomplete information, ask for clarification and gather supporting evidence before any final decision.",
        expected_next_action="Request clarification and review internal logs to resolve the discrepancy.",
    ),
]


def get_scenarios() -> List[Scenario]:
    return [Scenario(**scenario.__dict__) for scenario in SCENARIOS]
