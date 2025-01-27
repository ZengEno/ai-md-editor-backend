
from langchain_core.messages import SystemMessage, AIMessage

from ...ai_models import get_llm
from ..state import EditorGraphState
from ...agent_utils import format_reflections
from ..prompts.article_prompt_new import current_article_prompt, other_articles_prompt, reference_articles_prompt


def reply_cot_prompt(current_article_prompt:str,
                    other_articles_prompt:str,
                    reference_articles_prompt:str,
                    formatted_reflections:str):
    return f'''You are an AI article editor assistant, your job is to answer the user's query based on the editing article or perform tasks based on the user's query.
You need to think step by step and decide if you need to edit the current article, and then reply to the user.
You should always think step by step first, and wrap your thinking process in <think> and </think> tags. The user will not see your thinking process, but you should always think step by step first.
At the end of your thinking process, you should think about if you need to edit the current article. You have to use the tool "edit_article_tool" to edit the current article.
If you decide to edit the article, you should think aoubt how to correctly call the tool "edit_article_tool" in your thinking process, and use the proper parameters for the tool.
Important: editing the article is not your job, what you can do is decide to call the tool or not, you should only use the tool "edit_article_tool" if you decide to edit the article.
After thinking, you should reply to the user. Be aware that the user will not see your thinking process, so you should reply to the user concisely and clearly. 
If the user asks questions, you should answer them briefly. If the user asks you to edit the article, or you think editting the article is necessary, you should let the user know that you will edit the article.

The user is currently working on an article in markdown format, you should use the current article as context when responding to the users query.
The user may highlight some text in the current article, you should use the highlighted text as context when generating your response.
You should edit the current article based on the users query, ensure you use markdown syntax when appropriate, as the text you generate will be rendered in markdown.
If the user has highlighted text, you should mainly focus on the highlighted text and the text around it. 

You should always respond with two parts, the first part is your thinking process to the users query wrapped in <think> and </think> tags, the second part is your response to the users query.
You don't need to include any other tags in your response.
The cuurent article has been formmated with tags which indicate the start and end of each line, you should use these tags to identify the text you need to edit.
Here are some examples of how you should respond, each example is wrapped in <example> and </example> tags:
<example_1>
The user's query:
What color an apple may look like?

Here is the current article the user is working on:
<line_1>Apple could be red</line_1>
<line_2>Banana could be yellow</line_2>
<line_3>Orange could be orange</line_3>

Here should be your response to the users query:
<think>
The user is asking about the color of an apple, and the line 1 of the current article mention the color of an apple could be red. As a result, I will respond to the user that the color of an apple could be red.
The user just asked about the color of an apple, there is no need to edit the current article.
</think>
Based on line 1 of the current article, an apple could be red.
</example_1>

<example_2>
The user's query:
Help me extend this sentence to be more informative.

Here is the current article the user is working on:
<line_1>Apple could be red</line_1>
<line_2>Banana could be yellow</line_2>
<line_3>Orange could be orange</line_3>

Here is the highlighted or selected text by the user:
<line_2>Banana could be yellow</line_2>

Here should be your response to the users query:
<think>
The user is asking to extend the highlighted sentence to be more informative, and the highlighted sentence is line 2 of the current article.
As a result, aside from letting the user know that I will edit the sentence accordingly, I will also use the tool "edit_article_tool" to edit the sentence accordingly.
</think>
I will edit the sentence you selected to be more informative.
</example_2>

<example_3>
The user's query:
What color an avocado may look like?

Here is the current article the user is working on:
<line_1>Apple could be red</line_1>
<line_2>Banana could be yellow</line_2>
<line_3>Orange could be orange</line_3>

Here should be your response to the users query:
<think>
The user is asking about the color of an avocado, and the current article does not mention the color of an avocado.
As a result, I will respond to the user that the color of an avocado could be green, and I can edit the current article to add this information.
</think>
The color of an avocado could be green. I will edit the current article to add this information.
</example_3>

<example_4>
The user's query:
What color an avocado may look like?

Here is the current article the user is working on:
<line_1>Apple could be red</line_1>
<line_2>Banana could be yellow</line_2>
<line_3>Orange could be orange</line_3>

Here is the reference article the user has access to:
<reference_article>
Article File Name: information_about_avocados.md
Content: Avocado could be green.
</reference_article>

Here should be your response to the users query:
<think>
The user is asking about the color of an avocado, and the current article does not mention the color of an avocado.
However, the reference article information_about_avocados.md mentions that the color of an avocado could be green.
As a result, I will respond to the user that based on the reference article, the color of an avocado could be green, and I can edit the current article to add this information.
</think>
Based on the reference article information_about_avocados.md, the color of an avocado could be green. I will edit the current article to add this information.
</example_4>


{current_article_prompt}

{other_articles_prompt}

{reference_articles_prompt}

You have the following reflections on style guidelines and general facts about the user to use when generating your response.
<reflections>
{formatted_reflections}
</reflections>

'''

# this is a tool for the llm to use
def edit_article_tool(line_to_edit: list[int], line_to_add: list[int], editing_instruction: str):
    '''This tool is used to edit the current article.
    line_to_edit: the line number of the line to edit, if there are multiple lines to edit, you should pass a list of line numbers.
    line_to_add: the line number that you want to add a new line after. For example, if you want to add a new line after the last line, you should pass the line number of the last line. 
    editing_instruction: the instruction of how you'd like to edit lines or add new lines.
    '''
    return {"line_to_edit": line_to_edit, "line_to_add": line_to_add, "editing_instruction": editing_instruction}


async def reply_cot(state: EditorGraphState):
    assistant_data = state.assistant_data
    if not assistant_data:
        raise ValueError(f"Assistant data not found")
    
    formatted_reflections = format_reflections(assistant_data.reflections)

    system_prompt = reply_cot_prompt(current_article_prompt=current_article_prompt(state.article, state.highlight_data),
                                    other_articles_prompt=other_articles_prompt(state.other_articles),
                                    reference_articles_prompt=reference_articles_prompt(state.reference_articles),
                                    formatted_reflections=formatted_reflections)
    
    llm = get_llm(llm=state.assistant_data.llm_provider, model='qwen-turbo', temperature=0)
    llm_tools = llm.bind_tools([edit_article_tool])

    input_messages = [SystemMessage(system_prompt)] + state.messages

    ai_message = await llm_tools.ainvoke(input=input_messages)

    if ai_message.tool_calls:
        tool_call = ai_message.tool_calls[0]
        tool_call_name = tool_call['name']
        tool_call_args = tool_call['args']
        tool_call_id = tool_call['id']
        edit_article_tool_call = {"name": tool_call_name, "args": tool_call_args, "id": tool_call_id}
    else:
        edit_article_tool_call = None

    return {"messages": ai_message, "edit_article_tool_call": edit_article_tool_call}