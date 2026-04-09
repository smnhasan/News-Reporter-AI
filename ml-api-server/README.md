# GPT-OSS-20B + Multilingual-E5 + Instructor-Large  
### OpenAI-Compatible FastAPI Server — v2

---

## Project layout

```
gpt_oss_server/
│
├── main.py               # Entrypoint — loads models, starts uvicorn + optional ngrok
├── app.py                # FastAPI app factory (create_app)
├── server.py             # CombinedServer — model loading + async handler methods
├── schemas.py            # Shared Pydantic request models
├── config.py             # Pydantic-Settings (reads .env)
├── logger.py             # Centralised logging — console + rotating daily file
├── tunnel.py             # NgrokTunnelManager
│
├── routes/
│   ├── __init__.py       # register_routes() — attaches all routers to the app
│   ├── health.py         # GET /   GET /health
│   ├── models.py         # GET /v1/models
│   ├── chat.py           # POST /v1/chat/completions
│   ├── completions.py    # POST /v1/completions
│   └── embeddings.py     # POST /v1/embeddings
│
├── logs/                 # Auto-created at runtime
│   ├── server_YYYY-MM-DD.log    (Python rotating handler — DEBUG+)
│   └── stdout_YYYY-MM-DD.log   (bash stdout/stderr capture — INFO+)
│
├── start.sh              # Launch server (background, logs to logs/)
├── stop.sh               # Graceful shutdown via PID file
│
├── test_api.py           # Smoke-test for all endpoints
├── requirements.txt
└── .env.example          # → copy to .env and configure
```

---

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

For GPU support, install llama-cpp-python with CUDA wheels:
```bash
pip install llama-cpp-python \
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122 \
    --no-cache-dir
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env — set PORT, USE_NGROK, NGROK_AUTHTOKEN, HF_TOKEN, etc.
```

### 3. Start

```bash
chmod +x start.sh stop.sh

./start.sh             # localhost (USE_NGROK=false)
USE_NGROK=true ./start.sh  # with ngrok tunnel
PORT=8001 ./start.sh   # custom port
```

Press **Ctrl+C** to detach from the log tail — the server keeps running in the background.

### 4. Stop

```bash
./stop.sh
```

### 5. Run directly (no background / no log capture)

```bash
python main.py
```

---

## Endpoints

| Method | Path                    | Description                            |
|--------|-------------------------|----------------------------------------|
| GET    | `/`                     | API info                               |
| GET    | `/health`               | Health check                           |
| GET    | `/v1/models`            | List available models                  |
| POST   | `/v1/chat/completions`  | Chat completion (stream / non-stream)  |
| POST   | `/v1/completions`       | Text completion (stream / non-stream)  |
| POST   | `/v1/embeddings`        | Embeddings (E5 or Instructor)          |

---

## Embedding models

| Model ID                        | Dimensions | Notes                      |
|---------------------------------|-----------|----------------------------|
| `intfloat/multilingual-e5-large`| 1024      | Default; 100+ languages    |
| `hkunlp/instructor-large`       | 768       | Pass custom `instruction`  |

```json
{
  "model": "hkunlp/instructor-large",
  "input": ["Your text here"],
  "instruction": "Represent the document for retrieval: "
}
```

---

## Logs

| File                            | Content                         | Rotation         |
|---------------------------------|---------------------------------|------------------|
| `logs/server_YYYY-MM-DD.log`    | Python logger (DEBUG and above) | Daily, 30 days   |
| `logs/stdout_YYYY-MM-DD.log`    | Raw stdout/stderr from process  | New file per day |
| `logs/server.pid`               | PID of running server           | Removed on stop  |

---

## Environment variables reference

| Variable                         | Default                          | Description                            |
|----------------------------------|----------------------------------|----------------------------------------|
| `HOST`                           | `0.0.0.0`                        | Bind host                              |
| `PORT`                           | `8000`                           | Bind port                              |
| `USE_NGROK`                      | `false`                          | `true` to expose via ngrok             |
| `NGROK_AUTHTOKEN`                | *(empty)*                        | ngrok auth token                       |
| `LLM_MODEL_REPO`                 | `ggml-org/gpt-oss-20b-GGUF`      | HuggingFace repo                       |
| `LLM_MODEL_FILE`                 | `gpt-oss-20b-mxfp4.gguf`         | GGUF filename                          |
| `LLM_MODEL_ID`                   | `gpt-oss-20b`                    | ID used in API responses               |
| `N_CTX`                          | `10048`                          | Context window size                    |
| `N_GPU_LAYERS`                   | `-1`                             | `-1` = all layers on GPU               |
| `MAX_REQUESTS`                   | `3`                              | Max concurrent requests (semaphore)    |
| `EMBEDDING_MODEL_E5_ID`          | `intfloat/multilingual-e5-large` | E5 model HF path                       |
| `EMBEDDING_MODEL_INSTRUCTOR_ID`  | `hkunlp/instructor-large`        | Instructor model HF path               |
| `HF_TOKEN`                       | *(empty)*                        | HuggingFace token for faster downloads |
