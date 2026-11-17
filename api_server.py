"""Local HTTP server for the AI Study Buddy frontend."""
from __future__ import annotations

import json
import mimetypes
import os
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import config
from agent.core import StudyBuddyAgent
from agent.memory import AgentMemory
from agent.safety import AuditLogger, SafetyGuard
from run_agent import get_llm

ROOT = Path(__file__).resolve().parent
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 8000))

MEMORY = AgentMemory(storage_path=config.MEMORY_FILE_PATH)
LOGGER = AuditLogger(log_file=config.LOG_FILE_PATH)
AGENT_LOCK = threading.Lock()
PENDING_APPROVALS: dict[str, dict] = {}


class ApprovalRequired(Exception):
    def __init__(self, tool_name: str, args: dict):
        super().__init__(f"Approval required for {tool_name}")
        self.tool_name = tool_name
        self.args = args


def run_agent_task(task: str, approved_action: dict | None = None) -> dict:
    def confirmation_callback(tool_name, args):
        if approved_action:
            if (tool_name == approved_action.get("tool_name")
                    and args == approved_action.get("args")):
                return True
        raise ApprovalRequired(tool_name, args)

    safety = SafetyGuard(
        max_steps=config.MAX_STEPS,
        logger=LOGGER,
        confirmation_callback=confirmation_callback,
    )
    agent = StudyBuddyAgent(
        llm=get_llm(),
        memory=MEMORY,
        safety=safety,
        logger=LOGGER,
        max_steps=config.MAX_STEPS,
        auto_approve_safety=None,
    )
    with AGENT_LOCK:
        return agent.run(task)


class Handler(BaseHTTPRequestHandler):
    server_version = "AIStudyBuddy/1.0"

    def _send(self, status: int, data, content_type="application/json; charset=utf-8"):
        body = data if isinstance(data, bytes) else json.dumps(
            data, ensure_ascii=False
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 1_000_000:
                raise ValueError("Request body is empty or too large.")
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Please send valid JSON.") from exc

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            return self._serve_file(ROOT / "index.html")
        if path == "/frontend_integration.js":
            return self._serve_file(ROOT / "frontend_integration.js")
        if path == "/api/health":
            self._send(200, {
                "ok": True,
                "provider": config.REAL_LLM_PROVIDER,
                "fake_llm": bool(config.USE_FAKE_LLM),
                "message": "AI Study Buddy server is running.",
            })
            return
        if path == "/api/memory":
            self._send(200, {"ok": True, "memory": MEMORY.data})
            return
        self._send(404, {"error": "Not found."})

    def _serve_file(self, path: Path):
        if not path.is_file():
            self._send(404, {"error": f"Required file not found: {path.name}"})
            return
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        if path.suffix == ".js":
            content_type = "text/javascript; charset=utf-8"
        self._send(200, path.read_bytes(), content_type)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            if path == "/api/ask":
                self._ask(payload)
            elif path == "/api/approve":
                self._approve(payload)
            else:
                self._send(404, {"error": "Not found."})
        except ValueError as exc:
            self._send(400, {"error": str(exc)})
        except Exception as exc:
            LOGGER.log_event("api_error", {"error": str(exc)})
            self._send(500, {"error": str(exc)})

    def _ask(self, payload):
        task = str(payload.get("task", "")).strip()
        if not task:
            self._send(400, {"error": "Please enter a question or task."})
            return
        try:
            result = run_agent_task(task)
            self._send(200, {"ok": True, "result": result})
        except ApprovalRequired as request:
            request_id = str(uuid.uuid4())
            PENDING_APPROVALS[request_id] = {
                "task": task,
                "tool_name": request.tool_name,
                "args": request.args,
            }
            self._send(202, {
                "ok": True,
                "approval_required": True,
                "request_id": request_id,
                "tool_name": request.tool_name,
                "args": request.args,
                "message": "This action needs your approval.",
            })

    def _approve(self, payload):
        request_id = str(payload.get("request_id", ""))
        approved = payload.get("approved")
        pending = PENDING_APPROVALS.pop(request_id, None)
        if not pending:
            self._send(404, {"error": "This approval request has expired. Please try again."})
            return
        if approved is not True:
            self._send(200, {
                "ok": True,
                "cancelled": True,
                "message": "Action cancelled.",
            })
            return
        try:
            result = run_agent_task(
                pending["task"],
                approved_action={
                    "tool_name": pending["tool_name"],
                    "args": pending["args"],
                },
            )
            self._send(200, {"ok": True, "result": result})
        except ApprovalRequired as request:
            next_id = str(uuid.uuid4())
            PENDING_APPROVALS[next_id] = {
                "task": pending["task"],
                "tool_name": request.tool_name,
                "args": request.args,
            }
            self._send(202, {
                "ok": True,
                "approval_required": True,
                "request_id": next_id,
                "tool_name": request.tool_name,
                "args": request.args,
                "message": "Another action needs your approval.",
            })


if __name__ == "__main__":
    print("=" * 60)
    print("AI STUDY BUDDY — LOCAL WEB SERVER")
    print("=" * 60)
    print(f"Website: http://{HOST}:{PORT}")
    print(f"LLM mode: {'fake' if config.USE_FAKE_LLM else config.REAL_LLM_PROVIDER}")
    print("Press Ctrl+C to stop the server.")
    print("=" * 60)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
