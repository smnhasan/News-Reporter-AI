"""
main.py
Entrypoint — loads models, builds the FastAPI app, starts uvicorn,
and optionally creates an ngrok tunnel.

Usage
-----
  python main.py                                        # localhost (default)
  USE_NGROK=true NGROK_AUTHTOKEN=<tok> python main.py  # ngrok tunnel
  uvicorn app:app --host 0.0.0.0 --port 8000           # direct uvicorn (no ngrok)
"""

import logging
import sys
import threading
import time

import uvicorn

from app    import create_app
from config import settings
from server import CombinedServer
from tunnel import NgrokTunnelManager

logger = logging.getLogger(__name__)


# ── Startup banner ────────────────────────────────────────────────────────────

def _print_banner(base_url: str, via_ngrok: bool) -> None:
    sep  = "=" * 65
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


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    from logger import setup_logging
    setup_logging()

    print("=" * 65)
    print("  Initialising GPT-OSS-20B + E5 + Instructor-Large Server")
    print("=" * 65)

    # ── Load models ───────────────────────────────────────────────────────────
    print("\n[1/2] Downloading & loading models (may take a few minutes)...")
    combined_server = CombinedServer()
    app = create_app(combined_server)

    # ── Start uvicorn in a background thread ──────────────────────────────────
    print(f"\n[2/2] Starting FastAPI server on {settings.host}:{settings.port}...")

    def _run_uvicorn():
        uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")

    server_thread = threading.Thread(target=_run_uvicorn, daemon=True)
    server_thread.start()
    time.sleep(4)   # wait for uvicorn to bind

    # ── Ngrok (optional) ──────────────────────────────────────────────────────
    tunnel_mgr: NgrokTunnelManager | None = None
    if settings.use_ngrok:
        tunnel_mgr = NgrokTunnelManager()
        tunnel_mgr.setup_auth(settings.ngrok_authtoken)
        public_url = tunnel_mgr.create_tunnel(port=settings.port)

        if not public_url:
            logger.error("Failed to create ngrok tunnel. Falling back to localhost.")
            base_url  = f"http://localhost:{settings.port}"
            via_ngrok = False
        else:
            time.sleep(2)
            tunnel_mgr.test_tunnel()   # logs result; proceed regardless
            base_url  = public_url
            via_ngrok = True
    else:
        base_url  = f"http://localhost:{settings.port}"
        via_ngrok = False

    _print_banner(base_url, via_ngrok)
    print("  Server is running. Press Ctrl+C to stop.\n")

    # ── Block — keep the process alive ────────────────────────────────────────
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
