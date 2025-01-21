import json
from pydantic import BaseModel
from langchain_core.messages import AIMessageChunk
from agent.editor.graph import editor_graph

class ChatStreamResponse(BaseModel):
    assistant_id: str
    assistant_status: str
    role: str
    content_chunk: str
    edited_article_chunk: str
    edited_article_related_to: str
    other_data: dict



# Find the index of the tag in the chunk
def find_tag_index_in_chunk(chunk: str, tag: str):
    tag_found = False
    j=0
    for i in range(len(chunk)):
        if chunk[i] == tag[j]:
            tag_found = True
            j+=1
            if j == len(tag):
                break
        else:
            tag_found = False
            j=0

    tag_index_start = None
    tag_index_end = None
    if tag_found:
        tag_index_start = i-j+1
        tag_index_end = i

    return tag_index_start, tag_index_end


# Stream the data to the client
async def send_stream_data(initial_state):
    # Initialize the stream data
    begin_tag = '<@edited_article>'
    end_tag = '</@edited_article>'

    updated_state = initial_state

    content_to_send = ''
    edited_article_to_send = ''
    temporary_chunk = ''
    streaming_edited_article = False

    data_to_send = ChatStreamResponse(assistant_id=initial_state.assistant_data.assistant_id,
                                     assistant_status='thinking',
                                     role='assistant',
                                     content_chunk='',
                                     edited_article_chunk='',
                                     edited_article_related_to='',
                                     other_data={})
    yield f"data: {data_to_send.model_dump_json()}\n\n"

    try:
        async for event, chunk in editor_graph.astream(initial_state, stream_mode=["messages", "values"]):

            if event == 'values':
                updated_state = chunk

            if event == 'messages':
                if isinstance(chunk[0], AIMessageChunk):
                    temporary_chunk += chunk[0].content

                    # Check if we are streaming the edited article
                    if not streaming_edited_article:
                        tag = begin_tag
                    else:
                        tag = end_tag

                    # Find the tag in the temporary chunk
                    tag_index_start, tag_index_end = find_tag_index_in_chunk(temporary_chunk, tag)
                    if tag_index_start is None:
                        # If the tag is not found, add the temporary chunk to the content or edited article
                        if not streaming_edited_article:
                            content_to_send += temporary_chunk
                        else:
                            edited_article_to_send += temporary_chunk
                        temporary_chunk = ''

                    elif temporary_chunk[tag_index_start : tag_index_end+1] != tag:
                        # If just part of the tag is found, add the string before the tag to the content or edited article
                        if not streaming_edited_article:
                            content_to_send += temporary_chunk[0:tag_index_start]
                        else:
                            edited_article_to_send += temporary_chunk[0:tag_index_start]
                        temporary_chunk = temporary_chunk[tag_index_start:]

                    else:
                        # If the tag is found, toggle the streaming_edited_article flag
                        if not streaming_edited_article:
                            content_to_send += temporary_chunk[0:tag_index_start]
                        else:
                            edited_article_to_send += temporary_chunk[0:tag_index_start]
                        
                        temporary_chunk = temporary_chunk[tag_index_end+1:]
                        content_to_send += tag
                        # toggle the streaming_edited_article flag
                        streaming_edited_article = not streaming_edited_article
                    
            data_to_send = ChatStreamResponse(assistant_id=initial_state.assistant_data.assistant_id,
                                     assistant_status='responding',
                                     role='assistant',
                                     content_chunk=content_to_send,
                                     edited_article_chunk=edited_article_to_send,
                                     edited_article_related_to=updated_state['article'].file_name,
                                     other_data={})
            # send the data to the client
            yield f"data: {data_to_send.model_dump_json()}\n\n"
            # clear the content and edited article after sending to prevent sending the same data again
            content_to_send = ''
            edited_article_to_send = ''

        
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        print(f"Unexpected error during stream generation: {e}")
    finally:
        yield f"data: [DONE]\n\n"











# async def send_stream_data_test(initial_state):

#     # Initialize the stream data
#     begin_tag = '<@edited_article>'
#     end_tag = '</@edited_article>'

#     updated_state = initial_state

#     content_to_send = ''
#     edited_article_to_send = ''
#     temporary_chunk = ''
#     streaming_edited_article = False

#     data_to_send = ChatStreamResponse(assistant_id=initial_state.assistant_data.assistant_id,
#                                      assistant_status='thinking',
#                                      role='assistant',
#                                      content_chunk='',
#                                      edited_article_chunk='',
#                                      edited_article_related_to='',
#                                      other_data={})
#     print(f"data: {data_to_send.model_dump_json()}\n\n")

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
#                         streaming_edited_article = not streaming_edited_article
#                         content_to_send += temporary_chunk[0:tag_index_start]
#                         content_to_send += tag
#                         edited_article_to_send += temporary_chunk[tag_index_end+1:]
#                         temporary_chunk = ''
                    
#             data_to_send = ChatStreamResponse(assistant_id=initial_state.assistant_data.assistant_id,
#                                      assistant_status='responding',
#                                      role='assistant',
#                                      content_chunk=content_to_send,
#                                      edited_article_chunk=edited_article_to_send,
#                                      edited_article_related_to=updated_state['article'].file_name,
#                                      other_data={})
#             print('-'*100)
#             print(f"content:{data_to_send.content_chunk}")
#             print(f"edited_article:{data_to_send.edited_article_chunk}")

        
#     except Exception as e:
#         print(f"Unexpected error during stream generation: {e}")
#     finally:
#         print("data: [DONE]\n\n")