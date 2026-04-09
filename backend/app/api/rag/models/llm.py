import requests
import os
from typing import Any, Dict, List, Optional, Union
from langchain_core.language_models.llms import BaseLLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.outputs import Generation, LLMResult
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("API_URL", "").rstrip("/")

class LLM(BaseLLM):
    """
    Custom LLM class for interfacing with a local OpenAI-compatible API endpoint.
    """

    api_url: str = Field(default=f"{BASE_URL}/v1/chat/completions")
    api_key: Optional[str] = Field(default=None)
    model_name: str = Field(default="gpt-oss-20b")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=512)

    def __init__(
        self,
        api_url: str = f"{BASE_URL}/v1/chat/completions",
        api_key: Optional[str] = None,
        model_name: str = "gpt-oss-20b",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ):
        super().__init__(
            api_url=api_url,
            api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    def _call(
        self,
        prompt: Union[str, List[Dict[str, str]]],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Handle messages list or raw string
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            **kwargs
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]

        except requests.RequestException as e:
            raise ValueError(f"LLM API request failed: {e}")

    def stream_response(self, prompt: Union[str, List[Dict[str, str]]], **kwargs: Any):
        import json
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        else:
            messages = prompt

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
            **kwargs
        }

        response = requests.post(self.api_url, json=payload, headers=headers, stream=True)
        response.raise_for_status()

        for line in response.iter_lines(chunk_size=1):
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    if data_str == '[DONE]':
                        break
                    try:
                        data = json.loads(data_str)
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                yield delta['content']
                    except json.JSONDecodeError:
                        continue

    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        generations = []
        for prompt in prompts:
            text = self._call(prompt, stop, run_manager, **kwargs)
            generations.append([Generation(text=text)])

        return LLMResult(generations=generations)

    @property
    def _llm_type(self) -> str:
        return "custom_openai_compat_llm"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"api_url": self.api_url, "model_name": self.model_name}
    
    def generate_response(self, prompt: Union[str, List[Dict[str, str]]]):
        """
        Convenience method to generate a response from either a string or message list.
        """
        try:
            return self._call(prompt)
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm sorry, I couldn't generate a response. Please try again."