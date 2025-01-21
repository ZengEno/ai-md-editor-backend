
from langchain_core.messages import SystemMessage, AIMessage

from ...ai_models import get_llm
from ..state import EditorGraphState
from ...agent_utils import format_reflections
from ..prompts.article_prompts import current_article_prompt, other_articles_prompt, reference_articles_prompt


def reply_with_edit_prompt(current_article_prompt:str,
                            other_articles_prompt:str,
                            reference_articles_prompt:str,
                            formatted_reflections:str):
    return f'''You are an AI assistant tasked with responding to the users query and editing the current article.
The user is currently working on an article in markdown format, you should use the current article as context when responding to the users query.
The user may highlight some text in the current article, you should use the highlighted text as context when generating your response.
You should edit the current article based on the users query, ensure you use markdown syntax when appropriate, as the text you generate will be rendered in markdown.
If the user has highlighted text, you should mainly focus on the highlighted text and the text around it. 

You should always respond with two parts, the first part is your response to the users query, the second part is the edited article.
You should always wrap the edited article in <@edited_article> and </@edited_article> tags, and you don't need to include any other tags in your response other than the <@edited_article> and </@edited_article> tags.
Here are some examples of how you should format your response:
<example_1>
The user's query:
Help me correct the typos in the article.

Here is the current article the user is working on:
I am a sotware enginer.

Here should be your response to the users query:
I will help you correct the typos in the article.

<@edited_article>I am a software engineer.</@edited_article>
</example_1>

<example_2>
The user's query:
Help me extend this sentence to be more informative.

Here is the highlighted text in the current article the user is working on:
I am a software engineer.

Here should be your response to the users query:
I will help you extend the sentence to be more informative.

<@edited_article>I am a software engineer, and I write python and javascript.</@edited_article>
</example_2>


{current_article_prompt}

{other_articles_prompt}

{reference_articles_prompt}

You have the following reflections on style guidelines and general facts about the user to use when generating your response.
<reflections>
{formatted_reflections}
</reflections>

'''


def seperate_response_and_edited_article(ai_message: AIMessage):
    if "<@edited_article>" not in ai_message.content or "</@edited_article>" not in ai_message.content:
        return ai_message.content, ''
        
    response_str = ai_message.content.split("<@edited_article>")[0]
    edited_article = ai_message.content.split("<@edited_article>")[1].split("</@edited_article>")[0]
    return response_str, edited_article


async def reply_with_edit(state: EditorGraphState):
    assistant_data = state.assistant_data
    if not assistant_data:
        raise ValueError(f"Assistant data not found")
    
    formatted_reflections = format_reflections(assistant_data.reflections)

    system_prompt = reply_with_edit_prompt(current_article_prompt=current_article_prompt(state.article, state.highlight_data.text),
                                            other_articles_prompt=other_articles_prompt(state.other_articles),
                                            reference_articles_prompt=reference_articles_prompt(state.reference_articles),
                                            formatted_reflections=formatted_reflections)
        
    llm = get_llm(llm=state.assistant_data.llm_provider, size="small", temperature=0)

    input_messages = [SystemMessage(system_prompt)] + state.messages

    # the llm response will be streamed and handled by routers/chat.py
    ai_message = await llm.ainvoke(input=input_messages)

    response_str, edited_article = seperate_response_and_edited_article(ai_message)

    ai_message.content = response_str

    edited_article_related_to = state.article.file_name if edited_article else ''

    return {"messages": ai_message, 
            "edited_article": edited_article,
            "edited_article_related_to": edited_article_related_to}