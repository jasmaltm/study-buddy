"""
Pillar 1: The Core Loop (Think -> Act -> Look)
Pillar 3: Self-Healing & Error Recovery
Orchestrates the autonomous ReAct agent loop for AI Study Buddy.
"""

import re
import json
import traceback
from typing import Dict, Any, Optional, Tuple, List

from agent.tools import TOOL_REGISTRY, ToolResult
from agent.memory import AgentMemory
from agent.planner import ExecutionPlan, generate_heuristic_plan
from agent.safety import SafetyGuard, AuditLogger
from agent.llm.base import BaseLLM


SYSTEM_PROMPT_TEMPLATE = """You are AI Study Buddy, an intelligent educational agent designed to help students learn, solve problems, generate study notes, and master concepts.

{memory_context}

Available Tools:
{tools_description}

You must follow this strict ReAct protocol.

IMPORTANT: Generate ONLY ONE response step per call.

For a tool call, respond exactly like this:

Thought: Briefly explain what you need to do.
Action: tool_name(param1="value")

STOP immediately after the Action line.
Do not write an Observation.
Do not write another Thought.
Do not write a Final Answer in the same response.

The Python program will execute the tool and provide the real Observation.
You must wait for that Observation before deciding what to do next.

When you have enough information to answer, respond exactly like this:

Thought: Briefly explain that you have enough information.
Final Answer: Your clear, friendly educational answer.

CRITICAL RULES:
1. Never invent or fabricate tool results or Observations.
2. Never claim a tool was executed unless Python supplied its Observation.
3. Use only the tools listed above.
4. Make at most one Action per response.
5. If a tool reports an error, use its actual error message to recover.
6. If search_knowledge_base returns NotFoundError, DO NOT search again for the same topic. The topic is missing from the local knowledge base, not necessarily unknown. Answer using your general educational knowledge, and clearly distinguish that answer from local knowledge-base results.
7. After receiving a NotFoundError, your next response should normally be a Final Answer, not another search action.
8. Do not include Action and Final Answer in the same response.
9. Keep explanations suitable for the student's level.
"""

class StudyBuddyAgent:
    """
    Autonomous Study Buddy Agent implementing:
    1. Think -> Act -> Look Loop
    2. 2-4 Clearly Described Tools
    3. Self-healing / Error Recovery on tool failure
    4. Memory across tasks
    5. A plan before it acts
    6. Safety: Asks you first, Step limit, Audit log
    7. Pluggable Fake LLM / Real LLM
    """
    def __init__(
        self,
        llm: BaseLLM,
        memory: Optional[AgentMemory] = None,
        safety: Optional[SafetyGuard] = None,
        logger: Optional[AuditLogger] = None,
        max_steps: int = 8,
        auto_approve_safety: Optional[bool] = None
    ):
        self.llm = llm
        self.memory = memory or AgentMemory()
        self.logger = logger or AuditLogger()
        self.safety = safety or SafetyGuard(max_steps=max_steps, logger=self.logger)
        self.auto_approve_safety = auto_approve_safety
        self.tools = TOOL_REGISTRY

    def _format_tools_description(self) -> str:
        lines = []
        for name, meta in self.tools.items():
            params = ", ".join(f"{k}: {v}" for k, v in meta["parameters"].items())
            confirm_flag = " [REQUIRES HUMAN CONFIRMATION]" if meta["requires_confirmation"] else ""
            lines.append(f"- {name}({params}): {meta['description']}{confirm_flag}")
        return "\n".join(lines)

    def _parse_action(self, text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Parses 'Action: tool_name(arg1="val", arg2=123)' from LLM output.
        Handles nested parentheses within strings and math formulas with 100% precision.
        """
        match = re.search(r"Action:\s*([a-zA-Z0-9_]+)\s*\(", text)
        if not match:
            return None

        tool_name = match.group(1).strip()
        start_idx = match.end()  # position right after the opening '('

        # Find the matching closing parenthesis that balances depth, respecting quotes
        depth = 1
        in_double_quote = False
        in_single_quote = False
        escape = False
        end_idx = -1

        for i in range(start_idx, len(text)):
            ch = text[i]
            if escape:
                escape = False
                continue
            if ch == '\\':
                escape = True
                continue
            if ch == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif ch == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif not in_double_quote and not in_single_quote:
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
                    if depth == 0:
                        end_idx = i
                        break

        if end_idx == -1:
            args_str = text[start_idx:].split("\n")[0].rstrip(")")
        else:
            args_str = text[start_idx:end_idx]

        args = {}
        if not args_str.strip():
            return tool_name, args

        # Safe AST parsing of arguments
        try:
            import ast
            call_tree = ast.parse(f"f({args_str})")
            call_node = call_tree.body[0].value
            for kw in call_node.keywords:
                try:
                    args[kw.arg] = ast.literal_eval(kw.value)
                except Exception:
                    args[kw.arg] = ast.unparse(kw.value) if hasattr(ast, "unparse") else str(kw.value)
            return tool_name, args
        except Exception:
            pass

        # Robust regex fallback
        arg_matches = re.findall(r'([a-zA-Z0-9_]+)\s*=\s*(".*?"|\'.*?\'|\[.*?\]|\{.*?\}|[^,]+)', args_str, re.DOTALL)
        for k, v in arg_matches:
            v = v.strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                args[k] = v[1:-1]
            elif v.isdigit():
                args[k] = int(v)
            elif v.lower() == "true":
                args[k] = True
            elif v.lower() == "false":
                args[k] = False
            elif v.startswith("[") and v.endswith("]"):
                try:
                    args[k] = json.loads(v.replace("'", '"'))
                except Exception:
                    args[k] = [item.strip().strip("'\"") for item in v[1:-1].split(",") if item.strip()]
            else:
                try:
                    args[k] = float(v)
                except ValueError:
                    args[k] = v

        return tool_name, args

    def run(self, task: str) -> Dict[str, Any]:
        """
        Main execution loop for a student task.
        """
        session_log = []
        tools_invoked = []
        
        self.logger.log("START", f"New Student Task received: '{task}'")
        
        # Pillar 5: A Plan Before It Acts
        plan: ExecutionPlan = generate_heuristic_plan(task)
        self.logger.log("PLAN", f"\n{plan.format_plan_display()}")
        session_log.append(f"Plan:\n{plan.format_plan_display()}")

        # Pillar 4: Retrieve persistent memory context
        memory_context = self.memory.get_context_for_prompt(task)

        # Build prompt scratchpad
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            memory_context=memory_context,
            tools_description=self._format_tools_description()
        )
        
        scratchpad = f"{system_prompt}\n\nTask: {task}\n\n{plan.format_plan_display()}\n\n"
        
        current_step = 1
        final_answer = None
        last_tool_action = None

        # Pillar 1: The Core Loop (Think -> Act -> Look)
        while current_step <= self.safety.max_steps:
            self.logger.log("STEP_START", f"Starting loop iteration {current_step}/{self.safety.max_steps}", step=current_step)
            
            # Step safety check
            if not self.safety.check_step_limit(current_step):
                final_answer = f"Execution reached safety step limit of {self.safety.max_steps} steps. Task stopped for student safety."
                break

            # LLM Think / Act generation
            try:
                response = self.llm.generate(scratchpad)
            except Exception as e:
                self.logger.log("LLM_ERROR", f"LLM generation failed: {str(e)}", step=current_step)
                final_answer = f"I encountered an error communicating with the reasoning model: {str(e)}"
                break

            scratchpad += response + "\n"

                       # Reject responses that combine an action and a final answer.
            has_action = self._parse_action(response) is not None
            has_final = "Final Answer:" in response

            if has_action and has_final:
                self.logger.log(
                    "PARSE_WARNING",
                    "LLM returned an Action and Final Answer together. Requesting one response step.",
                    step=current_step
                )
                scratchpad += (
                    "Observation: INVALID RESPONSE. You must provide either "
                    "one Action OR one Final Answer, never both. "
                    "Do not invent tool observations. Try again.\n"
                )
                current_step += 1
                continue

            # Accept a final answer only when no action is present.
            if has_final:
                thought_match = re.search(
                    r"Thought:(.*?)(?=Final Answer:|$)",
                    response,
                    re.DOTALL
                )
                thought_text = (
                    thought_match.group(1).strip()
                    if thought_match else "Synthesizing answer"
                )
                self.logger.log("THINK", thought_text, step=current_step)

                final_answer_match = re.search(
                    r"Final Answer:(.*)",
                    response,
                    re.DOTALL
                )
                final_answer = (
                    final_answer_match.group(1).strip()
                    if final_answer_match else response
                )
                self.logger.log("FINAL_ANSWER", final_answer, step=current_step)
                fallback_used = any(
                    step.status.startswith("FAILED")
                    for step in plan.steps
                )

                if fallback_used:
                    for step_index, step in enumerate(plan.steps):
                        if step.status.startswith("FAILED"):
                            step.status = "FAILED (Fallback used)"
                        elif step_index == len(plan.steps) - 1:
                            step.status = "COMPLETED"
                        elif step.status not in ("COMPLETED", "COMPLETED (Recovered)"):
                            step.status = "SKIPPED (Fallback used)"

                    plan.current_step_index = len(plan.steps)
                else:
                    while plan.current_step_index < len(plan.steps):
                        current = plan.steps[plan.current_step_index]
                        if current.status.startswith("FAILED"):
                            plan.current_step_index += 1
                        else:
                            plan.mark_current_completed()

                current_step += 1
                break

            # Parse Thought and Action
            thought_match = re.search(r"Thought:(.*?)(?=Action:|$)", response, re.DOTALL)
            thought_text = thought_match.group(1).strip() if thought_match else "Analyzing next step"
            self.logger.log("THINK", thought_text, step=current_step)

            action_data = self._parse_action(response)
            if not action_data:
                self.logger.log("PARSE_WARNING", "No explicit Action or Final Answer detected. Prompting LLM to continue.", step=current_step)
                scratchpad += "Observation: Please provide an Action: tool_name(...) or a Final Answer:.\n"
                current_step += 1
                continue

            tool_name, tool_args = action_data

            action_signature = (
                tool_name,
                tuple(sorted((key, repr(value)) for key, value in tool_args.items()))
            )

            if action_signature == last_tool_action:
                self.logger.log(
                    "DUPLICATE_ACTION",
                    f"Skipped repeated action: {tool_name}({tool_args})",
                    step=current_step
                )
                scratchpad += (
                    "Observation: You already executed this exact tool action "
                    "and received its result above. Do not call it again. "
                    "Use the existing Observation to provide your Final Answer, "
                    "or choose a genuinely different action if necessary.\n"
                )
                current_step += 1
                continue

            last_tool_action = action_signature
            self.logger.log("ACT", f"Action requested: {tool_name}({tool_args})", step=current_step)

            # Check if tool exists
            if tool_name not in self.tools:
                # Pillar 3: Tool error feedback loop
                error_msg = f"Tool '{tool_name}' does not exist. Available tools: {list(self.tools.keys())}"
                self.logger.log("ERROR_RECOVERY", error_msg, step=current_step)
                scratchpad += f"Observation: ERROR [UnknownTool]: {error_msg}\n"
                current_step += 1
                continue

            tool_meta = self.tools[tool_name]

            # Pillar 6: Safety - "Asks you first" for sensitive tools
            if tool_meta["requires_confirmation"]:
                self.logger.log("SAFETY_CHECK", f"Tool '{tool_name}' requires human-in-the-loop confirmation.", step=current_step)
                approved = self.safety.request_user_confirmation(
                    tool_name=tool_name,
                    args=tool_args,
                    auto_approve=self.auto_approve_safety
                )
                if not approved:
                    self.logger.log("SAFETY_DENIED", f"User rejected execution of '{tool_name}'.", step=current_step)
                    final_answer = (
                        f"Cancelled: You did not approve the action '{tool_name}'. "
                        "No changes were made."
                    )
                    self.logger.log("FINAL_ANSWER", final_answer, step=current_step)

                    while plan.current_step_index < len(plan.steps):
                        current = plan.steps[plan.current_step_index]
                        if current.status.startswith('FAILED'):
                            plan.current_step_index += 1
                        else:
                            plan.mark_current_completed()

                    current_step += 1
                    break

            # Prevent unrequested quiz generation.
            if tool_name == "generate_quiz":
                task_lower = task.lower()
                quiz_keywords = (
                    "quiz", "quizzes", "mcq", "mcqs",
                    "multiple choice", "practice questions",
                    "test me", "test my knowledge"
                )

                if not any(word in task_lower for word in quiz_keywords):
                    message = (
                        "Quiz generation skipped: the student did not explicitly "
                        "request a quiz or practice questions."
                    )
                    self.logger.log("SAFETY_BLOCK", message, step=current_step)

                    fallback_prompt = (
                        f"You are AI Study Buddy. Answer this student task directly: {task}\n\n"
                        "The local knowledge base did not contain the requested topic. "
                        "Use your general educational knowledge to answer accurately "
                        "in simple, student-friendly language. Do not call tools. "
                        "Do not generate a quiz. Return a clear explanation only."
                    )

                    try:
                        fallback_response = self.llm.generate(fallback_prompt)
                        final_match = re.search(
                            r"Final Answer:\s*(.*)",
                            fallback_response,
                            re.DOTALL
                        )
                        final_answer = (
                            final_match.group(1).strip()
                            if final_match else fallback_response.strip()
                        )
                        self.logger.log(
                            "FINAL_ANSWER",
                            final_answer,
                            step=current_step
                        )
                    except Exception as e:
                        self.logger.log(
                            "LLM_ERROR",
                            f"Explanation fallback failed: {str(e)}",
                            step=current_step
                        )
                        final_answer = (
                            "I couldn't generate the explanation just now. "
                            "Please try asking again."
                        )

                    while plan.current_step_index < len(plan.steps):
                        current = plan.steps[plan.current_step_index]
                        if current.status.startswith('FAILED'):
                            plan.current_step_index += 1
                        else:
                            plan.mark_current_completed()

                    current_step += 1
                    break

            # Count only tools that pass safety checks and are about to execute.
            tools_invoked.append(tool_name)

            # Pillar 1 & 3: LOOK (Execute Tool and Observe result or Catch error)
            try:
                tool_func = tool_meta["func"]
                tool_result: ToolResult = tool_func(**tool_args)
                obs_text = tool_result.to_observation()
                
                # Check if tool itself reported an error for self-correction (Pillar 3)
                if not tool_result.success:
                    self.logger.log("LOOK_TOOL_ERROR", f"Tool returned failure: {obs_text}", step=current_step)
                    if hasattr(plan, "replan_on_error"):
                        plan.replan_on_error(tool_name, tool_result.error or "Tool error")
                    else:
                        plan.mark_current_failed(tool_result.error or "Tool error")
                else:
                    self.logger.log("LOOK", f"Tool output: {obs_text[:140]}...", step=current_step)
                    plan.mark_current_completed()

            except Exception as e:
                # Pillar 3: Catch unexpected exceptions and deliver as structured observation
                obs_text = f"ERROR [ExecutionException]: {str(e)}"
                self.logger.log("LOOK_EXCEPTION", obs_text, step=current_step)
                if hasattr(plan, "replan_on_error"):
                    plan.replan_on_error(tool_name, str(e))
                else:
                    plan.mark_current_failed(str(e))

            scratchpad += f"Observation: {obs_text}\n"

            # Index successfully saved notes in persistent student memory.
            if tool_name == "save_study_notes" and tool_result.success:
                saved_note = tool_result.data
                self.memory.index_study_note(
                    title=saved_note["title"],
                    file_path=saved_note["saved_file"],
                    tags=saved_note["tags"]
                )

            # Finish immediately after a successfully approved note save.
            if tool_name == "save_study_notes" and tool_result.success:
                final_answer = (
                    f"Study note '{tool_args.get('title', 'Untitled')}' "
                    "was saved successfully. "
                    "No further action is needed."
                )
                self.logger.log(
                    "FINAL_ANSWER",
                    final_answer,
                    step=current_step
                )

                while plan.current_step_index < len(plan.steps):
                    current = plan.steps[plan.current_step_index]
                    if current.status.startswith('FAILED'):
                        plan.current_step_index += 1
                    else:
                        plan.mark_current_completed()

                current_step += 1
                break

            current_step += 1

        if not final_answer:
            final_answer = f"Execution reached safety step limit of {self.safety.max_steps} steps. Task stopped for student safety."

        # Pillar 4: Update persistent memory with task completion
        self.memory.record_task_completion(
            task=task,
            summary=final_answer[:150] + ("..." if len(final_answer) > 150 else ""),
            tools_used=tools_invoked
        )
        self.logger.log("FINISHED", f"Task complete. Memory updated. Total steps: {current_step - 1}")

        return {
            "task": task,
            "final_answer": final_answer,
            "total_steps": current_step - 1,
            "tools_used": tools_invoked,
            "plan": plan.to_dict() if hasattr(plan, 'to_dict') else [s.to_dict() for s in plan.steps]
        }

