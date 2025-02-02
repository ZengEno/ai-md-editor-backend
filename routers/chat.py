from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AnyMessage, AIMessage, AIMessageChunk

from routers.chat_utils import send_stream_data
from agent.agent_classes import Article, Reflections, HighlightData
from agent.editor.state import EditorGraphState
from agent.editor.graph import editor_graph
from routers.auth_utils import validate_jwt_and_get_pyaload
from database.db import db
from database.db_classes import AssistantData


chat_router = APIRouter(tags=["Chat with Agent Assistant"])

class ChatRequest(BaseModel):
    assistant_id: str
    messages: list[dict]
    highlight_data: HighlightData
    article: Article
    other_articles: list[Article]
    reference_articles: list[Article]
    config: dict


class ChatResponse(BaseModel):
    assistant_id: str
    role: str
    content: str
    think_content: str
    edited_article: str
    edited_article_related_to: str
    other_data: dict


    

@chat_router.post("/completion")
async def chat_with_agent(chat_request: ChatRequest,
                          payload: dict = Depends(validate_jwt_and_get_pyaload)):
    # Get the assistant data for the user.
    user_id = payload['data']['user_id']
    assistant_data = await db.assistant_data.find_one({"assistant_id": chat_request.assistant_id, "user_id": user_id})
    if not assistant_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Assistant not found")
    assistant_data = AssistantData(**assistant_data)

    # Convert the messages to a list of Langchain messages.
    lang_messages = []
    for msg in chat_request.messages:
        if msg['role'] == 'user':
            lang_messages.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            lang_messages.append(AIMessage(content=msg['content']))

    initial_state = EditorGraphState(messages=lang_messages, 
                                     assistant_data=assistant_data,
                                     article=chat_request.article,
                                     highlight_data=chat_request.highlight_data,
                                     other_articles=chat_request.other_articles,
                                     reference_articles=chat_request.reference_articles)
    
    all_states = []
    async for output in editor_graph.astream(initial_state, stream_mode="values"):
        all_states.append(output)

    response_content = all_states[-1]['messages'][-1].content
    think_content = all_states[-1]['think_content'] if 'think_content' in all_states[-1] else ''
    edited_article = all_states[-1]['edited_article'] if 'edited_article' in all_states[-1] else ''
    edited_article_related_to = all_states[-1]['edited_article_related_to'] if 'edited_article_related_to' in all_states[-1] else ''
    
    return ChatResponse(assistant_id=chat_request.assistant_id,
                                role="assistant",
                                content=response_content,
                                think_content=think_content,
                                edited_article=edited_article,
                                edited_article_related_to=edited_article_related_to,
                                other_data={})
















@chat_router.post("/stream")
async def stream_chat_with_agent(chat_request: ChatRequest,
                                payload: dict = Depends(validate_jwt_and_get_pyaload)):
    # Get the assistant data for the user.
    user_id = payload['data']['user_id']
    assistant_data = await db.assistant_data.find_one({"assistant_id": chat_request.assistant_id, "user_id": user_id})
    if not assistant_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Assistant not found")
    assistant_data = AssistantData(**assistant_data)

    # Convert the messages to a list of Langchain messages.
    lang_messages = []
    for msg in chat_request.messages:
        if msg['role'] == 'user':
            lang_messages.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            lang_messages.append(AIMessage(content=msg['content']))

    initial_state = EditorGraphState(messages=lang_messages, 
                                     assistant_data=assistant_data,
                                     article=chat_request.article,
                                     highlight_data=chat_request.highlight_data,
                                     other_articles=chat_request.other_articles,
                                     reference_articles=chat_request.reference_articles)
    
    return StreamingResponse(send_stream_data(initial_state), media_type="text/event-stream")



@chat_router.websocket("/stream")
async def stream_chat_with_agent(websocket: WebSocket,
                                 payload: dict = Depends(validate_jwt_and_get_pyaload)):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        print(data)
