# study-buddy

## Run locally

Install dependencies and start the web server:

```powershell
python -m pip install -r requirements.txt
$env:USE_FAKE_LLM = "false"
$env:REAL_LLM_PROVIDER = "ollama"
.\start_ui.ps1
```

Make sure Ollama is running and has the `llama3.2:3b` model installed. The
launcher starts the API server and opens `http://127.0.0.1:8000`. For Gemini,
set `$env:REAL_LLM_PROVIDER = "gemini"`; the launcher will prompt for a key.
For offline demo mode, set `$env:USE_FAKE_LLM = "true"` instead.

## Deploy on Render

Create a Python web service connected to this repository and configure:

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `python api_server.py`
- **Environment:** `HOST=0.0.0.0`, `USE_FAKE_LLM=false`, `REAL_LLM_PROVIDER=gemini`, and
  `GEMINI_API_KEY` as a secret environment variable

Render supplies the `PORT` variable used by the server. To run without an API
key, set `USE_FAKE_LLM=true` instead.