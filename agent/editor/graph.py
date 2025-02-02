from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from .state import EditorGraphState
from .nodes.reply_to_general_input import reply_to_general_input
from .nodes.reply_with_edit import reply_with_edit
from .nodes.routing import routing
from .nodes.think import think


def route_condition(state: EditorGraphState):
    if not state.next_node:
        raise ValueError("Next node not found")
    
    send_to = state.next_node
    state.next_node = None
    return Send(send_to, state)


graph_builder = StateGraph(EditorGraphState)

graph_builder.add_node('routing', routing)
graph_builder.add_node('reply_to_general_input', reply_to_general_input)
graph_builder.add_node('reply_with_edit', reply_with_edit)
graph_builder.add_node('think', think)

graph_builder.add_edge(START, 'routing')
graph_builder.add_conditional_edges('routing', route_condition, ['reply_to_general_input', 
                                                                'reply_with_edit',
                                                                'think'])

graph_builder.add_edge('reply_to_general_input', END)
graph_builder.add_edge('reply_with_edit', END)
graph_builder.add_edge('think', END)

editor_graph = graph_builder.compile()


