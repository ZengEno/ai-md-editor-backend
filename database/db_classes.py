from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
from agent.agent_classes import Reflections

class UserInfo(BaseModel):
    user_id: str  # has to be unique
    email: str  # has to be unique
    user_nickname: str
    phone_number: str | None = None

class LLMToken(BaseModel):
    model_name: str
    timestamp: datetime
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class EmbeddingToken(BaseModel):
    model_name: str
    timestamp: datetime
    total_tokens: int

class AssistantInfo(BaseModel):
    assistant_id: str
    assistant_name: str

class UserProfile(UserInfo):
    hashed_password: str
    refresh_token: str | None = None

    created_at: datetime
    last_login: datetime | None = None

    assistant_info_list: list[AssistantInfo] = Field(default_factory=list)

    llm_token_usage: list[LLMToken] = Field(default_factory=list)
    llm_price: float = 0.0
    embedding_token_usage: list[EmbeddingToken] = Field(default_factory=list)
    embedding_price: float = 0.0

    inactive: bool = False


class AssistantData(BaseModel):
    user_id: str
    assistant_id: str

    assistant_name: str
    llm_provider: Literal['qwen']

    reflections: Reflections

    user_defined_rules: list[str] | None = None

