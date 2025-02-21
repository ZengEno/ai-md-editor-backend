import json
import re
from fastapi import WebSocket
from pydantic import BaseModel
from langchain_core.messages import AIMessageChunk
from agent.editor.graph import editor_graph
from agent.editor.state import EditorGraphState

class StreamResponse(BaseModel):
    type: str
    assistant_id: str
    assistant_status: str
    role: str
    content_chunk: str
    think_content_chunk: str
    edited_article_chunk: str
    edited_article_related_to: str | None
    other_data: dict | None



def process_text_chunk(text_chunk, target_tags, default_content, tag_contents, current_tag, chunk_leftover):
    while text_chunk:
            bracket_match = re.search(r'<([^<>]*)>', text_chunk)
            if bracket_match:
                text_inside_bracket = bracket_match.group(1)

                if current_tag:
                    if text_inside_bracket == f"/{current_tag}":
                        # 如果有current_tag, 且text_inside_bracket是current_tag的close tag
                        tag_contents[current_tag] += text_chunk[:bracket_match.start()]
                        text_chunk = text_chunk[bracket_match.end():]
                        current_tag = None
                    else:
                        # 如果有current_tag, 且text_inside_bracket不是current_tag的close tag
                        tag_contents[current_tag] += text_chunk[:bracket_match.end()]
                        text_chunk = text_chunk[bracket_match.end():]
                elif text_inside_bracket in target_tags:
                    # find if there's a new open tag in the chunk
                    default_content += text_chunk[:bracket_match.start()]
                    text_chunk = text_chunk[bracket_match.end():]
                    current_tag = text_inside_bracket

                    # handle edited content tag specifically
                    if text_inside_bracket == 'edited_content':
                        default_content += f"<edited_content></edited_content>"
                else:
                    default_content += text_chunk[:bracket_match.end()]
                    text_chunk = text_chunk[bracket_match.end():]
            
            else:
                # no bracket match
                unfinished_bracket_match = re.search(r'<([^<>]*)$', text_chunk)
                if unfinished_bracket_match and len(unfinished_bracket_match.group(1)) <= (max(len(tag) for tag in target_tags) + 1):
                    chunk_leftover = text_chunk[unfinished_bracket_match.start():]
                    if current_tag:
                        tag_contents[current_tag] += text_chunk[:unfinished_bracket_match.start()]
                    else:
                        default_content += text_chunk[:unfinished_bracket_match.start()]
                    text_chunk = ''
                else:
                    if current_tag:
                        tag_contents[current_tag] += text_chunk
                    else:
                        default_content += text_chunk
                    text_chunk = ''
    return default_content, tag_contents, current_tag, chunk_leftover


async def run_graph_and_stream(current_state, websocket: WebSocket):
    data_to_send = StreamResponse(type='stream',
                                assistant_id=current_state.assistant_data.assistant_id,
                                assistant_status='thinking',
                                role='assistant',
                                content_chunk='',
                                think_content_chunk='',
                                edited_article_chunk='',
                                edited_article_related_to=current_state.article.file_name,
                                other_data={})
    await websocket.send_json(data_to_send.model_dump())

    try:
        target_tags = ['think', 'edited_content']
        default_content = ""
        tag_contents = {tag: "" for tag in target_tags}  # Initialize buffers for target tags
        current_tag = None
        chunk_leftover = ''

        async for event, chunk in editor_graph.astream(current_state, stream_mode=["messages", "values"]):
            if event == 'values':
                current_state = EditorGraphState(**chunk)

            if event == 'messages' and isinstance(chunk[0], AIMessageChunk):
                # prepare the text chunk
                text_chunk = chunk_leftover + chunk[0].content
                chunk_leftover = ''

                # process the text chunk
                (default_content, 
                    tag_contents, 
                    current_tag, 
                    chunk_leftover) = process_text_chunk(text_chunk=text_chunk, 
                                                        target_tags=target_tags, 
                                                        default_content=default_content, 
                                                        tag_contents=tag_contents, 
                                                        current_tag=current_tag, 
                                                        chunk_leftover=chunk_leftover)
                
                # send the default content and tag contents here
                data_to_send = StreamResponse(type='stream',
                                            assistant_id=current_state.assistant_data.assistant_id,
                                            assistant_status='thinking',
                                            role='assistant',
                                            content_chunk=default_content,
                                            think_content_chunk=tag_contents['think'],
                                            edited_article_chunk=tag_contents['edited_content'],
                                            edited_article_related_to=current_state.article.file_name,
                                            other_data={})
                await websocket.send_json(data_to_send.model_dump())
                default_content = ''
                tag_contents['think'] = ''
                tag_contents['edited_content'] = ''
                
        # finally handle the leftover chunk
        if current_tag:
            tag_contents[current_tag] += chunk_leftover
        else:
            default_content += chunk_leftover
        
        data_to_send = StreamResponse(type='stream',
                                    assistant_id=current_state.assistant_data.assistant_id,
                                    assistant_status='thinking',
                                    role='assistant',
                                    content_chunk=default_content,
                                    think_content_chunk=tag_contents['think'],
                                    edited_article_chunk=tag_contents['edited_content'],
                                    edited_article_related_to=current_state.article.file_name,
                                    other_data={})
        await websocket.send_json(data_to_send.model_dump())

    except Exception as e:
        await websocket.close(code=1000, reason=str(e))
    finally:
        data_to_send = StreamResponse(type='stream_end',
                                    assistant_id=current_state.assistant_data.assistant_id,
                                    assistant_status='thinking',
                                    role='assistant',
                                    content_chunk='',
                                    think_content_chunk='',
                                    edited_article_chunk='',
                                    edited_article_related_to=current_state.article.file_name,
                                    other_data={})
        await websocket.send_json(data_to_send.model_dump())