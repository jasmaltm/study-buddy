import unittest

from agent.planner import ExecutionPlan, PlanStep


class TestPlanProgress(unittest.TestCase):
    def test_in_progress_recovery_is_not_counted_as_resolved(self):
        plan = ExecutionPlan(
            "Explain a topic",
            [
                PlanStep(1, "Search knowledge base"),
                PlanStep(2, "Recover search"),
                PlanStep(3, "Adapt explanation"),
                PlanStep(4, "Answer"),
            ],
        )
        plan.steps[0].status = "COMPLETED"
        plan.steps[1].status = "FAILED (Retrying)"
        plan.steps[2].status = "IN_PROGRESS"

        progress = plan.get_progress_summary()

        self.assertEqual(progress["completed_steps"], 1)
        self.assertEqual(progress["resolved_steps"], 1)
        self.assertEqual(progress["percentage"], 25)

    def test_fallback_completion_resolves_failed_and_skipped_steps(self):
        plan = ExecutionPlan(
            "Explain a topic",
            [
                PlanStep(1, "Search knowledge base"),
                PlanStep(2, "Recover search"),
                PlanStep(3, "Adapt explanation"),
                PlanStep(4, "Answer"),
            ],
        )
        plan.steps[0].status = "FAILED (Fallback used)"
        plan.steps[1].status = "SKIPPED (Fallback used)"
        plan.steps[2].status = "SKIPPED (Fallback used)"
        plan.steps[3].status = "COMPLETED"

        progress = plan.get_progress_summary()

        self.assertEqual(progress["completed_steps"], 1)
        self.assertEqual(progress["resolved_steps"], 4)
        self.assertEqual(progress["percentage"], 100)


if __name__ == "__main__":
    unittest.main()
