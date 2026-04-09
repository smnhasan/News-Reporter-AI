import logging
import time
from typing import Any, Dict, List, Optional, Sequence, Union

from .db.redis_client import RedisDB
from .retriever import Retriever

# Configure logging only if no handlers exist (avoid duplicate logs in larger apps)
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


class IngestorError(Exception):
    """Base exception for Ingestor-related failures."""


class IngestorInitError(IngestorError):
    """Raised when initialization fails."""


class Ingestor:
    """
    Fetches scraped contents from Redis, converts them to retriever documents, and ingests them.

    Parameters
    ----------
    redis_client : Optional[RedisDB]
        Inject a RedisDB instance for easier testing.
    retriever : Optional[Retriever]
        Inject a Retriever instance for easier testing.
    max_retries : int
        Max retry attempts for transient read operations (e.g., Redis).
    backoff_base : float
        Initial backoff delay in seconds for retries (exponential).
    """

    def __init__(
        self,
        redis_client: Optional[RedisDB] = None,
        retriever: Optional[Retriever] = None,
        max_retries: int = 3,
        backoff_base: float = 0.2,
    ) -> None:
        self.max_retries = max(1, int(max_retries))
        self.backoff_base = max(0.0, float(backoff_base))

        try:
            self.redis_client = redis_client if redis_client is not None else RedisDB()
        except Exception as e:
            logger.exception("Failed to initialize Redis client.")
            raise IngestorInitError(f"Redis initialization failed: {e}") from e

        try:
            self.retriever = retriever if retriever is not None else Retriever()
        except Exception as e:
            logger.exception("Failed to initialize Retriever.")
            raise IngestorInitError(f"Retriever initialization failed: {e}") from e

    # ---------------------------
    # Internal helpers
    # ---------------------------

    def _retry(self, fn, *args, **kwargs):
        """Simple exponential backoff retry wrapper for read operations."""
        attempt = 0
        delay = self.backoff_base
        last_exc: Optional[Exception] = None

        while attempt < self.max_retries:
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_exc = e
                attempt += 1
                logger.warning(
                    "Operation %s failed on attempt %d/%d: %s",
                    getattr(fn, "__name__", str(fn)),
                    attempt,
                    self.max_retries,
                    e,
                )
                if attempt < self.max_retries and delay > 0:
                    time.sleep(delay)
                    delay *= 2

        # Exhausted retries
        assert last_exc is not None
        raise last_exc

    # ---------------------------
    # Public API
    # ---------------------------

    def fetch_data(self) -> List[Dict[str, Any]]:
        """
        Fetch all contents for scraped URLs from Redis.

        Returns
        -------
        List[Dict[str, Any]]
            Each item is a dict that at least contains:
            - 'url': str
            - 'content': str
        """
        try:
            urls: Sequence[str] = self._retry(self.redis_client.get_all_scraped_urls)
        except Exception as e:
            logger.exception("Failed to fetch scraped URLs from Redis.")
            raise IngestorError(f"Fetching URLs failed: {e}") from e

        if not urls:
            logger.info("No scraped URLs found in Redis.")
            return []

        contents: List[Dict[str, Any]] = []
        for url in urls:
            try:
                raw = self._retry(self.redis_client.get_content, url)
            except Exception as e:
                logger.error("Failed to fetch content for url=%s: %s", url, e)
                continue

            if raw is None:
                logger.warning("No content returned for url=%s; skipping.", url)
                continue

            # Normalize into a dict with at least 'url' and 'content'
            if isinstance(raw, dict):
                text = raw.get("content")
                if not text or not str(text).strip():
                    logger.warning("Empty 'content' for url=%s; skipping.", url)
                    continue
                payload = dict(raw)
                payload.setdefault("url", url)
                contents.append(payload)
            else:
                text = str(raw).strip()
                if not text:
                    logger.warning("Empty content (non-dict) for url=%s; skipping.", url)
                    continue
                contents.append({"url": url, "content": text})

        return contents


    def process_data(self, contents: Sequence[Dict[str, Any]]) -> List[Any]:
        """
        Convert raw contents into retriever documents, ensuring no empty strings.

        Args:
            contents (Sequence[Dict[str, Any]]): List of content items to process.

        Returns:
            List[Any]: A flat list of documents with non-empty content ready for ingestion.
        """
        documents: List[Any] = []

        for item in contents:
            url = item.get("url", "unknown")
            text = item.get("content")
            
            logger.info("Processing content for url=%s", url)
            logger.info("Raw content: \n%s", text)            

            if not text or not str(text).strip():
                logger.warning("Skipping item with empty content (url=%s).", url)
                continue

            try:
                docs = self.retriever.create_documents(str(text), source_url=url)
            except Exception as e:
                logger.exception("Failed to create documents for url=%s: %s", url, e)
                continue

            if docs is None:
                logger.warning("Retriever returned None for url=%s; skipping.", url)
                continue

            # Normalize to list and filter out any empty documents
            if isinstance(docs, list):
                non_empty_docs = [doc for doc in docs if doc.page_content.strip()]
                documents.extend(non_empty_docs)
            else:
                if docs.page_content.strip():
                    documents.append(docs)
                else:
                    logger.warning("Skipping single empty document for url=%s", url)
                    continue
                    
            logger.info("Created %d non-empty documents for url=%s", len(non_empty_docs) if isinstance(docs, list) else 1, url)

        if not documents:
            logger.info("No non-empty documents produced from %d content items.", len(contents))

        return documents

    def ingest(self) -> Dict[str, Union[int, str]]:
        """
        Full pipeline: fetch -> process -> ingest.

        Returns
        -------
        Dict[str, Union[int, str]]
            Summary including counts of items processed and ingested.
        """
        try:
            contents = self.fetch_data()
        except IngestorError:
            # Already logged.
            raise
        except Exception as e:
            logger.exception("Unexpected error during fetch_data: %s", e)
            raise IngestorError(f"Unexpected error during fetch: {e}") from e

        try:
            processed_documents = self.process_data(contents)
        except Exception as e:
            logger.exception("Unexpected error during process_data: %s", e)
            raise IngestorError(f"Unexpected error during processing: {e}") from e

        if not processed_documents:
            logger.warning("No documents to ingest. Pipeline ends with 0 ingested documents.")
            return {
                "urls_found": len(contents),
                "docs_created": 0,
                "docs_ingested": 0,
                "status": "nothing_to_ingest",
            }

        # Ingest (avoid retries by default to prevent duplicate writes)
        try:
            self.retriever.ingest(processed_documents)
        except Exception as e:
            logger.exception("Failed to ingest documents: %s", e)
            raise IngestorError(f"Ingestion failed: {e}") from e

        ingested_count = len(processed_documents)
        logger.info("Successfully ingested %d documents.", ingested_count)
        return {
            "urls_found": len(contents),
            "docs_created": ingested_count,
            "docs_ingested": ingested_count,
            "status": "ok",
        }

