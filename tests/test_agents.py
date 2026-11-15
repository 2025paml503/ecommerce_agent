import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.classical_agents import (
    GoalBasedAgent,
    LearningAgent,
    ModelBasedReflexAgent,
    SimpleReflexAgent,
    UtilityBasedAgent,
)
from agents.llm_agent import LLMToolCallingAgent
from data.scenarios import SCENARIOS


def test_scenarios_are_present():
    assert len(SCENARIOS) == 3
    ids = {scenario.scenario_id for scenario in SCENARIOS}
    assert ids == {"A", "B", "C"}


def test_all_agents_produce_decisions():
    agents = [
        SimpleReflexAgent(),
        ModelBasedReflexAgent(),
        GoalBasedAgent(),
        UtilityBasedAgent(),
        LearningAgent(),
        LLMToolCallingAgent(),
    ]

    for scenario in SCENARIOS:
        decisions = [agent.decide(scenario) for agent in agents]
        assert len(decisions) == 6
        for decision in decisions:
            assert decision.recommendation
            assert decision.reasoning
            assert 0 <= decision.confidence <= 1
            assert decision.action


def test_llm_agent_uses_two_or_more_tool_evidence_items():
    scenario = next(item for item in SCENARIOS if item.scenario_id == "A")
    result = LLMToolCallingAgent().decide(scenario)
    assert len(result.evidence["tool_calls"]) >= 2
    assert "scenario_id" in result.evidence
