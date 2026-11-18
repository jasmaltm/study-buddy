"""Token-protected local proxy for exposing Ollama through a secure tunnel."""

from __future__ import annotations

import hmac
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_PROXY_TOKEN = os.environ.get("OLLAMA_PROXY_TOKEN", "")
OLLAMA_PROXY_PORT = int(os.environ.get("OLLAMA_PROXY_PORT", "11435"))
MAX_REQUEST_BYTES = 1_000_000


class OllamaProxyHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: int, message: str):
        body = json.dumps({"error": message}).encode("utf-8")
        self._send(status, body)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/generate":
            self._send_error(404, "Not found.")
            return
        if not OLLAMA_PROXY_TOKEN:
            self._send_error(503, "Ollama proxy token is not configured.")
            return

        scheme, separator, token = self.headers.get("Authorization", "").partition(" ")
        if (
            not separator
            or scheme.lower() != "bearer"
            or not hmac.compare_digest(token, OLLAMA_PROXY_TOKEN)
        ):
            self._send_error(401, "A valid bearer token is required.")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_error(400, "Invalid Content-Length header.")
            return
        if content_length <= 0:
            self._send_error(400, "Request body is empty.")
            return
        if content_length > MAX_REQUEST_BYTES:
            self._send_error(413, "Request body is too large.")
            return

        body = self.rfile.read(content_length)
        if len(body) != content_length:
            self._send_error(400, "Request body was incomplete.")
            return

        request = urllib.request.Request(
            OLLAMA_URL,
            data=body,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                self._send(
                    response.getcode(),
                    response.read(),
                    response.headers.get("Content-Type", "application/json"),
                )
        except urllib.error.HTTPError as error:
            self._send(
                error.code,
                error.read(),
                error.headers.get("Content-Type", "application/json"),
            )
        except urllib.error.URLError as error:
            self._send_error(502, f"Ollama is unavailable: {error.reason}")

    def log_message(self, format_string: str, *args):
        print(f"{self.address_string()} - {format_string % args}")


def main():
    if not OLLAMA_PROXY_TOKEN:
        raise SystemExit("Set OLLAMA_PROXY_TOKEN before starting the proxy.")

    server = ThreadingHTTPServer(("127.0.0.1", OLLAMA_PROXY_PORT), OllamaProxyHandler)
    print(f"Protected Ollama proxy listening on 127.0.0.1:{OLLAMA_PROXY_PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
