
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import START, END, StateGraph
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore
from .state import ReflectionGraphState
from .prompts import REFLECT_SYSTEM_PROMPT, REFLECT_USER_PROMPT
from ..agent_utils import format_reflections
from ..agent_classes import Reflections
from ..ai_models import get_llm
from database.db import db


async def reflect(state: ReflectionGraphState):

    assistant_data = state.assistant_data
    if not assistant_data:
        raise ValueError(f"Assistant data not found")
    
    formatted_reflections = format_reflections(assistant_data.reflections)

    # convert the article to a string
    if hasattr(state.article, 'content'):
        article_as_string = state.article.content
    else:
        article_as_string = 'No article found.'

    # convert the conversation history to a string
    conversation_as_string = "\n\n".join(
        f"<{msg.type}>\n{msg.content}\n</{msg.type}>" for msg in state.messages
        )

    # this is a tool for the llm
    def generate_reflections(style_guidelines: list[str], general_facts: list[str]):
        '''This function is used to generate reflections based on the context provided.
        The input variable style_guidelines should be the complete new list of style rules and guidelines.
        The input variable general_facts should be the complete new list of memories/facts about the user.'''
        return Reflections(style_guidelines=style_guidelines, general_facts=general_facts)
    
    llm = get_llm(llm="qwen", size="small", temperature=0)
    llm_tools = llm.bind_tools(tools=[generate_reflections], tool_choice="generate_reflections")

    formatted_system_prompt = REFLECT_SYSTEM_PROMPT.format(article=article_as_string, reflections=formatted_reflections)

    formatted_user_prompt = REFLECT_USER_PROMPT.format(conversation=conversation_as_string)

    # Prepare messages for the language model
    input_messages = [
        SystemMessage(formatted_system_prompt),
        HumanMessage(formatted_user_prompt),
    ]

    response = await llm_tools.ainvoke(input=input_messages)
    if not response.tool_calls:
        raise AttributeError('No tool_calls found in LLM response')

    # Extract the generated reflections (replace with actual extraction logic)
    new_reflections = generate_reflections(style_guidelines=response.tool_calls[0]['args']['style_guidelines'],
                                        general_facts=response.tool_calls[0]['args']['general_facts'])
    
    await db.assistant_data.update_one({"assistant_id": assistant_data.assistant_id}, {"$set": {"reflections": new_reflections.model_dump()}})

    # this node will not update anything to the state
    return {"messages": []}

graph_builder = StateGraph(ReflectionGraphState)
graph_builder.add_node('reflect', reflect)
graph_builder.add_edge(START, 'reflect')

reflection_graph = graph_builder.compile()
