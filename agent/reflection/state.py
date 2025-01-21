from typing import Annotated
from pydantic import BaseModel
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from ..agent_classes import Article
from database.db_classes import AssistantData


class ReflectionGraphState(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages]
    article: Article | None = None
    assistant_data: AssistantData | None = None