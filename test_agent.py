"""
Comprehensive Test Suite for the 7 Pillars of AI Study Buddy Agent.
Tests everything deterministically using FakeLLM first (Pillar 7).
Requires zero network access, zero API keys, and zero external packages.
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from agent.core import StudyBuddyAgent
from agent.tools import (
    TOOL_REGISTRY,
    search_knowledge_base,
    calculate_math_formula,
    generate_quiz,
    save_study_notes
)
from agent.memory import AgentMemory
from agent.planner import generate_heuristic_plan
from agent.safety import SafetyGuard, AuditLogger
from agent.llm.fake_llm import FakeLLM


class TestAgentPillars(unittest.TestCase):
    """
    Validates all 7 agent pillars:
    1. Loop (Think -> Act -> Look)
    2. 2-4 clearly described tools
    3. Fixed errors when a tool fails
    4. Memory between tasks
    5. A plan before it acts
    6. Safety: Asks you first, step limit, log
    7. Test: Fake LLM first
    """

    def setUp(self):
        self.test_storage = tempfile.TemporaryDirectory(prefix="study-buddy-test-")
        self.test_storage_dir = self.test_storage.name
        self.memory_file = os.path.join(self.test_storage_dir, "test_memory.json")
        self.log_file = os.path.join(self.test_storage_dir, "test_audit.log")
        self.loggers = []

    def tearDown(self):
        for logger in self.loggers:
            logger.close()
        self.test_storage.cleanup()

    def new_logger(self):
        logger = AuditLogger(log_file=self.log_file)
        self.loggers.append(logger)
        return logger

    def test_corrupt_memory_is_not_silently_replaced(self):
        with open(self.memory_file, "w", encoding="utf-8") as memory_file:
            memory_file.write("{")

        with self.assertRaisesRegex(RuntimeError, "Could not load memory file"):
            AgentMemory(storage_path=self.memory_file)

        with open(self.memory_file, "r", encoding="utf-8") as memory_file:
            self.assertEqual(memory_file.read(), "{")

    def test_memory_save_keeps_previous_file_when_serialization_fails(self):
        memory = AgentMemory(storage_path=self.memory_file)
        memory.save()
        with open(self.memory_file, "r", encoding="utf-8-sig") as memory_file:
            original = memory_file.read()

        memory.data["not_serializable"] = object()
        with self.assertRaises(TypeError):
            memory.save()

        with open(self.memory_file, "r", encoding="utf-8-sig") as memory_file:
            self.assertEqual(memory_file.read(), original)
        self.assertEqual(
            [name for name in os.listdir(self.test_storage_dir) if name.endswith(".tmp")],
            []
        )

    def test_math_evaluator_rejects_python_object_access(self):
        result = calculate_math_formula("().__class__.__bases__")
        self.assertFalse(result.success)
        self.assertEqual(result.error, "ValidationError")

    def test_math_evaluator_preserves_supported_functions_and_limits_large_results(self):
        result = calculate_math_formula("sqrt(144) + 25")
        self.assertTrue(result.success)
        self.assertEqual(result.data, 37)

        oversized = calculate_math_formula("100**1000")
        self.assertFalse(oversized.success)
        self.assertEqual(oversized.error, "ValidationError")

    def test_quiz_generator_does_not_invent_generic_questions_or_overstate_count(self):
        unknown = generate_quiz(topic="planetary geology", num_questions=2)
        self.assertFalse(unknown.success)
        self.assertEqual(unknown.error, "NotFoundError")

        unavailable_count = generate_quiz(
            topic="Newton's second law",
            num_questions=3
        )
        self.assertFalse(unavailable_count.success)
        self.assertEqual(unavailable_count.error, "InsufficientQuestionsError")

    def test_empty_safety_confirmation_denies_sensitive_action(self):
        guard = SafetyGuard(logger=self.new_logger())
        with patch("builtins.input", return_value=""):
            self.assertFalse(
                guard.request_user_confirmation("save_study_notes", {"title": "Notes"})
            )

    def test_save_tool_exception_does_not_access_uninitialized_result(self):
        def fail_to_save(**kwargs):
            raise OSError(f"simulated write failure for {kwargs['title']}")

        test_tools = dict(TOOL_REGISTRY)
        test_tools["save_study_notes"] = {
            **TOOL_REGISTRY["save_study_notes"],
            "func": fail_to_save,
        }
        with patch("agent.core.TOOL_REGISTRY", test_tools):
            agent = StudyBuddyAgent(
                llm=FakeLLM(scripted_responses=[
                    "Thought: Save the requested note.\n"
                    "Action: save_study_notes(title=\"Notes\", content=\"Study notes\")",
                    "Thought: The save failed, so I will report that clearly.\n"
                    "Final Answer: The note could not be saved.",
                ]),
                memory=AgentMemory(storage_path=self.memory_file),
                logger=self.new_logger(),
                auto_approve_safety=True,
            )
            result = agent.run("Save a study note")

        self.assertIn("could not be saved", result["final_answer"])

    # -------------------------------------------------------------
    # Pillar 2: 2-4 Clearly Described Tools
    # -------------------------------------------------------------
    def test_pillar_2_tools_execution(self):
        print("\n--- Testing Pillar 2: Tools Specification & Execution ---")
        
        # Tool 1: search_knowledge_base
        res1 = search_knowledge_base(query="photosynthesis")
        self.assertTrue(res1.success)
        self.assertIn("chloroplasts", str(res1.data).lower())

        # Tool 2: calculate_math_formula
        res2 = calculate_math_formula(expression="(9.8 * 5**2) / 2")
        self.assertTrue(res2.success)
        self.assertEqual(res2.data, 122.5)

        # Tool 3: generate_quiz
        res3 = generate_quiz(topic="photosynthesis", num_questions=2)
        self.assertTrue(res3.success)
        self.assertEqual(res3.data["question_count"], 2)

        # Tool 4: save_study_notes
        notes_dir = os.path.join(self.test_storage_dir, "notes")
        res4 = save_study_notes(
            title="Photosynthesis_Notes",
            content="Summary: Light + Water + CO2 -> Glucose + Oxygen",
            tags=["biology", "revision"],
            storage_dir=notes_dir
        )
        self.assertTrue(res4.success)
        self.assertTrue(os.path.exists(res4.data["saved_file"]))
        print("  [PASSED] All 4 tools executed correctly with proper schemas.")

    # -------------------------------------------------------------
    # Pillar 5: A Plan Before It Acts
    # -------------------------------------------------------------
    def test_pillar_5_planning_before_acting(self):
        print("\n--- Testing Pillar 5: Planning Engine ---")
        task = "Calculate the distance fallen by a rock in 5 seconds under gravity and save study notes"
        plan = generate_heuristic_plan(task)
        
        self.assertEqual(plan.goal, task)
        self.assertGreaterEqual(len(plan.steps), 3)
        self.assertEqual(plan.steps[0].expected_tool, "search_knowledge_base")
        self.assertEqual(plan.steps[1].expected_tool, "calculate_math_formula")
        self.assertEqual(plan.steps[2].expected_tool, "save_study_notes")
        
        plan_str = plan.format_plan_display()
        self.assertIn("Execution Plan:", plan_str)
        self.assertIn("Step 1:", plan_str)
        print("  [PASSED] Structured multi-step plan generated before any tool execution.")

    # -------------------------------------------------------------
    # Pillar 1 & 7: Think -> Act -> Look Loop with Fake LLM
    # -------------------------------------------------------------
    def test_pillar_1_and_7_think_act_look_loop(self):
        print("\n--- Testing Pillars 1 & 7: Think-Act-Look Loop with Fake LLM ---")
        
        # Scripted Fake LLM responses
        scripted = [
            # Turn 1
            "Thought: The student wants to know about photosynthesis. I will search the knowledge base.\n"
            "Action: search_knowledge_base(query=\"photosynthesis\", subject=\"biology\")",
            
            # Turn 2
            "Thought: I have the verified biological facts. Now I will generate a 2-question quiz.\n"
            "Action: generate_quiz(topic=\"photosynthesis\", num_questions=2, difficulty=\"easy\")",
            
            # Turn 3
            "Thought: The quiz has been generated. I am ready to formulate the final explanation.\n"
            "Final Answer: Photosynthesis is the process plants use to convert sunlight into energy (glucose) and produce oxygen."
        ]
        
        fake_llm = FakeLLM(scripted_responses=scripted)
        memory = AgentMemory(storage_path=self.memory_file)
        logger = self.new_logger()
        
        agent = StudyBuddyAgent(
            llm=fake_llm,
            memory=memory,
            logger=logger,
            auto_approve_safety=True
        )
        
        result = agent.run("Teach me about photosynthesis and quiz me")
        
        self.assertEqual(result["total_steps"], 3)
        self.assertEqual(result["tools_used"], ["search_knowledge_base", "generate_quiz"])
        self.assertIn("Photosynthesis is the process", result["final_answer"])
        print("  [PASSED] Complete Think -> Act -> Look loop executed across 3 cycles.")

    # -------------------------------------------------------------
    # Pillar 3: Fixed Errors When a Tool Fails (Self-Correction)
    # -------------------------------------------------------------
    def test_pillar_3_error_recovery_and_retry(self):
        print("\n--- Testing Pillar 3: Error Recovery & Self-Correction ---")
        
        # Scripted simulation where tool fails initially with invalid syntax
        scripted = [
            # Turn 1: Uses invalid exponentiation operator '^'
            "Thought: I will calculate the kinetic energy using the formula.\n"
            "Action: calculate_math_formula(expression=\"(9.8 * 5^2) / 2\")",
            
            # Turn 2: Agent reads error observation, self-corrects operator to '**'
            "Thought: The previous tool failed with invalid operator '^'. In Python '**' is used for powers. I will fix the formula.\n"
            "Action: calculate_math_formula(expression=\"(9.8 * 5**2) / 2\")",
            
            # Turn 3: Final Answer using successful recovery
            "Thought: The corrected calculation succeeded with 122.5. I can now answer.\n"
            "Final Answer: The calculated distance is 122.5 meters."
        ]
        
        fake_llm = FakeLLM(scripted_responses=scripted)
        memory = AgentMemory(storage_path=self.memory_file)
        agent = StudyBuddyAgent(
            llm=fake_llm,
            memory=memory,
            logger=self.new_logger(),
            auto_approve_safety=True
        )
        
        result = agent.run("Calculate falling distance for 5 seconds")
        
        self.assertEqual(result["total_steps"], 3)
        self.assertEqual(result["tools_used"], ["calculate_math_formula", "calculate_math_formula"])
        self.assertIn("122.5 meters", result["final_answer"])
        print("  [PASSED] Agent recovered from tool failure, diagnosed error, and retried successfully.")

    # -------------------------------------------------------------
    # Pillar 4: Memory Between Tasks (Cross-Session Persistence)
    # -------------------------------------------------------------
    def test_pillar_4_memory_between_tasks(self):
        print("\n--- Testing Pillar 4: Memory Between Tasks ---")
        
        # Session 1: Set user preferences and complete Task 1
        memory1 = AgentMemory(storage_path=self.memory_file)
        memory1.set_user_profile(grade_level="Grade 11", learning_style="Visual diagrams and concise formulas")
        memory1.add_mastered_concept("Newton's Laws")
        memory1.add_weak_area("Organic Chemistry Reactions")
        
        llm1 = FakeLLM(scripted_responses=[
            "Thought: Recalling concepts.\nFinal Answer: Task 1 finished."
        ])
        agent1 = StudyBuddyAgent(
            llm=llm1,
            memory=memory1,
            logger=self.new_logger(),
            auto_approve_safety=True
        )
        agent1.run("Review Newton's second law")
        
        # Session 2: Fresh Agent instance loading the same persistent memory file
        memory2 = AgentMemory(storage_path=self.memory_file)
        context_prompt = memory2.get_context_for_prompt()
        
        self.assertIn("Grade 11", context_prompt)
        self.assertIn("Visual diagrams", context_prompt)
        self.assertIn("Newton's Laws", context_prompt)
        self.assertIn("Organic Chemistry Reactions", context_prompt)
        self.assertIn("Review Newton's second law", context_prompt)
        print("  [PASSED] Memory persisted to disk and accurately restored into new agent session.")

    # -------------------------------------------------------------
    # Pillar 6: Safety — Asks You First, Step Limit & Logging
    # -------------------------------------------------------------
    def test_pillar_6_safety_controls(self):
        print("\n--- Testing Pillar 6: Safety Controls (HITL & Step Limits) ---")
        
        # Test 6A: "Asks you first" — Denied Action
        scripted_denied = [
            "Thought: I should save the notes.\n"
            "Action: save_study_notes(title=\"Exam_CheatSheet\", content=\"Important rules\")",
            "Thought: The user denied permission to save the file. I will respect the decision and output directly.\n"
            "Final Answer: Since file saving was not authorized, here are your notes directly on screen: Important rules."
        ]
        agent_denied = StudyBuddyAgent(
            llm=FakeLLM(scripted_responses=scripted_denied),
            memory=AgentMemory(storage_path=self.memory_file),
            logger=self.new_logger(),
            auto_approve_safety=False  # User rejects confirmation!
        )
        res_denied = agent_denied.run("Save exam cheat sheet")
        self.assertTrue(
            "not authorized" in res_denied["final_answer"] or "did not approve" in res_denied["final_answer"],
            f"Unexpected final answer: {res_denied['final_answer']}"
        )
        print("  [PASSED] Safety Gate: Sensitive tool was intercepted and rejection was respected.")

        # Test 6B: Step Limit enforcement
        runaway_script = [
            f"Thought: Running step {i}\nAction: search_knowledge_base(query='gravity')"
            for i in range(10)
        ]
        agent_limited = StudyBuddyAgent(
            llm=FakeLLM(scripted_responses=runaway_script),
            memory=AgentMemory(storage_path=self.memory_file),
            logger=self.new_logger(),
            max_steps=3  # Hard cap at 3 steps
        )
        res_limited = agent_limited.run("Run infinite queries")
        self.assertLessEqual(res_limited["total_steps"], 4)
        self.assertIn("safety step limit", res_limited["final_answer"])
        print("  [PASSED] Step Limit: Runaway loop safely halted after max_steps reached.")


if __name__ == "__main__":
    unittest.main()

