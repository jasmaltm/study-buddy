# study-buddy

## Run locally

Install dependencies and start the web server:

```powershell
python -m pip install -r requirements.txt
$env:USE_FAKE_LLM = "false"
$env:REAL_LLM_PROVIDER = "ollama"
.\start_ui.ps1
```

Make sure Ollama is running and has the configured model installed. By default,
the app connects to `http://localhost:11434` using `llama3.2:3b`. Set
`OLLAMA_BASE_URL` and `OLLAMA_MODEL` to use different values. The launcher
starts the API server and opens `http://127.0.0.1:8000`. For Gemini, set
`$env:REAL_LLM_PROVIDER = "gemini"`; the launcher will prompt for a key. For
offline demo mode, set `$env:USE_FAKE_LLM = "true"` instead.

## Deploy on Render

Create a Python web service connected to this repository and configure:

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `python api_server.py`
- **Environment:** `HOST=0.0.0.0`, `USE_FAKE_LLM=false`, and
  `REAL_LLM_PROVIDER=gemini` with `GEMINI_API_KEY` as a secret, or
  `REAL_LLM_PROVIDER=ollama` with `OLLAMA_BASE_URL` set to a remotely reachable
  Ollama server and `OLLAMA_MODEL` installed there. Never use `localhost` or
  `127.0.0.1` for the Render Ollama URL. Put `OLLAMA_API_KEY` in Render's secret
  environment variables when the server is protected by a Bearer-auth gateway.

Render supplies the `PORT` variable used by the server. To run without an API
key, set `USE_FAKE_LLM=true` instead.

### Use a local Ollama server with Render

The Render Free service cannot run the 3B Ollama model itself. You can keep
Ollama running on your PC and connect Render through an authenticated tunnel,
but your PC and Ollama must stay online. The tunnel URL is temporary and changes
when the tunnel restarts.

1. Generate a strong random token and keep it private.
2. In one PowerShell window, set `OLLAMA_PROXY_TOKEN` and run
   `python ollama_proxy.py`.
3. In another window, run
   `cloudflared tunnel --url http://127.0.0.1:11435`. Use the HTTPS
   `trycloudflare.com` URL it prints as Render's `OLLAMA_BASE_URL`.
4. In Render's environment settings, set `REAL_LLM_PROVIDER=ollama`,
   `OLLAMA_MODEL=llama3.2:3b`, and `OLLAMA_API_KEY` to the same private token.

The proxy binds only to localhost, accepts only authenticated
`/api/generate` requests, and forwards them to local Ollama. Do not expose port
`11434` directly or commit the token.