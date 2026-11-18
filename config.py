"""
Configuration file for AI Study Buddy Agent.
Toggle between Fake LLM (for zero-cost offline testing) and real LLM providers.
"""

import os

# Set to true to use FakeLLM (zero cost, zero keys, 100% deterministic).
_use_fake_llm = os.environ.get("USE_FAKE_LLM", "false").strip().lower()
if _use_fake_llm not in {"true", "false"}:
    raise ValueError("USE_FAKE_LLM must be 'true' or 'false'.")
USE_FAKE_LLM = _use_fake_llm == "true"

# Real LLM Provider ('ollama', 'gemini', or 'openai')
REAL_LLM_PROVIDER = os.environ.get("REAL_LLM_PROVIDER", "ollama").strip().lower()
if REAL_LLM_PROVIDER not in {"gemini", "openai", "ollama"}:
    raise ValueError("REAL_LLM_PROVIDER must be 'gemini', 'openai', or 'ollama'.")

# API Keys
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Safety Controls
MAX_STEPS = 8
REQUIRE_CONFIRMATION_FOR_SENSITIVE_TOOLS = True

# Storage & Logging Paths
MEMORY_FILE_PATH = "storage/memory.json"
NOTES_STORAGE_DIR = "storage/notes"
LOG_FILE_PATH = "logs/agent_audit.log"

