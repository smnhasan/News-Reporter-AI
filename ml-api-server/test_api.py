"""
Quick API test script.

Usage:
    python test_api.py                          # tests against localhost:8000
    python test_api.py http://localhost:8001    # custom URL
    python test_api.py https://xxxx.ngrok.io   # ngrok URL
"""

import sys
import json
import requests

BASE_URL = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")

SEP = "─" * 60


def section(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


# ── Health ────────────────────────────────────────────────────────────────────
section("Health")
r = requests.get(f"{BASE_URL}/health", timeout=10)
r.raise_for_status()
print(json.dumps(r.json(), indent=2))

# ── Models ────────────────────────────────────────────────────────────────────
section("Models")
r = requests.get(f"{BASE_URL}/v1/models", timeout=10)
r.raise_for_status()
for m in r.json()["data"]:
    print(f"  {m['id']}")

# ── Chat completion ───────────────────────────────────────────────────────────
section("Chat Completion")
r = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    json={
        "model": "gpt-oss-20b",
        "messages": [
            {"role": "system",  "content": "You are a helpful assistant. Be concise."},
            {"role": "user",    "content": "What is machine learning in one sentence?"},
        ],
        "max_tokens": 100,
        "temperature": 0.7,
    },
    timeout=60,
)
r.raise_for_status()
print(r.json()["choices"][0]["message"]["content"])

# ── Text completion ───────────────────────────────────────────────────────────
section("Text Completion")
r = requests.post(
    f"{BASE_URL}/v1/completions",
    json={
        "model": "gpt-oss-20b",
        "prompt": "The capital of France is",
        "max_tokens": 20,
        "temperature": 0.0,
    },
    timeout=60,
)
r.raise_for_status()
print(r.json()["choices"][0]["text"])

# ── Embeddings — E5 single ────────────────────────────────────────────────────
section("Embeddings: multilingual-e5-large (single)")
r = requests.post(
    f"{BASE_URL}/v1/embeddings",
    json={"model": "intfloat/multilingual-e5-large", "input": "query: What is artificial intelligence?"},
    timeout=30,
)
r.raise_for_status()
result = r.json()
print(f"  dim={len(result['data'][0]['embedding'])}  usage={result['usage']}")

# ── Embeddings — E5 batch ─────────────────────────────────────────────────────
section("Embeddings: multilingual-e5-large (batch)")
r = requests.post(
    f"{BASE_URL}/v1/embeddings",
    json={
        "model": "intfloat/multilingual-e5-large",
        "input": [
            "passage: Artificial intelligence is the simulation of human intelligence.",
            "passage: মেশিন লার্নিং একটি কৃত্রিম বুদ্ধিমত্তার শাখা।",
            "passage: L'apprentissage automatique est une branche de l'IA.",
        ],
    },
    timeout=30,
)
r.raise_for_status()
batch = r.json()
for item in batch["data"]:
    print(f"  index {item['index']}  →  dim={len(item['embedding'])}")
print(f"  total_tokens={batch['usage']['total_tokens']}")

# ── Embeddings — Instructor single ───────────────────────────────────────────
section("Embeddings: hkunlp/instructor-large (single, default instruction)")
r = requests.post(
    f"{BASE_URL}/v1/embeddings",
    json={"model": "hkunlp/instructor-large", "input": "What is artificial intelligence?"},
    timeout=30,
)
r.raise_for_status()
ins = r.json()
print(f"  dim={len(ins['data'][0]['embedding'])}  usage={ins['usage']}")

# ── Embeddings — Instructor batch + custom instruction ────────────────────────
section("Embeddings: hkunlp/instructor-large (batch, custom instruction)")
r = requests.post(
    f"{BASE_URL}/v1/embeddings",
    json={
        "model": "hkunlp/instructor-large",
        "input": [
            "Artificial intelligence is the simulation of human intelligence.",
            "Machine learning is a branch of AI.",
            "Deep learning uses neural networks.",
        ],
        "instruction": "Represent the document for retrieval: ",
    },
    timeout=30,
)
r.raise_for_status()
ins_batch = r.json()
for item in ins_batch["data"]:
    print(f"  index {item['index']}  →  dim={len(item['embedding'])}")
print(f"  total_tokens={ins_batch['usage']['total_tokens']}")

print(f"\n{'─'*60}")
print("  All tests passed ✓")
print(f"{'─'*60}\n")
