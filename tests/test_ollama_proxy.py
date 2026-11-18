import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import MagicMock, patch

from ollama_proxy import OllamaProxyHandler


class TestOllamaProxy(unittest.TestCase):
    def setUp(self):
        self.token_patch = patch("ollama_proxy.OLLAMA_PROXY_TOKEN", "test-token")
        self.token_patch.start()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), OllamaProxyHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.token_patch.stop()

    def post(self, path="/api/generate", token=None, body=b'{"prompt":"test"}'):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        connection.request("POST", path, body=body, headers=headers)
        response = connection.getresponse()
        result = response.status, response.read()
        connection.close()
        return result

    def test_requires_bearer_token(self):
        with patch("ollama_proxy.urllib.request.urlopen") as urlopen:
            status, body = self.post()

        self.assertEqual(status, 401)
        self.assertEqual(json.loads(body), {"error": "A valid bearer token is required."})
        urlopen.assert_not_called()

    def test_forwards_authorized_generation_to_local_ollama(self):
        upstream = MagicMock()
        upstream.__enter__.return_value = upstream
        upstream.__exit__.return_value = False
        upstream.getcode.return_value = 200
        upstream.read.return_value = b'{"response":"ok"}'
        upstream.headers.get.return_value = "application/json"

        with patch(
            "ollama_proxy.urllib.request.urlopen",
            return_value=upstream,
        ) as urlopen:
            status, body = self.post(token="test-token")

        request = urlopen.call_args.args[0]
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"response": "ok"})
        self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/generate")
        self.assertEqual(json.loads(request.data), {"prompt": "test"})

    def test_rejects_other_paths(self):
        with patch("ollama_proxy.urllib.request.urlopen") as urlopen:
            status, body = self.post(path="/api/tags", token="test-token")

        self.assertEqual(status, 404)
        self.assertEqual(json.loads(body), {"error": "Not found."})
        urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
