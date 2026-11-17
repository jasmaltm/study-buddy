# study-buddy

## Run locally

Install dependencies and start the web server:

```powershell
python -m pip install -r requirements.txt
$env:USE_FAKE_LLM = "true"
python api_server.py
```

Open `http://localhost:8000`. For live Gemini responses, set
`USE_FAKE_LLM=false` and provide `GEMINI_API_KEY` through the environment.

## Deploy on Render

Create a Python web service connected to this repository and configure:

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `python api_server.py`
- **Environment:** `USE_FAKE_LLM=false`, `REAL_LLM_PROVIDER=gemini`, and
  `GEMINI_API_KEY` as a secret environment variable

Render supplies the `PORT` variable used by the server. To run without an API
key, set `USE_FAKE_LLM=true` instead.