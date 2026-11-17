import os
import subprocess
import sys
import unittest


class TestConfigurationEnvironment(unittest.TestCase):
    def run_config(self, **environment):
        env = os.environ.copy()
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

    def test_rejects_invalid_fake_llm_setting(self):
        result = self.run_config(USE_FAKE_LLM="sometimes")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("USE_FAKE_LLM must be", result.stderr)

    def test_rejects_invalid_provider(self):
        result = self.run_config(REAL_LLM_PROVIDER="unknown")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("REAL_LLM_PROVIDER must be", result.stderr)


if __name__ == "__main__":
    unittest.main()
