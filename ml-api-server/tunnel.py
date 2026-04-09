"""
Ngrok tunnel manager.
Wraps pyngrok to create / test / tear down an HTTP tunnel.
"""

import logging
import os
import time
import atexit
import requests

logger = logging.getLogger(__name__)


class NgrokTunnelManager:
    def __init__(self):
        self.tunnel     = None
        self.public_url: str | None = None
        self.is_active  = False
        atexit.register(self.cleanup)

    def setup_auth(self, authtoken: str = "") -> None:
        from pyngrok import ngrok as _ngrok
        try:
            token = authtoken or os.environ.get("NGROK_AUTHTOKEN", "")
            if token:
                _ngrok.set_auth_token(token)
                logger.info("Ngrok auth token set.")
            else:
                logger.warning("No ngrok auth token found — tunnel may be rate-limited or fail.")
        except Exception as e:
            logger.warning(f"Ngrok auth warning: {e}")

    def create_tunnel(self, port: int = 8000) -> str | None:
        from pyngrok import ngrok as _ngrok
        try:
            self.cleanup()
            logger.info(f"Creating ngrok tunnel on port {port}...")
            self.tunnel     = _ngrok.connect(port, "http")
            self.public_url = str(self.tunnel.public_url).rstrip("/")
            self.is_active  = True
            logger.info(f"Tunnel created: {self.public_url}")
            return self.public_url
        except Exception as e:
            logger.error(f"Tunnel creation failed: {e}")
            return None

    def test_tunnel(self, max_retries: int = 5) -> bool:
        if not self.public_url:
            return False
        for i in range(max_retries):
            try:
                r = requests.get(f"{self.public_url}/health", timeout=15)
                if r.status_code == 200:
                    logger.info("Tunnel health check passed.")
                    return True
            except Exception as e:
                if i == max_retries - 1:
                    logger.error(f"Tunnel test failed: {e}")
                else:
                    time.sleep(3)
        return False

    def cleanup(self) -> None:
        try:
            from pyngrok import ngrok as _ngrok
            if self.tunnel:
                _ngrok.disconnect(self.tunnel.public_url)
            _ngrok.kill()
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
        finally:
            self.tunnel     = None
            self.public_url = None
            self.is_active  = False
