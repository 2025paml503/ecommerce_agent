# E-commerce Order and Refund Support Assistant

This Streamlit application compares six support decision agents on three simulated e-commerce scenarios:

1. Delivered but not received
2. Refund overdue after return inspection
3. Conflicting or incomplete order records

It implements five classical agents and one local LLM agent. It never issues a refund or changes an order.

## Implemented agents

- Simple Reflex Agent: matches direct scenario patterns.
- Model-Based Reflex Agent: maintains an inferred internal delivery/refund/data-state model.
- Goal-Based Agent: selects the action that best satisfies the highest-priority goal.
- Utility-Based Agent: compares candidate actions using utility scores.
- Learning Agent: updates success/failure counts and scenario history in `experience/experience.json`.
- LLM Tool-Calling Agent: uses local Ollama/LangChain and calls order, delivery, policy, and refund tools.

## Setup

Python 3.10 or newer is recommended.

```bash
cd ecommerce_agent
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Install and start Ollama, then download the default local model:

```bash
ollama pull qwen3
ollama serve
```

## Run

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit, select Scenario A, B, or C, and compare the agent recommendations.

## Tests

```bash
python -m pytest -q tests/test_agents.py
```

The test suite validates scenario coverage, all six agent outputs, the required action for each scenario, LLM tool evidence, and learning history updates.

## Tool evidence

The LLM agent provides four relevant tool functions:

- `get_order_status`
- `get_delivery_events`
- `search_return_policy`
- `get_refund_status`

It requests at least two tool calls from the local Ollama model and executes recognized model tool calls against the selected scenario. It always exposes locally collected evidence, including when Ollama is unavailable, so the UI remains usable.

## Learning and limitations

The learning agent combines scenario patterns with local success/failure counts. Its history is simulated and is not real operational evidence. Confidence values are heuristic, and the Ollama fallback is a deterministic evidence-based recommendation rather than proof of model tool execution.

## Repository contents

- `agents/`: agent implementations
- `data/scenarios.py`: required A, B, and C scenarios
- `experience/`: learning-history data
- `screenshots/`: assignment demonstration captures
- `test_results/`: scenario and pytest outputs
- `tests/test_agents.py`: automated validation
