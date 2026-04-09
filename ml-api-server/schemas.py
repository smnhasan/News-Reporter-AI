"""
schemas.py
Pydantic request / response models shared across all routes.
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field
from config import settings

# Use configured IDs as defaults so schemas stay in sync with settings
_LLM_ID   = settings.llm_model_id
_E5_ID    = settings.embedding_model_e5_id


class Message(BaseModel):
    role: str    = Field(..., description="Role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class ChatCompletionRequest(BaseModel):
    model: str                            = Field(default=_LLM_ID)
    messages: List[Message]               = Field(...)
    temperature: Optional[float]          = Field(default=0.7,  ge=0.0, le=2.0)
    max_tokens: Optional[int]             = Field(default=500,  ge=1)
    stream: Optional[bool]                = Field(default=False)
    top_p: Optional[float]                = Field(default=1.0,  ge=0.0, le=1.0)
    frequency_penalty: Optional[float]    = Field(default=0.0,  ge=-2.0, le=2.0)
    presence_penalty: Optional[float]     = Field(default=0.0,  ge=-2.0, le=2.0)
    stop: Optional[Union[str, List[str]]] = Field(default=None)


class CompletionRequest(BaseModel):
    model: str                            = Field(default=_LLM_ID)
    prompt: str                           = Field(...)
    temperature: Optional[float]          = Field(default=0.7,  ge=0.0, le=2.0)
    max_tokens: Optional[int]             = Field(default=500,  ge=1)
    stream: Optional[bool]                = Field(default=False)
    top_p: Optional[float]                = Field(default=1.0,  ge=0.0, le=1.0)
    stop: Optional[Union[str, List[str]]] = Field(default=None)


class EmbeddingRequest(BaseModel):
    model: str                     = Field(default=_E5_ID)
    input: Union[str, List[str]]   = Field(..., description="Text or list of texts to embed")
    encoding_format: Optional[str] = Field(default="float")
    dimensions: Optional[int]      = Field(default=None)
    user: Optional[str]            = Field(default=None)
    instruction: Optional[str]     = Field(default=None)
