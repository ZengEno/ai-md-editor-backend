
from ..state import EditorGraphState




async def routing(state: EditorGraphState):

    if state.article.file_category == "reference":
        return {"messages": [], 
                "next_node": "reply_to_general_input"}
    
    next_node = "think"

    if next_node == "think":
        return {"messages": [], 
                "next_node": next_node, 
                "edited_article_related_to": state.article.file_name}

    return {"messages": [], 
            "next_node": next_node}