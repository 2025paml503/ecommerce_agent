from __future__ import annotations

import os
from typing import Dict, List

import pandas as pd
import streamlit as st

try:
    from assignment1.agents.base import AgentDecision, Scenario
    from assignment1.agents.classical_agents import (
        GoalBasedAgent,
        LearningAgent,
        ModelBasedReflexAgent,
        SimpleReflexAgent,
        UtilityBasedAgent,
    )
    from assignment1.agents.llm_agent import LLMToolCallingAgent
    from assignment1.data.scenarios import SCENARIOS
except ModuleNotFoundError:  # pragma: no cover - script execution fallback
    from agents.base import AgentDecision, Scenario
    from agents.classical_agents import (
        GoalBasedAgent,
        LearningAgent,
        ModelBasedReflexAgent,
        SimpleReflexAgent,
        UtilityBasedAgent,
    )
    from agents.llm_agent import LLMToolCallingAgent
    from data.scenarios import SCENARIOS


st.set_page_config(
    page_title="E-commerce Support Agent Comparator",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] .main .block-container {
        max-width: 1280px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }
    [data-testid="stAppViewContainer"] h1 {
        font-size: clamp(1.8rem, 3vw, 2.55rem);
        line-height: 1.15;
        overflow-wrap: anywhere;
    }
    [data-testid="stAppViewContainer"] h2 {
        font-size: 1.55rem;
    }
    [data-testid="stAppViewContainer"] h3 {
        font-size: 1.1rem;
    }
    [data-testid="stMetric"] {
        padding: 0.8rem 1rem;
        border: 1px solid rgba(128, 128, 128, 0.22);
        border-radius: 0.75rem;
        background: rgba(128, 128, 128, 0.04);
    }
    [data-testid="stMetricLabel"] p {
        font-size: 0.85rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.05rem;
        line-height: 1.25;
        white-space: normal;
        overflow-wrap: anywhere;
    }
    @media (max-width: 700px) {
        [data-testid="stAppViewContainer"] .main .block-container {
            padding: 1rem 1rem 2rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

AGENTS = [
    SimpleReflexAgent(),
    ModelBasedReflexAgent(),
    GoalBasedAgent(),
    UtilityBasedAgent(),
    LearningAgent(),
]
LLM_AGENT = LLMToolCallingAgent()
MECHANISMS = {
    "Simple Reflex Agent": "Condition-action rules",
    "Model-Based Reflex Agent": "Internal state model",
    "Goal-Based Agent": "Goal selection",
    "Utility-Based Agent": "Expected-utility scoring",
    "Learning Agent": "Experience-based adaptation",
    "LLM Tool-Calling Agent": "Local Ollama + evidence tools",
}
AGENT_LABELS = {
    "Simple Reflex Agent": "Simple Reflex",
    "Model-Based Reflex Agent": "Model-Based Reflex",
    "Goal-Based Agent": "Goal-Based",
    "Utility-Based Agent": "Utility-Based",
    "Learning Agent": "Learning Agent",
    "LLM Tool-Calling Agent": "LLM Tool-Calling",
}
ACTION_LABELS = {
    "verify_delivery": "Verify delivery evidence",
    "escalate_refund": "Escalate overdue refund",
    "request_clarification": "Clarify conflicting records",
    "review_records": "Review operational records",
}
SCENARIO_TYPES = {
    "A": "NORMAL CASE",
    "B": "CRITICAL / FAILURE",
    "C": "EDGE / AMBIGUOUS",
}


def get_classical_decisions(scenario: Scenario) -> List[AgentDecision]:
    return [agent.decide(scenario) for agent in AGENTS]


def decision_row(decision: AgentDecision) -> Dict[str, object]:
    return {
        "Agent": AGENT_LABELS.get(decision.agent_name, decision.agent_name),
        "Recommended action": ACTION_LABELS.get(decision.action, decision.recommendation),
    }


st.title("E-commerce Order & Refund Support")
st.caption("Compare five classical agents and a local Ollama agent on simulated support cases.")
st.info("Simulation only. This assistant investigates records and recommends next steps; it never changes orders or issues refunds.")

with st.sidebar:
    model_name = os.getenv("OLLAMA_MODEL", "qwen3:latest")
    st.header("LLM configuration")
    st.caption(f"LLM model: `{model_name}`")
    st.caption("The LLM runs only when requested. Classical recommendations are shown immediately.")

selected_scenario = st.selectbox(
    "Choose a scenario",
    SCENARIOS,
    format_func=lambda item: f"{item.scenario_id} · {item.title}",
    key="selected_scenario",
)

scenario = selected_scenario
st.subheader(f"Scenario {scenario.scenario_id} · {scenario.title}")
st.caption(SCENARIO_TYPES.get(scenario.scenario_id, "SUPPORT CASE"))

with st.container(border=True):
    st.markdown("#### Order snapshot")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Order status", scenario.order_status)
    metric_cols[1].metric("Delivery / return", scenario.delivery_status)
    metric_cols[2].metric("Refund status", scenario.refund_status)
    metric_cols[3].metric("Inspection", scenario.inspection_status)
    details_col, category_col = st.columns([3, 1])
    with details_col:
        st.caption(f"Order ID: **{scenario.order_id}**")
    with category_col:
        st.caption(f"Item: **{scenario.item_category}**")

message_col, policy_col = st.columns(2)
with message_col, st.container(border=True):
    st.markdown("#### Customer message")
    st.write(scenario.customer_message)
with policy_col, st.container(border=True):
    st.markdown("#### Applicable policy")
    st.write(scenario.policy)

classical_results_by_scenario = st.session_state.setdefault("classical_decisions", {})
if scenario.scenario_id not in classical_results_by_scenario:
    classical_results_by_scenario[scenario.scenario_id] = get_classical_decisions(scenario)
classical_results: List[AgentDecision] = classical_results_by_scenario[scenario.scenario_id]

st.divider()
st.subheader("Agent comparison")
llm_results_by_scenario = st.session_state.setdefault("llm_decisions", {})
llm_result = llm_results_by_scenario.get(scenario.scenario_id)
comparison_results = classical_results + ([llm_result] if llm_result else [])
comparison = pd.DataFrame([decision_row(result) for result in comparison_results])
st.table(comparison)

actions = [result.action for result in comparison_results if result.action]
if actions:
    action_counts = pd.Series(actions).value_counts()
    majority_action = str(action_counts.index[0])
    majority_label = ACTION_LABELS.get(majority_action, majority_action)
    st.success(
        f"Most common recommendation: **{majority_label}** "
        f"({int(action_counts.iloc[0])} of {len(comparison_results)} agents so far)."
    )
if llm_result is None:
    st.caption("The table currently shows the five classical agents. Run the local LLM below to add its result to this comparison.")

st.subheader("Classical agent reasoning")
for start in range(0, len(classical_results), 2):
    agent_cols = st.columns(2)
    for column, result in zip(agent_cols, classical_results[start:start + 2]):
        with column, st.container(border=True):
            st.markdown(f"#### {result.agent_name}")
            st.caption(MECHANISMS[result.agent_name])
            st.markdown(f"**Recommendation**  \n{result.recommendation}")
            st.progress(result.confidence, text=f"Confidence: {result.confidence:.0%}")
            st.write(result.reasoning)
            with st.expander("Evidence and internal state"):
                st.json(result.evidence)

st.divider()
st.subheader("Local LLM recommendation")
st.write(
    "Ask Ollama to inspect the support tools and return a recommendation grounded in their evidence. "
    "The request can take longer on the model's first run."
)
if st.button("Run LLM recommendation", type="primary", key=f"run_llm_{scenario.scenario_id}"):
    with st.spinner("Querying local Ollama and support tools…"):
        llm_results_by_scenario[scenario.scenario_id] = LLM_AGENT.decide(scenario)
    st.rerun()

llm_result = llm_results_by_scenario.get(scenario.scenario_id)
if llm_result:
    with st.container(border=True):
        st.markdown(f"#### {llm_result.agent_name}")
        st.caption(MECHANISMS[llm_result.agent_name])
        st.markdown(f"**Recommendation**  \n{llm_result.recommendation}")
        st.progress(llm_result.confidence, text=f"Confidence: {llm_result.confidence:.0%}")
        st.write(llm_result.reasoning)
        with st.expander("Tool calls and evidence", expanded=True):
            st.json(llm_result.evidence)

st.divider()
st.subheader("Why agent decisions can differ")
st.write(
    "The reflex agents respond to recognized patterns or inferred state. The goal-based agent prioritizes "
    "a desired outcome, while the utility-based agent ranks trade-offs. The learning agent also considers "
    "local outcome history. The LLM recommendation is generated separately from the same selected scenario "
    "and should cite evidence returned by its support tools."
)
