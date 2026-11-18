import os
import subprocess
import sys
import unittest


class TestConfigurationEnvironment(unittest.TestCase):
    def run_config(self, **environment):
        env = os.environ.copy()
        env.pop("PORT", None)
        env.update(environment)
        return subprocess.run(
            [
                sys.executable,
                "-c",
                "import config; print(config.USE_FAKE_LLM, config.REAL_LLM_PROVIDER)",
            ],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def test_reads_render_model_settings(self):
        result = self.run_config(
            USE_FAKE_LLM="false",
            REAL_LLM_PROVIDER="gemini",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "False gemini")

    def test_defaults_to_gemini(self):
        env = os.environ.copy()
        env.pop("REAL_LLM_PROVIDER", None)
        env["USE_FAKE_LLM"] = "false"
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import config; print(config.USE_FAKE_LLM, config.REAL_LLM_PROVIDER)",
            ],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "False gemini")

    def test_rejects_invalid_fake_llm_setting(self):
        result = self.run_config(USE_FAKE_LLM="sometimes")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("USE_FAKE_LLM must be", result.stderr)

    def test_rejects_invalid_provider(self):
        result = self.run_config(REAL_LLM_PROVIDER="unknown")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("REAL_LLM_PROVIDER must be", result.stderr)

    def test_rejects_loopback_ollama_url_on_hosted_service(self):
        result = self.run_config(
            REAL_LLM_PROVIDER="ollama",
            PORT="10000",
            OLLAMA_BASE_URL="http://127.0.0.1:8000",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Render cannot reach Ollama at localhost", result.stderr)

    def test_accepts_secure_remote_ollama_settings(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import config; print(config.OLLAMA_BASE_URL, config.OLLAMA_MODEL)",
            ],
            capture_output=True,
            text=True,
            env={
                **os.environ,
                "PORT": "10000",
                "REAL_LLM_PROVIDER": "ollama",
                "OLLAMA_BASE_URL": "https://ollama.example.com/",
                "OLLAMA_MODEL": "llama3.2:3b",
            },
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            "https://ollama.example.com llama3.2:3b",
        )


if __name__ == "__main__":
    unittest.main()
