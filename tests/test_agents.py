import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import pytest

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
import agents.llm_agent as llm_module


@pytest.fixture(autouse=True)
def disable_real_ollama(monkeypatch):
    monkeypatch.setattr(llm_module, "ChatOllama", None)


def test_scenarios_are_present():
    assert len(SCENARIOS) == 3
    ids = {scenario.scenario_id for scenario in SCENARIOS}
    assert ids == {"A", "B", "C"}


def test_all_agents_produce_decisions():
    with TemporaryDirectory() as directory:
        experience_path = str(Path(directory) / "experience.json")
        agents = [
            SimpleReflexAgent(),
            ModelBasedReflexAgent(),
            GoalBasedAgent(),
            UtilityBasedAgent(),
            LearningAgent(experience_path=experience_path),
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


def test_required_actions_for_scenarios():
    expected = {
        "A": "verify_delivery",
        "B": "escalate_refund",
        "C": "request_clarification",
    }

    with TemporaryDirectory() as directory:
        experience_path = str(Path(directory) / "experience.json")
        agents = [
            SimpleReflexAgent(),
            ModelBasedReflexAgent(),
            GoalBasedAgent(),
            UtilityBasedAgent(),
            LearningAgent(experience_path=experience_path),
            LLMToolCallingAgent(),
        ]

        for scenario in SCENARIOS:
            for agent in agents:
                assert agent.decide(scenario).action == expected[scenario.scenario_id]


def test_learning_agent_updates_experience_history():
    scenario = next(item for item in SCENARIOS if item.scenario_id == "A")
    with TemporaryDirectory() as directory:
        agent = LearningAgent(experience_path=str(Path(directory) / "experience.json"))
        decision = agent.decide(scenario)
        evidence = decision.evidence
        assert evidence["historical_success_counts"]["verify_delivery"] == 1
        assert evidence["scenario_id"] == "A"
        assert "limitation" in evidence


@pytest.mark.parametrize(
    ("module_name", "class_name"),
    [
        ("agents.simle_reflex_agent", "SimpleReflexAgent"),
        ("agents.model_based_reflex_agent", "ModelBasedReflexAgent"),
        ("agents.goal_based_agent", "GoalBasedAgent"),
        ("agents.utility_based_agent", "UtilityBasedAgent"),
        ("agents.learning_agent", "LearningAgent"),
    ],
)
def test_separate_classical_agent_modules(module_name, class_name):
    module = __import__(module_name, fromlist=[class_name])
    assert getattr(module, class_name)
