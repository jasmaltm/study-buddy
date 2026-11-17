"""
Pillar 6: Safety — Asks You First, Step Limit, Audit Logging
Ensures safe, bounded, transparent, and user-confirmed tool execution.
"""

import os
import time
import logging
from typing import Dict, Any, Callable, Optional


class AuditLogger:
    """
    Detailed audit logger writing both to disk (logs/agent_audit.log) and console.
    """
    def __init__(self, log_file: str = "logs/agent_audit.log"):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        
        self.logger = logging.getLogger(f"StudyBuddyAgentAudit_{id(self)}")
        self.logger.setLevel(logging.INFO)
        for h in list(self.logger.handlers):
            try:
                h.close()
            except Exception:
                pass
        self.logger.handlers = []  # Clear existing handlers
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
        self.logger.addHandler(file_handler)

    def log(self, phase: str, message: str, step: int = None):
        step_prefix = f"[Step {step}] " if step is not None else ""
        formatted = f"{step_prefix}[{phase.upper()}] {message}"
        self.logger.info(formatted)
        print(f"  --> {formatted}")


class SafetyGuard:
    """
    Safety manager enforcing step limits and human-in-the-loop (HITL) confirmations.
    """
    def __init__(
        self,
        max_steps: int = 8,
        logger: AuditLogger = None,
        confirmation_callback: Optional[Callable[[str, Dict[str, Any]], bool]] = None
    ):
        self.max_steps = max_steps
        self.logger = logger or AuditLogger()
        self.confirmation_callback = confirmation_callback

    def check_step_limit(self, current_step: int) -> bool:
        """
        Returns True if execution can proceed, False if hard step limit exceeded.
        """
        if current_step > self.max_steps:
            msg = f"Step limit exceeded ({current_step} > {self.max_steps}). Halting loop to prevent infinite execution."
            self.logger.log("SAFETY_LIMIT", msg, step=current_step)
            return False
        return True

    def request_user_confirmation(self, tool_name: str, args: Dict[str, Any], auto_approve: Optional[bool] = None) -> bool:
        """
        Pillar 6: 'Asks you first'
        Prompts human for approval before executing sensitive or persistent operations.
        """
        # If programmatic flag passed (e.g. in test suites)
        if auto_approve is not None:
            status = "APPROVED (auto)" if auto_approve else "DENIED (auto)"
            self.logger.log("SAFETY_GATE", f"Action '{tool_name}' was {status}")
            return auto_approve

        # If custom callback provided
        if self.confirmation_callback:
            approved = self.confirmation_callback(tool_name, args)
            status = "APPROVED" if approved else "DENIED"
            self.logger.log("SAFETY_GATE", f"User confirmation callback for '{tool_name}': {status}")
            return approved

        # Interactive CLI fallback
        print("\n" + "=" * 60)
        print("  [SAFETY ALERT] Human-in-the-Loop Confirmation Required")
        print("=" * 60)
        print(f"  The agent requests permission to execute sensitive tool: '{tool_name}'")
        print("  Proposed Arguments:")
        for k, v in args.items():
            val_str = str(v)
            if len(val_str) > 120:
                val_str = val_str[:117] + "..."
            print(f"    - {k}: {val_str}")
        print("=" * 60)
        
        try:
            choice = input("  Do you authorize this action? [Y/n]: ").strip().lower()
            approved = choice in ["y", "yes", ""]
        except (EOFError, KeyboardInterrupt):
            approved = False

        status = "APPROVED by user" if approved else "DENIED by user"
        self.logger.log("SAFETY_GATE", f"Action '{tool_name}' {status}")
        return approved

