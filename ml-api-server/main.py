"""
Entry point for the GPT-OSS embedding / chat server.

Usage
-----
  # Localhost only (default):
  python main.py

  # With ngrok:
  USE_NGROK=true NGROK_AUTHTOKEN=<token> python main.py

  # Or configure via .env (copy .env.example → .env):
  python main.py
"""

import threading
import time
import logging
import sys

import uvicorn

from config import settings
from server import CombinedServer
from tunnel import NgrokTunnelManager

logger = logging.getLogger(__name__)


def print_banner(base_url: str, via_ngrok: bool) -> None:
    sep = "=" * 65
    mode = "ngrok tunnel" if via_ngrok else "localhost"
    print(f"\n{sep}")
    print(f"  GPT-OSS-20B + Multilingual-E5 + Instructor-Large  [{mode}]")
    print(sep)
    print(f"\n  Base URL : {base_url}")
    print(f"\n  Endpoints:")
    print(f"    POST  {base_url}/v1/chat/completions")
    print(f"    POST  {base_url}/v1/completions")
    print(f"    POST  {base_url}/v1/embeddings")
    print(f"    GET   {base_url}/v1/models")
    print(f"    GET   {base_url}/health")
    print(f"\n  Models:")
    print(f"    LLM            : {settings.llm_model_id}")
    print(f"    Embeddings (1) : {settings.embedding_model_e5_id} (dim={settings.embedding_model_e5_dim})")
    print(f"    Embeddings (2) : {settings.embedding_model_instructor_id} (dim={settings.embedding_model_instructor_dim})")
    print(f"{sep}\n")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)s  %(message)s",
    )

    print("=" * 65)
    print("  Initialising GPT-OSS-20B + E5 + Instructor-Large Server")
    print("=" * 65)

    # ── Load models ───────────────────────────────────────────────────────────
    print("\n[1/2] Downloading & loading models (may take a few minutes)...")
    combined = CombinedServer(
        llm_model_name=settings.llm_model_repo,
        llm_model_file=settings.llm_model_file,
        n_ctx=settings.n_ctx,
        n_gpu_layers=settings.n_gpu_layers,
        max_concurrent_requests=settings.max_requests,
    )

    # ── Start uvicorn in a background thread ──────────────────────────────────
    print(f"\n[2/2] Starting FastAPI server on {settings.host}:{settings.port}...")

    def _run_uvicorn():
        uvicorn.run(
            combined.app,
            host=settings.host,
            port=settings.port,
            log_level="info",
        )

    server_thread = threading.Thread(target=_run_uvicorn, daemon=True)
    server_thread.start()

    # Give uvicorn a moment to bind
    time.sleep(4)

    # ── Ngrok (optional) ──────────────────────────────────────────────────────
    if settings.use_ngrok:
        tunnel_mgr = NgrokTunnelManager()
        tunnel_mgr.setup_auth(settings.ngrok_authtoken)
        public_url = tunnel_mgr.create_tunnel(port=settings.port)

        if not public_url:
            logger.error("Failed to create ngrok tunnel. Falling back to localhost.")
            base_url   = f"http://localhost:{settings.port}"
            via_ngrok  = False
        else:
            time.sleep(2)
            if tunnel_mgr.test_tunnel():
                base_url  = public_url
                via_ngrok = True
            else:
                logger.warning("Tunnel health check failed — server may still be starting.")
                base_url  = public_url
                via_ngrok = True
    else:
        tunnel_mgr = None
        base_url   = f"http://localhost:{settings.port}"
        via_ngrok  = False

    print_banner(base_url, via_ngrok)

    # ── Block main thread (keep process alive) ────────────────────────────────
    print("  Server is running. Press Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        if tunnel_mgr:
            tunnel_mgr.cleanup()
        sys.exit(0)


if __name__ == "__main__":
    main()
