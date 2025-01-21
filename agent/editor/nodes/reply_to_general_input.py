from langchain_core.messages import SystemMessage

from ..state import EditorGraphState
from ..prompts.article_prompts import current_article_prompt, other_articles_prompt, reference_articles_prompt
from ...agent_utils import format_reflections
from ...ai_models import get_llm


def reply_to_general_input_prompt(current_article_prompt:str,
                                  other_articles_prompt:str,
                                  reference_articles_prompt:str,
                                  formatted_reflections:str):
    return f'''You are an AI assistant tasked with responding to the users question.
The user is currently working on an article in markdown format, you should use the current article as context when responding to the users question.
The user may highlight some text in the current article, you should use the highlighted text as context when generating your response.

{current_article_prompt}

{other_articles_prompt}

{reference_articles_prompt}

You have the following reflections on style guidelines and general facts about the user to use when generating your response.
<reflections>
{formatted_reflections}
</reflections>

'''


async def reply_to_general_input(state: EditorGraphState):
    assistant_data = state.assistant_data
    if not assistant_data:
        raise ValueError(f"Assistant data not found")
    
    formatted_reflections = format_reflections(assistant_data.reflections)

    system_prompt = reply_to_general_input_prompt(current_article_prompt=current_article_prompt(state.article, state.highlight_data.text),
                                                    other_articles_prompt=other_articles_prompt(state.other_articles),
                                                    reference_articles_prompt=reference_articles_prompt(state.reference_articles),
                                                    formatted_reflections=formatted_reflections)
 

    llm = get_llm(llm=state.assistant_data.llm_provider, size="small", temperature=0)

    input_messages = [SystemMessage(system_prompt)] + state.messages

    ai_message = await llm.ainvoke(input=input_messages)

    return {"messages": ai_message}

