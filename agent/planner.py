"""
Pillar 5: A Plan Before It Acts
Pre-action planning, dynamic progress tracking, and runtime replanning for the AI Study Buddy Agent.
"""

import re
from typing import List, Dict, Any, Optional


class PlanStep:
    def __init__(self, step_number: int, description: str, expected_tool: Optional[str] = None):
        self.step_number = step_number
        self.description = description
        self.expected_tool = expected_tool or "none"
        self.status = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED, FAILED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step_number,
            "description": self.description,
            "expected_tool": self.expected_tool,
            "status": self.status
        }


class ExecutionPlan:
    """
    Represents the structured roadmap generated before acting.
    Tracks progress, supports step transitions, and enables dynamic replanning.
    """
    def __init__(self, goal: str, steps: List[PlanStep]):
        self.goal = goal
        self.steps = steps
        self.current_step_index = 0
        if self.steps:
            self.steps[0].status = "IN_PROGRESS"

    def mark_current_completed(self):
        """Marks active step as completed and advances to the next step."""
        if self.current_step_index < len(self.steps):
            current = self.steps[self.current_step_index]

            if current.description.startswith("Self-Correction:"):
                original_index = self.current_step_index - 1
                if original_index >= 0:
                    original = self.steps[original_index]
                    if original.status == "FAILED (Retrying)":
                        original.status = "COMPLETED (Recovered)"

            current.status = "COMPLETED"
            self.current_step_index += 1

            if self.current_step_index < len(self.steps):
                self.steps[self.current_step_index].status = "IN_PROGRESS"

    def mark_current_failed(self, reason: str = ""):
        """Marks current step as failed."""
        if self.current_step_index < len(self.steps):
            self.steps[self.current_step_index].status = f"FAILED: {reason}"

    def replan_on_error(self, failed_tool: str, error_diagnosis: str):
        """
        Task 4.2: Dynamic Replanning
        When a tool fails, dynamically injects a self-healing recovery step
        into the active roadmap without aborting the mission.
        """
        curr_idx = self.current_step_index
        recovery_step_num = curr_idx + 1
        
        recovery_desc = f"Self-Correction: Fix {failed_tool} parameters based on '{error_diagnosis}' and retry"
        recovery_step = PlanStep(recovery_step_num, recovery_desc, expected_tool=failed_tool)
        recovery_step.status = "IN_PROGRESS"

        # Mark previously failed step
        if curr_idx < len(self.steps):
            self.steps[curr_idx].status = f"FAILED (Retrying)"

        # Insert recovery step into sequence
        self.steps.insert(curr_idx + 1, recovery_step)

        # Renumber remaining steps
        for i, step in enumerate(self.steps):
            step.step_number = i + 1

        self.current_step_index = curr_idx + 1

    def get_progress_summary(self) -> Dict[str, Any]:
        total = len(self.steps)
        completed = sum(1 for s in self.steps if s.status == "COMPLETED" or s.status == "COMPLETED (Recovered)")
        resolved = sum(
            1
            for step in self.steps
            if step.status in ("COMPLETED", "COMPLETED (Recovered)")
            or step.status in ("FAILED (Fallback used)", "SKIPPED (Fallback used)")
        )
        pct = round((resolved / total) * 100) if total > 0 else 0
        active_step_desc = self.steps[self.current_step_index].description if self.current_step_index < total else "All steps finished"
        
        return {
            "total_steps": total,
            "completed_steps": completed,
            "resolved_steps": resolved,
            "percentage": pct,
            "current_step_index": self.current_step_index + 1,
            "active_step_description": active_step_desc
        }

    def format_plan_display(self) -> str:
        """Renders formatted ASCII checklist of the plan with real-time indicators."""
        icons = {
            "PENDING": "[ ]",
            "IN_PROGRESS": "[>]",
            "COMPLETED": "[x]"
        }
        lines = [f"Goal: {self.goal}", "Execution Plan:"]
        for s in self.steps:
            icon = icons.get(s.status, "[!]")
            lines.append(f"  {icon} Step {s.step_number}: {s.description} ({s.expected_tool})")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "progress": self.get_progress_summary(),
            "steps": [s.to_dict() for s in self.steps]
        }


def parse_plan_from_text(text: str, goal: str) -> Optional[ExecutionPlan]:
    """
    Parses LLM generated plan format:
    Plan:
    1. ...
    2. ...
    """
    match = re.search(r"Plan:\s*(.*?)(?=\n\n|\nThought:|$)", text, re.DOTALL | re.IGNORECASE)
    if not match:
        return None

    raw_plan = match.group(1).strip()
    step_lines = re.findall(r"(\d+)\.\s*(.*)", raw_plan)
    if not step_lines:
        return None

    steps = []
    for num_str, desc in step_lines:
        num = int(num_str)
        desc_clean = desc.strip()
        # Heuristic for expected tool
        tool = "none"
        if "search" in desc_clean.lower() or "knowledge" in desc_clean.lower():
            tool = "search_knowledge_base"
        elif "calculate" in desc_clean.lower() or "formula" in desc_clean.lower() or "math" in desc_clean.lower():
            tool = "calculate_math_formula"
        elif "quiz" in desc_clean.lower() or "mcq" in desc_clean.lower():
            tool = "generate_quiz"
        elif "save" in desc_clean.lower() or "note" in desc_clean.lower():
            tool = "save_study_notes"
            
        steps.append(PlanStep(num, desc_clean, tool))

    return ExecutionPlan(goal=goal, steps=steps)


def generate_heuristic_plan(task: str) -> ExecutionPlan:
    """
    Task 4.1: Generates an initial structured plan based on the student task.
    Ensures the agent plans before every action.
    """
    lower = task.lower()
    steps = []

    # If math or calculation is involved (e.g. solve, calculate, compute, formula with numbers)
    is_calc_query = (
        any(k in lower for k in ["calculate", "solve", "compute", "falling distance", "eval"]) or
        ("formula" in lower and any(c in lower for c in ["=", "*", "/", "+", "^"])) or
        (any(k in lower for k in ["gravity", "force", "acceleration"]) and any(c in lower for c in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]))
    )
    if is_calc_query:
        steps.append(PlanStep(1, "Retrieve relevant scientific/mathematical formulas and definitions", "search_knowledge_base"))
        steps.append(PlanStep(2, "Compute numerical values using deterministic math evaluator", "calculate_math_formula"))
        if any(w in lower for w in ["note", "save", "record", "cheat sheet"]):
            steps.append(PlanStep(3, "Format study note with explanation and save to storage with user approval", "save_study_notes"))
        else:
            steps.append(PlanStep(3, "Synthesize step-by-step solution and final answer", "none"))

    # If study notes / revision is involved, prioritize this over quiz keywords.
    elif any(k in lower for k in ["note", "notes", "summary", "cheat sheet", "revision"]):
        steps.append(PlanStep(1, "Search and extract comprehensive facts on the subject", "search_knowledge_base"))
        steps.append(PlanStep(2, "Draft structured markdown notes and summary cards", "none"))
        steps.append(PlanStep(3, "Request user confirmation to save the notes file to storage", "save_study_notes"))

    # If quiz generation is involved, match standalone quiz/test keywords.
    elif any(k in lower.split() for k in ["quiz", "quizzes", "test", "tests", "mcq", "mcqs"]) or "practice questions" in lower or "multiple choice" in lower:
        steps.append(PlanStep(1, "Search knowledge base to verify core concepts of the topic", "search_knowledge_base"))
        steps.append(PlanStep(2, "Generate interactive multiple-choice quiz questions", "generate_quiz"))
        steps.append(PlanStep(3, "Present quiz with answer keys and learning explanations", "none"))

    # General explanation
    else:
        steps.append(PlanStep(1, "Query knowledge base for concept explanation and analogies", "search_knowledge_base"))
        steps.append(PlanStep(2, "Check student memory profile to adapt explanation depth", "none"))
        steps.append(PlanStep(3, "Formulate clear, simple explanation with examples", "none"))

    return ExecutionPlan(goal=task, steps=steps)
