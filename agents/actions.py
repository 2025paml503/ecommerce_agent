"""
Shared vocabularies of supported actions for agents.

All six agents choose from this same list so that their decisions can be put side by side in a comparison table.
Every action is a Recommendation for the human support agent - nothing here issues a refund or changes an order.
"""

VERIFY_DELIVERY = "verify_delivery"
ESCALATE_REFUND = "escalate_refund"
REQUEST_CLARIFICATION = "request_clarification"
REVIEW_RECORDS = "review_records"

SUPPORTED_ACTIONS = (
    VERIFY_DELIVERY,
    ESCALATE_REFUND,
    REQUEST_CLARIFICATION,
    REVIEW_RECORDS,
)