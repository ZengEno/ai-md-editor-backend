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
    edited_article_related_to: str
    other_data: dict



# # Find the index of the tag in the chunk
# def find_tag_index_in_chunk(chunk: str, tag: str):
#     tag_found = False
#     j=0
#     for i in range(len(chunk)):
#         if chunk[i] == tag[j]:
#             tag_found = True
#             j+=1
#             if j == len(tag):
#                 break
#         else:
#             tag_found = False
#             j=0

#     tag_index_start = None
#     tag_index_end = None
#     if tag_found:
#         tag_index_start = i-j+1
#         tag_index_end = i

#     return tag_index_start, tag_index_end


# # Stream the data to the client
# async def send_stream_data(initial_state):
#     # Initialize the stream data
#     begin_tag = '<@edited_article>'
#     end_tag = '</@edited_article>'

#     updated_state = initial_state

#     content_to_send = ''
#     edited_article_to_send = ''
#     temporary_chunk = ''
#     streaming_edited_article = False

#     data_to_send = StreamResponse(assistant_id=initial_state.assistant_data.assistant_id,
#                                      assistant_status='thinking',
#                                      role='assistant',
#                                      content_chunk='',
#                                      edited_article_chunk='',
#                                      edited_article_related_to='',
#                                      other_data={})
#     yield f"data: {data_to_send.model_dump_json()}\n\n"

#     try:
#         async for event, chunk in editor_graph.astream(initial_state, stream_mode=["messages", "values"]):

#             if event == 'values':
#                 updated_state = chunk

#             if event == 'messages':
#                 if isinstance(chunk[0], AIMessageChunk):
#                     temporary_chunk += chunk[0].content

#                     # Check if we are streaming the edited article
#                     if not streaming_edited_article:
#                         tag = begin_tag
#                     else:
#                         tag = end_tag

#                     # Find the tag in the temporary chunk
#                     tag_index_start, tag_index_end = find_tag_index_in_chunk(temporary_chunk, tag)
#                     if tag_index_start is None:
#                         # If the tag is not found, add the temporary chunk to the content or edited article
#                         if not streaming_edited_article:
#                             content_to_send += temporary_chunk
#                         else:
#                             edited_article_to_send += temporary_chunk
#                         temporary_chunk = ''

#                     elif temporary_chunk[tag_index_start : tag_index_end+1] != tag:
#                         # If just part of the tag is found, add the string before the tag to the content or edited article
#                         if not streaming_edited_article:
#                             content_to_send += temporary_chunk[0:tag_index_start]
#                         else:
#                             edited_article_to_send += temporary_chunk[0:tag_index_start]
#                         temporary_chunk = temporary_chunk[tag_index_start:]

#                     else:
#                         # If the tag is found, toggle the streaming_edited_article flag
#                         if not streaming_edited_article:
#                             content_to_send += temporary_chunk[0:tag_index_start]
#                         else:
#                             edited_article_to_send += temporary_chunk[0:tag_index_start]
                        
#                         temporary_chunk = temporary_chunk[tag_index_end+1:]
#                         content_to_send += tag
#                         # toggle the streaming_edited_article flag
#                         streaming_edited_article = not streaming_edited_article
                    
#             data_to_send = StreamResponse(assistant_id=initial_state.assistant_data.assistant_id,
#                                      assistant_status='responding',
#                                      role='assistant',
#                                      content_chunk=content_to_send,
#                                      edited_article_chunk=edited_article_to_send,
#                                      edited_article_related_to=updated_state['article'].file_name,
#                                      other_data={})
#             # send the data to the client
#             yield f"data: {data_to_send.model_dump_json()}\n\n"
#             # clear the content and edited article after sending to prevent sending the same data again
#             content_to_send = ''
#             edited_article_to_send = ''

        
#     except Exception as e:
#         yield f"data: {json.dumps({'error': str(e)})}\n\n"
#         print(f"Unexpected error during stream generation: {e}")
#     finally:
#         yield f"data: [DONE]\n\n"









def process_text_chunk(text_chunk, target_tags, default_content, tag_contents, current_tag, chunk_leftover):
    while text_chunk:
            bracket_match = re.search(r'<([^<>]*)>', text_chunk)
            if bracket_match:
                text_inside_bracket = bracket_match.group(1)

                if current_tag and text_inside_bracket == f"/{current_tag}":
                    # 如果有current_tag, 且text_inside_bracket是current_tag的close tag
                    tag_contents[current_tag] += text_chunk[:bracket_match.start()]
                    text_chunk = text_chunk[bracket_match.end():]
                    current_tag = None
                    continue

                # find if there's a new open tag in the chunk
                if text_inside_bracket in target_tags:
                    if current_tag:
                        tag_contents[current_tag] += text_chunk[:bracket_match.start()]
                    else:
                        default_content += text_chunk[:bracket_match.start()]
                    text_chunk = text_chunk[bracket_match.end():]
                    current_tag = text_inside_bracket

                    # add the newly opened tag to content_default
                    default_content += f"<{text_inside_bracket}></{text_inside_bracket}>"
                    continue
                else:
                    # the text_inside_bracket is not a target tag
                    if current_tag:
                        tag_contents[current_tag] += text_chunk[:bracket_match.end()]
                    else:
                        default_content += text_chunk[:bracket_match.end()]
                    text_chunk = text_chunk[bracket_match.end():]
                    continue
            
            else:
                # no bracket match
                unfinished_bracket_match = re.search(r'<([^<>]*)$', text_chunk)
                if unfinished_bracket_match and len(unfinished_bracket_match.group(1)) <= max(len(tag) for tag in target_tags):
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
                                edited_article_related_to='',
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
                                    edited_article_related_to='',
                                    other_data={})
        await websocket.send_json(data_to_send.model_dump())