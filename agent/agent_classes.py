from pydantic import BaseModel
from typing import Literal, Any





class Article(BaseModel):
    file_name: str
    content: str
    file_category: Literal["editable", "reference"]


class HighlightData(BaseModel):
    text: str
    start_line: int | None = None
    end_line: int | None = None


class Reflections(BaseModel):
    # Style rules to follow for generating content.
    style_guidelines: list[str]
    # Key content to remember about the user when generating content.
    general_facts: list[str]



language_options = Literal["english", "chinese"]