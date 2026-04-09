# GPT-OSS-20B + Multilingual-E5 + Instructor-Large  
### OpenAI-Compatible FastAPI Server

A production-ready FastAPI server converted from the original Kaggle notebook.  
Serves GPT-OSS-20B (via llama-cpp-python) alongside two embedding models, fully compatible with the OpenAI API schema.

---

## Project layout

```
gpt_oss_server/
├── main.py           # Entrypoint — starts uvicorn + optional ngrok
├── server.py         # FastAPI app, routes, CombinedServer class
├── config.py         # Pydantic-settings config (reads .env)
├── tunnel.py         # NgrokTunnelManager
├── test_api.py       # Quick smoke-test script
├── requirements.txt
└── .env.example      # Copy to .env and fill in values
```

---

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

For GPU support install llama-cpp-python with CUDA wheels:
```bash
pip install llama-cpp-python \
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122 \
    --no-cache-dir
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env as needed
```

### 3. Run (localhost only — default)

```bash
python main.py
```

Server starts at **http://localhost:8000**

### 4. Run with ngrok

Set `USE_NGROK=true` and supply your auth token in `.env`:

```
USE_NGROK=true
NGROK_AUTHTOKEN=your_ngrok_token_here
```

Then:
```bash
python main.py
```

The public ngrok URL is printed in the startup banner.

---

## Endpoints

| Method | Path                    | Description                    |
|--------|-------------------------|--------------------------------|
| GET    | `/`                     | API info                       |
| GET    | `/health`               | Health check                   |
| GET    | `/v1/models`            | List available models          |
| POST   | `/v1/chat/completions`  | Chat completion (stream/non-stream) |
| POST   | `/v1/completions`       | Text completion (stream/non-stream) |
| POST   | `/v1/embeddings`        | Embeddings (E5 or Instructor)  |

---

## Embedding models

Pass the model ID in the request body:

| Model ID                        | Dimensions |
|---------------------------------|-----------|
| `intfloat/multilingual-e5-large`| 1024      |
| `hkunlp/instructor-large`       | 768       |

Instructor embeddings support a custom `instruction` field:

```json
{
  "model": "hkunlp/instructor-large",
  "input": ["Your text here"],
  "instruction": "Represent the document for retrieval: "
}
```

---

## Running the test script

```bash
python test_api.py                         # localhost:8000
python test_api.py http://localhost:8001   # custom port
python test_api.py https://xxxx.ngrok.io  # ngrok URL
```

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
| `LLM_MODEL_ID`                   | `gpt-oss-20b`                    | Model ID in API responses              |
| `N_CTX`                          | `10048`                          | Context window size                    |
| `N_GPU_LAYERS`                   | `-1`                             | `-1` = all layers on GPU               |
| `MAX_REQUESTS`                   | `3`                              | Concurrent request semaphore           |
| `EMBEDDING_MODEL_E5_ID`          | `intfloat/multilingual-e5-large` | E5 model HF path                       |
| `EMBEDDING_MODEL_INSTRUCTOR_ID`  | `hkunlp/instructor-large`        | Instructor model HF path               |
| `HF_TOKEN`                       | *(empty)*                        | HuggingFace token for faster downloads |
