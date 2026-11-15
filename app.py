from __future__ import annotations

import pandas as pd
import streamlit as st

try:
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
    from agents.classical_agents import (
        GoalBasedAgent,
        LearningAgent,
        ModelBasedReflexAgent,
        SimpleReflexAgent,
        UtilityBasedAgent,
    )
    from agents.llm_agent import LLMToolCallingAgent
    from data.scenarios import SCENARIOS


AGENTS = [
    SimpleReflexAgent(),
    ModelBasedReflexAgent(),
    GoalBasedAgent(),
    UtilityBasedAgent(),
    LearningAgent(),
    LLMToolCallingAgent(),
]


def get_decisions_for_scenario(scenario):
    return [agent.decide(scenario) for agent in AGENTS]


st.set_page_config(page_title="Support Agent Comparison", layout="wide")
st.title("E-commerce Order and Refund Support Assistant")

scenario = st.selectbox("Select scenario", [s.title for s in SCENARIOS], index=0)
selected = next(item for item in SCENARIOS if item.title == scenario)

st.subheader(f"Scenario: {selected.title} ({selected.scenario_id})")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Order details**")
    st.write({
        "Order ID": selected.order_id,
        "Order status": selected.order_status,
        "Delivery status": selected.delivery_status,
        "Refund status": selected.refund_status,
        "Inspection status": selected.inspection_status,
        "Item category": selected.item_category,
    })
with col2:
    st.markdown("**Customer message**")
    st.write(selected.customer_message)
    st.markdown("**Policy**")
    st.write(selected.policy)

results = get_decisions_for_scenario(selected)
rows = []
for result in results:
    rows.append({
        "Agent": result.agent_name,
        "Recommendation": result.recommendation,
        "Action": result.action,
        "Confidence": round(result.confidence, 2),
    })

comparison = pd.DataFrame(rows)
st.dataframe(comparison, use_container_width=True)

for result in results:
    st.markdown(f"### {result.agent_name}")
    st.write(f"**Recommendation:** {result.recommendation}")
    st.write(f"**Confidence:** {result.confidence:.2f}")
    st.write(f"**Reasoning:** {result.reasoning}")
    if result.evidence:
        with st.expander("Evidence"):
            st.json(result.evidence)

st.caption("All six agents receive the same scenario input to allow fair comparison between reflex-based, goal-based, utility-based, learning, and LLM-guided reasoning.")
