from typing import Annotated
from pydantic import BaseModel
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from ..agent_classes import (
    language_options,
    Article,
    HighlightData,
    )
from database.db_classes import AssistantData

class EditorGraphState(BaseModel):
    # The assistant data for the user.
    assistant_data: AssistantData | None = None
    # The next node to execute.
    next_node: str | None = None
    # The messages to send to the assistant.
    messages: Annotated[list[AnyMessage], add_messages]
    # The article the user is currently viewing.
    article: Article | None = None
    # The text the user highlighted.
    highlight_data: HighlightData | None = None

    edited_article: str | None = None
    edited_article_related_to: str | None = None
    
    other_articles: list[Article] | None = None
    reference_articles: list[Article] | None = None

    think_content: str | None = None

    # The language to translate the artifact to.
    language: language_options | None = None

    # The user defined rules to follow.
    user_defined_rules: list[str] | None = None


