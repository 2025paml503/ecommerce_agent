from __future__ import annotations

from dataclasses import dataclass

from .base import Scenario


@dataclass
class WorldModel:
    """Small inferred state used by the model-based reflex agent."""

    order_status: str
    delivery_status: str
    refund_status: str
    inspection_status: str

    @classmethod
    def from_scenario(cls, scenario: Scenario) -> "WorldModel":
        return cls(
            order_status=scenario.order_status,
            delivery_status=scenario.delivery_status,
            refund_status=scenario.refund_status,
            inspection_status=scenario.inspection_status,
        )