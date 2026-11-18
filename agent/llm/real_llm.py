"""
Pillar 7: ...Then a Real One (Live LLM Adapter)
Supports Google Gemini API and OpenAI API using standard library or SDK.
Provides zero-dependency HTTP fallback so it runs without extra package installations.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Optional
from agent.llm.base import BaseLLM


class GeminiLLM(BaseLLM):
    """
    Real LLM adapter using Google Gemini API.
    Can use google-genai SDK if installed, or standard REST API via urllib.
    """
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3.5-flash-lite"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found! Please set GEMINI_API_KEY in your environment, "
                "or run with FakeLLM for zero-cost offline testing."
            )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if not candidates:
                    block_reason = (result.get("promptFeedback") or {}).get("blockReason")
                    reason = f" (prompt blocked: {block_reason})" if block_reason else ""
                    raise RuntimeError(f"Gemini returned no response candidate{reason}.")

                candidate = candidates[0]
                parts = (candidate.get("content") or {}).get("parts", [])
                text = "\n".join(
                    part["text"]
                    for part in parts
                    if isinstance(part.get("text"), str)
                ).strip()
                if not text:
                    finish_reason = candidate.get("finishReason")
                    reason = f" (finish reason: {finish_reason})" if finish_reason else ""
                    raise RuntimeError(f"Gemini returned a candidate without text{reason}.")
                return text
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"Gemini API HTTP Error {e.code}: {error_body}")
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Gemini API Request failed: {str(e)}")


class OpenAILLM(BaseLLM):
    """
    Real LLM adapter using OpenAI API compatible endpoints.
    """
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini", base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found! Please set OPENAI_API_KEY in your environment, "
                "or run with FakeLLM for offline testing."
            )

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"OpenAI API HTTP Error {e.code}: {error_body}")
        except Exception as e:
            raise RuntimeError(f"OpenAI API Request failed: {str(e)}")



class OllamaLLM(BaseLLM):
    """
    Local LLM adapter using Ollama.
    No API key or cloud connection required.
    """

    def __init__(self, model: str = "llama3.2:3b",
                 base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "").strip()

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Ollama HTTP Error {e.code}: {error_body}"
            )

        except Exception as e:
            raise RuntimeError(
                f"Ollama request failed: {str(e)}"
            )