import re
from langchain_core.messages import SystemMessage, AIMessage

from ...ai_models import get_llm
from ..state import EditorGraphState
from ...agent_utils import format_reflections
from ..prompts.article_prompt_new import current_article_prompt, other_articles_prompt, reference_articles_prompt


def think_prompt(current_article_prompt:str,
                    other_articles_prompt:str,
                    reference_articles_prompt:str,
                    formatted_reflections:str):
    return f'''You are an AI article editor assistant, your job is to answer the user's query based on the editing article or perform tasks based on the user's query.
The user is currently working on an article in markdown format, you should use the current article as context when trying to understand the users query.
The user may highlight or select some text in the current article, if the user does, you should mainly use the highlighted text and the text around it as context. 
The user may ask questions or ask you to perform tasks, you can respond to the questions or use your ability to perform tasks. 
Since you are an editor assistant, you have the ability to edit the article. You do not have ability beyond an editor assistant, so you could not perform tasks beyond your ability. 
Your ability invovles editing some sentences in the article, inserting new lines, deleting some lines, extending some content in the article, and so on. 
The user may ask questions like helping them summarize the article, correct grammar, or anything else that helps them with their writing.
You should respond to the user and decide if you need to edit the article or just answer the user's question. Sometimes you can just answer the user, but sometimes you need to edit the article.
In essence, you can edit the article in any way you want in order to answer the users query or perform tasks.

The current article has been formmated with tags which indicate the start and end of each line, you should use these tags to identify the text you need to edit.
The tags are formatted as <line_i> and </line_i>, where i is the line number, you should use these tags to wrap the edited content of the line.
If you decide to edit the article, you should wrap all the edited content in <edited_content> and </edited_content> tags. 
Importantly, tags are used in the editor code to format the article, do not use any tags other than <line_i></line_i> and <edited_content></edited_content> since it may mess up the formatting.

For example, if there are lines in the article like this:
<line_1>This is a line in the article.</line_1>
<line_2>This is another line in the article.</line_2>

And you want to edit line 1, you should wrap your edited text in the tags like this:
<edited_content>
<line_1>This is the edited line in the article.</line_1>
</edited_content>

And if you want to delete line 2, you should wrap an empty line in the tags like this:
<edited_content>
<line_2></line_2>
</edited_content>

And if you want to insert a new line, you need to think about where to insert it. 
If you want to insert some content after a line, you can add a newline character after the content of the line, and then add the new content.
For example, if you want to insert a new line after line 2, you can do this:
<edited_content>
<line_2>This is another line in the article.\nThis is a new line after line 2.</line_2>
</edited_content>

Similarly, if you want to insert a new line before a line, you can add the new content followed by a newline character before the content of the line. 
This is useful when you want to insert a new line at the beginning of the article (before line 1), like this:
<edited_content>
<line_1>This is a new line at the beginning of the article.\nThis is a line in the article.</line_1>
</edited_content>

And you can edit multiple lines at once, for example, if you want to edit line 1 and line 2, you should wrap the edited content in tags like this:
<edited_content>
<line_1>This is the edited line 1.</line_1>
<line_2>This is the edited line 2.\nAnd this is a new line after line 2.</line_2>
</edited_content>

Typically, you don't need to repeat the lines that you don't edit, although you can if you want to.


{current_article_prompt}

{other_articles_prompt}

{reference_articles_prompt}

You have the following reflections on style guidelines and general facts about the user to use when generating your response.
<reflections>
{formatted_reflections}
</reflections>
'''


def parse_tag_content(ai_message: AIMessage):
    if "<think>" not in ai_message.content or "</think>" not in ai_message.content:
        return ai_message.content, '', ''
        
    think_content = ai_message.content.split("<think>")[1].split('</think>')[0].strip()

    response_content = ai_message.content.split('</think>')[1].strip()
    edited_content = ''

    if '<edited_content>' in response_content and '</edited_content>' in response_content:
        edited_content = response_content.split('<edited_content>')[1].split('</edited_content>')[0]
        response_content = response_content.split('<edited_content>')[0] + '<edited_content></edited_content>' + response_content.split('</edited_content>')[1]

    return response_content, think_content, edited_content


async def think(state: EditorGraphState):
    assistant_data = state.assistant_data
    if not assistant_data:
        raise ValueError(f"Assistant data not found")
    
    formatted_reflections = format_reflections(assistant_data.reflections)

    system_prompt = think_prompt(current_article_prompt=current_article_prompt(state.article, state.highlight_data),
                                    other_articles_prompt=other_articles_prompt(state.other_articles),
                                    reference_articles_prompt=reference_articles_prompt(state.reference_articles),
                                    formatted_reflections=formatted_reflections)
    
    llm = get_llm(llm='ollama', model='deepseek-r1:14b', temperature=0.5)

    input_messages = [SystemMessage(system_prompt)] + state.messages

    ai_message = await llm.ainvoke(input=input_messages)

    response_content, think_content, edited_content = parse_tag_content(ai_message)

    if edited_content:
        # Regular expression to find content inside <line_i> tags
        pattern = r'<line_(\d+)>(.*?)</line_\1>'
        matches = re.findall(pattern, edited_content, re.DOTALL)

        edited_article_by_lines = state.article.content.split('\n')
        for key, value in matches:
            edited_article_by_lines[int(key)-1] = value
        
        edited_article = '\n'.join(edited_article_by_lines)
    else:
        edited_article = ''
        
    edited_article_related_to = state.article.file_name if edited_article else ''

    ai_message.content = response_content

    return {"messages": ai_message,
            "think_content": think_content,
            "edited_article": edited_article,
            "edited_article_related_to": edited_article_related_to}