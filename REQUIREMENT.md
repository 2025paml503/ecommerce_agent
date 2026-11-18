Instructions

·        Implement five separate Python agents: Simple Reflex, Model-Based Reflex, Goal-Based, Utility-Based, and Learning Agent.

·        Implement one LLM-based agent using a local Ollama model (for example, Qwen3) with tool calling.

·        All six agents must receive the same selected scenario data so their decisions can be compared fairly.

·        Include at least three test scenarios: normal, critical/failure, and edge or ambiguous case.

·        Build a Streamlit UI to select a scenario and display each agent's decision, reasoning, and comparison.

·        The LLM must call at least two relevant tools and ground its recommendation in returned evidence.

·        The Learning Agent must use or update experience data, such as success/failure counts, and explain how it affects its decision.

·        Submit source code, requirements.txt, README, screenshots, test results.
Submission checklist

·        Python source for all five classical agents and the LLM agent.

·        requirements.txt, README, Streamlit UI, and setup/run instructions.

·        Three scenario test results and screenshots.

·        Comparison table and explanation of why decisions differ.

 
E-commerce Order and Refund Support Assistant

Problem statement: Develop a support assistant that investigates simulated order, delivery, return, and refund records. It should identify the current order status, check the applicable policy, and recommend the next support action without issuing real refunds or changing customer orders.

Required scenarios:

·        A: An order is marked delivered, but the customer reports that the package was not received.

·        B: A returned item has passed inspection, but the refund status has not changed within the expected time.

·        C: The order record and customer message contain conflicting or incomplete information.

Suggested LLM tools: get_order_status(), get_delivery_events(), search_return_policy(), get_refund_status()

 

Criterion
	

Assessment standard
	

Marks

Five classical agents
	

Separate, correct implementations using each intended decision mechanism.
	

5

LLM agent and tool calling
	

Local Ollama model through LangChain; at least two relevant tools called and evidence used.
	

4

Shared scenarios and testing
	

At least three test scenarios; all six agents receive the same input; edge case handled.
	

3

Streamlit UI and comparison
	

Usable UI; decisions and reasons displayed; clear comparison across agents.
	

3

Learning and evaluation
	

Learning agent uses/updates outcome history; evidence is checked; limitations acknowledged.
	

3

Documentation and demonstration
	

README, setup instructions, screenshots, organized code, and clear explanation.
	

2