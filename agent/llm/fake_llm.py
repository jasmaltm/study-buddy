"""
Pillar 7: Fake LLM First (Deterministic Test Engine)
Simulates an LLM for predictable, zero-cost, offline testing of the agent's
Think-Act-Look loop, error correction, memory, and safety.
"""

from typing import List, Optional
from agent.llm.base import BaseLLM


class FakeLLM(BaseLLM):
    """
    Fake / Mock LLM that returns a pre-configured sequence of responses,
    or dynamically responds based on prompt contents for deterministic tests.
    """
    def __init__(self, scripted_responses: Optional[List[str]] = None):
        self.scripted_responses = scripted_responses or []
        self.call_count = 0
        self.prompt_history: List[str] = []

    def generate(self, prompt: str) -> str:
        self.prompt_history.append(prompt)
        
        # If explicit scripted responses were queued, return them in order
        if self.call_count < len(self.scripted_responses):
            response = self.scripted_responses[self.call_count]
            self.call_count += 1
            return response

        self.call_count += 1
        
        # Only inspect the recent scratchpad turns, not ancient task history injected from memory
        # Scratchpad separator: split by "Task: " to look only at current task and steps
        if "\ntask: " in prompt.lower():
            active_context = prompt.lower().split("\ntask: ")[-1]
        else:
            active_context = prompt.lower()

        # Extract only the observations generated during current session steps
        current_observations = active_context.split("observation:")
        last_observation = current_observations[-1] if len(current_observations) > 1 else ""

        # 1. Math calculation with self-correction (Pillar 3 test)
        if "5^2" in active_context and "invalid operator" not in last_observation and "122.5" not in last_observation:
            return (
                "Thought: I need to calculate the falling distance for 5 seconds using formula (9.8 * 5^2) / 2.\n"
                "Action: calculate_math_formula(expression=\"(9.8 * 5^2) / 2\")"
            )

        if "invalid operator" in last_observation or "syntaxerror" in last_observation:
            return (
                "Thought: I noticed the previous calculation failed because '^' was used for exponentiation instead of '**'. "
                "I will fix the syntax and recalculate using '**'.\n"
                "Action: calculate_math_formula(expression=\"(9.8 * 5**2) / 2\")"
            )

        if "122.5" in last_observation:
            return (
                "Thought: The calculation completed successfully with result 122.5 meters. "
                "Now I have all information to answer the student's question.\n"
                "Final Answer: Using the formula d = 0.5 * g * t^2 with g = 9.8 m/s^2 and t = 5 seconds, "
                "the total distance fallen is 122.5 meters."
            )

        # 2. Photosynthesis flow
        # Step 3: Quiz questions observed -> Provide Final Answer
        if ("questions" in last_observation and "question" in last_observation) or "chlorophyll" in last_observation:
            return (
                "Thought: The quiz questions are generated. Now I will provide a friendly explanation "
                "and ask the student to solve the practice quiz.\n"
                "Final Answer: Photosynthesis is the process by which green plants use sunlight, water, and carbon dioxide "
                "to produce oxygen and energy in the form of glucose.\n\n"
                "Example: A sunflower leaves absorbing sunshine and carbon dioxide to grow tall and produce seeds!\n\n"
                "Quick Practice Quiz:\n"
                "1. What green pigment absorbs sunlight? (A: Hemoglobin, B: Chlorophyll - Correct: B)\n"
                "2. Which gas is absorbed from the air? (A: Oxygen, B: Carbon Dioxide - Correct: B)"
            )

        # Step 2: Knowledge base search observed -> Generate quiz
        if "chloroplasts" in last_observation or "photoautotrophs" in last_observation or "glucose" in last_observation:
            return (
                "Thought: I retrieved the core facts about photosynthesis from the knowledge base. "
                "Now I will generate a 2-question quiz to test the student's understanding.\n"
                "Action: generate_quiz(topic=\"photosynthesis\", num_questions=2, difficulty=\"medium\")"
            )

        # Step 1: Initial query -> Search knowledge base
        if "photosynthesis" in active_context:
            return (
                "Thought: I understand the student's question. I will search the knowledge base for verified information on photosynthesis.\n"
                "Action: search_knowledge_base(query=\"photosynthesis\", subject=\"biology\")"
            )

        if "gravity" in active_context or "falling" in active_context:
            return (
                "Thought: I need to check gravity and acceleration concepts in the knowledge base.\n"
                "Action: search_knowledge_base(query=\"gravity\", subject=\"physics\")"
            )

        # Generic safe completion if unexpected prompt
        if len(current_observations) > 1:
            return (
                "Thought: I have reviewed the observations and have sufficient data to answer the student.\n"
                "Final Answer: I have researched your topic and gathered the key facts from the study database."
            )

        return (
            "Thought: I understand the student's question. I will search the knowledge base for verified information.\n"
            "Action: search_knowledge_base(query=\"photosynthesis\", subject=\"biology\")"
        )

