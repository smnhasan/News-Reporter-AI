import os
import asyncio
import requests
import aiohttp
from typing import List, Optional, Union
from langchain_core.embeddings import Embeddings
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("API_URL", "").rstrip("/")

class Embedding(Embeddings):
    """
    Custom Embeddings class for interfacing with an OpenAI-compatible embedding API.
    Specifically optimized for the intfloat/multilingual-e5-large model.
    """

    def __init__(
        self,
        api_url: str = f"{BASE_URL}/v1/embeddings",
        api_key: Optional[str] = None,
        model_name: str = "intfloat/multilingual-e5-large"
    ):
        super().__init__()
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(requests.RequestException),
    )
    def _embed(self, input_data: Union[str, List[str]]) -> List[List[float]]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model_name,
            "input": input_data
        }
        
        response = requests.post(self.api_url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        return [item["embedding"] for item in data["data"]]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(aiohttp.ClientError),
    )
    async def _async_embed(self, session: aiohttp.ClientSession, input_data: Union[str, List[str]]) -> List[List[float]]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model_name,
            "input": input_data
        }

        async with session.post(self.api_url, json=payload, headers=headers) as response:
            if response.status != 200:
                body = await response.text()
                raise aiohttp.ClientError(f"HTTP Error {response.status}: {body}")
            data = await response.json()
            return [item["embedding"] for item in data["data"]]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs with 'passage: ' prefix."""
        prefixed_texts = [f"passage: {text}" for text in texts]
        return self._embed(prefixed_texts)

    def embed_query(self, text: str) -> List[float]:
        """Embed query with 'query: ' prefix."""
        prefixed_text = f"query: {text}"
        result = self._embed(prefixed_text)
        return result[0]

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Asynchronously embed search docs with 'passage: ' prefix."""
        prefixed_texts = [f"passage: {text}" for text in texts]
        async with aiohttp.ClientSession() as session:
            return await self._async_embed(session, prefixed_texts)

    async def aembed_query(self, text: str) -> List[float]:
        """Asynchronously embed query with 'query: ' prefix."""
        prefixed_text = f"query: {text}"
        async with aiohttp.ClientSession() as session:
            result = await self._async_embed(session, prefixed_text)
            return result[0]