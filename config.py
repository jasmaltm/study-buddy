"""
Configuration file for AI Study Buddy Agent.
Toggle between Fake LLM (for zero-cost offline testing) and real LLM providers.
"""

import os
from urllib.parse import urlsplit

# Set to true to use FakeLLM (zero cost, zero keys, 100% deterministic).
_use_fake_llm = os.environ.get("USE_FAKE_LLM", "false").strip().lower()
if _use_fake_llm not in {"true", "false"}:
    raise ValueError("USE_FAKE_LLM must be 'true' or 'false'.")
USE_FAKE_LLM = _use_fake_llm == "true"

# Real LLM Provider ('gemini', 'openai', or 'ollama')
REAL_LLM_PROVIDER = os.environ.get("REAL_LLM_PROVIDER", "gemini").strip().lower()
if REAL_LLM_PROVIDER not in {"gemini", "openai", "ollama"}:
    raise ValueError("REAL_LLM_PROVIDER must be 'gemini', 'openai', or 'ollama'.")

# API Keys
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OLLAMA_BASE_URL = os.environ.get(
    "OLLAMA_BASE_URL", "http://localhost:11434"
).strip().rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b").strip()
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "")
if not OLLAMA_BASE_URL or not OLLAMA_MODEL:
    raise ValueError("OLLAMA_BASE_URL and OLLAMA_MODEL must not be empty.")
_ollama_url = urlsplit(OLLAMA_BASE_URL)
if _ollama_url.scheme not in {"http", "https"} or not _ollama_url.hostname:
    raise ValueError("OLLAMA_BASE_URL must be an HTTP(S) server URL.")
_ollama_is_local = _ollama_url.hostname.lower() in {"localhost", "127.0.0.1", "::1"}
if REAL_LLM_PROVIDER == "ollama" and os.environ.get("PORT"):
    if _ollama_is_local:
        raise ValueError(
            "Render cannot reach Ollama at localhost. Set OLLAMA_BASE_URL to a remote server."
        )
    if _ollama_url.scheme != "https":
        raise ValueError("Remote OLLAMA_BASE_URL must use HTTPS.")

# Safety Controls
MAX_STEPS = 8
REQUIRE_CONFIRMATION_FOR_SENSITIVE_TOOLS = True

# Storage & Logging Paths
MEMORY_FILE_PATH = "storage/memory.json"
NOTES_STORAGE_DIR = "storage/notes"
LOG_FILE_PATH = "logs/agent_audit.log"

