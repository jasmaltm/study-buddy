import unittest
from unittest.mock import Mock

from agent.core import StudyBuddyAgent


class TestCorePlanProgress(unittest.TestCase):
    def test_model_failure_marks_active_plan_step_failed(self):
        llm = Mock()
        llm.generate.side_effect = RuntimeError("model unavailable")
        memory = Mock()
        memory.get_context_for_prompt.return_value = ""
        safety = Mock()
        safety.max_steps = 1
        safety.check_step_limit.return_value = True
        logger = Mock()

        result = StudyBuddyAgent(
            llm=llm,
            memory=memory,
            safety=safety,
            logger=logger,
            max_steps=1,
        ).run("Explain photosynthesis")

        self.assertEqual(
            result["plan"]["steps"][0]["status"],
            "FAILED: model unavailable",
        )
        self.assertEqual(result["plan"]["progress"]["percentage"], 0)
        self.assertIn("model unavailable", result["final_answer"])


if __name__ == "__main__":
    unittest.main()
