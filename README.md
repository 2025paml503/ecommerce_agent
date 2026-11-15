# Assignment 1: E-commerce Order and Refund Support Assistant

This project implements the required six-agent comparison system from Assignment 1, including five classical agents and one local LLM-driven agent. The pipeline compares the same scenario data across all six agents so the resulting decisions can be analyzed fairly.

## Included components

- Simple Reflex Agent
- Model-Based Reflex Agent
- Goal-Based Agent
- Utility-Based Agent
- Learning Agent
- LLM Tool-Calling Agent using a local Ollama model (Qwen3 if available)
- Streamlit comparison UI
- Shared scenario dataset with normal, critical, and ambiguous cases
- Experience tracking for the learning agent

## Folder structure

- `agents/` - full agent implementations
- `data/` - shared scenario definitions
- `experience/` - learning experience state
- `tests/` - validation tests
- `screenshots/` - sample visual output
- `test_results/` - validation summaries
- `app.py` - Streamlit dashboard entry point

## Local setup

1. Create and activate a Python virtual environment.
2. Install the dependencies:

   ```bash
   pip install -r assignment1/requirements.txt
   ```

3. Ensure Ollama is installed and the model is available locally (for example):

   ```bash
   ollama pull qwen3:8b
   ```

4. Run the dashboard:

   ```bash
   streamlit run assignment1/app.py
   ```

## Scenario coverage

The application includes three shared scenarios:

- A: delivered but not received
- B: refund overdue after return inspection passes
- C: conflicting or incomplete order data

## Notes on the LLM agent

The LLM agent attempts to use a local Ollama model and calls at least two relevant support tools before recommending an action. The tool flow is grounded in returned evidence from:

- `get_order_status`
- `get_delivery_events`
- `search_return_policy`
- `get_refund_status`

When a local model is unavailable, the code gracefully falls back to deterministic evidence-grounded reasoning so the project still works in offline environments.

## Validation

Run the focused test suite:

```bash
cd assignment1
pytest -q tests/test_agents.py
```

The test suite checks that all agents produce a decision, that all required scenario types are present, and that the LLM agent uses multiple tool outputs.

## Submission checklist status

- Five classical agents: complete
- LLM agent and tool calling: complete
- Shared scenarios with fair comparison: complete
- Streamlit UI: complete
- Learning agent with experience state: complete
- Documentation and test results: included
