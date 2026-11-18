import json
import unittest
from io import BytesIO
from unittest.mock import patch

from agent.llm.real_llm import GeminiLLM


class TestGeminiLLM(unittest.TestCase):
    def test_no_candidates_reports_prompt_block_reason(self):
        response_body = json.dumps({
            "promptFeedback": {"blockReason": "SAFETY"},
            "candidates": [],
        }).encode("utf-8")

        with patch(
            "agent.llm.real_llm.urllib.request.urlopen",
            return_value=BytesIO(response_body),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Gemini returned no response candidate \\(prompt blocked: SAFETY\\)",
            ):
                GeminiLLM(api_key="test-key").generate("test prompt")

    def test_returns_text_from_candidate_parts(self):
        response_body = json.dumps({
            "candidates": [{
                "content": {
                    "parts": [{"text": "Thought: "}, {"text": "Final Answer: Hello."}],
                },
            }],
        }).encode("utf-8")

        with patch(
            "agent.llm.real_llm.urllib.request.urlopen",
            return_value=BytesIO(response_body),
        ):
            answer = GeminiLLM(api_key="test-key").generate("test prompt")

        self.assertEqual(answer, "Thought: \nFinal Answer: Hello.")

    def test_candidate_without_text_reports_finish_reason(self):
        response_body = json.dumps({
            "candidates": [{
                "content": {"parts": []},
                "finishReason": "MALFORMED_RESPONSE",
                "finishMessage": "The response could not be decoded.",
            }],
        }).encode("utf-8")

        with patch(
            "agent.llm.real_llm.urllib.request.urlopen",
            return_value=BytesIO(response_body),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Gemini returned a candidate without text "
                "\\(finish reason: MALFORMED_RESPONSE; details: "
                "The response could not be decoded\\.\\)",
            ):
                GeminiLLM(api_key="test-key").generate("test prompt")


if __name__ == "__main__":
    unittest.main()
