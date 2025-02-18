import asyncio
import json
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage, AnyMessage, AIMessage, AIMessageChunk

from routers.chat_utils import run_graph_and_stream
from agent.agent_classes import Article, Reflections, HighlightData
from agent.editor.state import EditorGraphState
from agent.editor.graph import editor_graph
from routers.auth_utils import get_jwt_payload, oauth2_bearer
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

class StreamRequest(BaseModel):
    type: str
    assistant_id: str
    messages: list[dict]
    highlight_data: HighlightData
    article: Article
    other_articles: list[Article]
    reference_articles: list[Article]
    config: dict
    

@chat_router.post("/completion")
async def chat_with_agent(chat_request: ChatRequest,
                          jwt_token: str = Depends(oauth2_bearer)):
    payload = get_jwt_payload(jwt_token=jwt_token)
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



async def process_stream_request(user_id: str, stream_request: StreamRequest, websocket: WebSocket):
    assistant_data = await db.assistant_data.find_one({"assistant_id": stream_request.assistant_id, "user_id": user_id})
    if not assistant_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Assistant not found")
    assistant_data = AssistantData(**assistant_data)
    
    # Convert the messages to a list of Langchain messages.
    lang_messages = []
    for msg in stream_request.messages:
        if msg['role'] == 'user':
            lang_messages.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            lang_messages.append(AIMessage(content=msg['content']))

    initial_state = EditorGraphState(messages=lang_messages, 
                                     assistant_data=assistant_data,
                                     article=stream_request.article,
                                     highlight_data=stream_request.highlight_data,
                                     other_articles=stream_request.other_articles,
                                     reference_articles=stream_request.reference_articles)
    
    await run_graph_and_stream(initial_state, websocket)


@chat_router.websocket("/stream")
async def stream_chat(websocket: WebSocket):
    """
    This endpoint provides a WebSocket connection
    Clients can connect to this endpoint to send and receive messages.

    **Usage:**

    1. Establish a WebSocket connection to `chat/stream`.
    2. Send messages in JSON format.
    3. Receive messages in JSON format.
    4. After websocket is opened, the client should send a message with type `auth` and token in the message body.
    5. After authentication, the client can send `stream_request` message to start a new stream.
    6. After the stream is started, the client can send `stream_stop` message to stop the stream. (under development)

    """
    try:
        await websocket.accept()

        # 当刚开启websocket时对用户进行验证，等待10秒，如果10秒内没有收到消息，则关闭连接
        auth_data = await asyncio.wait_for(websocket.receive_json(), timeout=10)
        try:
            if auth_data.get("type") == "auth":
                jwt_token = auth_data.get("token")
                if not jwt_token:
                    await websocket.close(code=4003, reason="Authentication token required")
                    return
                try:
                    # 验证jwt token, 若成功，获取user_id
                    payload = get_jwt_payload(jwt_token=jwt_token)
                    user_id = payload['data']['user_id']
                    await websocket.send_json({"type": "auth", "user_id": user_id})
                except HTTPException as e:
                    await websocket.close(code=4003, reason=e.detail)
                    return
            else:
                await websocket.close(code=4003, reason="Authentication message required")
                return 
        except asyncio.TimeoutError: #handle authentication timeout
            await websocket.close(code=4003, reason="Authentication timed out")
            return
        except json.JSONDecodeError:
            await websocket.close(code=4003, reason="Invalid authentication message format")
            return
        except Exception as e:
            await websocket.close(code=4003, reason="Authentication failed")
            return
        
        # websocket 主循环
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=45)  # 等待45秒
                if data.get('type') == 'quit':
                    break
                elif data.get('type') == 'stream':
                    stream_request = StreamRequest(**data)
                    # 处理stream请求
                    await process_stream_request(user_id=user_id, stream_request=stream_request, websocket=websocket)
                elif data.get('type') == 'stream_stop':
                    break
                elif data.get('type') == 'ping':
                    # 收到ping消息，返回pong，用于保持连接。客户端每30秒发送一次ping消息
                    await websocket.send_json({'type': 'pong'})

            except HTTPException as e:
                await websocket.close(code=4003, reason=e.detail)
                return
            except asyncio.TimeoutError:
                await websocket.close(code=1000, reason="Stream timed out")
                return
            except Exception as e:
                await websocket.close(code=1000, reason=str(e))
                return
            
        await websocket.close(code=1000, reason="Client disconnected")
            
    except Exception as e:
        await websocket.close(code=1000, reason=str(e))
        return
    except WebSocketDisconnect:
        return


