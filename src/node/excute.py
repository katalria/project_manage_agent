from langgraph.graph import StateGraph
from src.orchestrator.state_schema import AgentState
from nodes.user_input import user_input_node
from src.orchestrator.manager import manager_node
from src.epic.agent import epic_agent_node
from src.story.agent import story_agent_node
from src.point.agent import point_agent_node
from src.user_query.agent import user_question_node

builder = StateGraph(AgentState)

# ❌ Nodes
builder.add_node("user_input", user_input_node)
builder.add_node("manager", manager_node)
builder.add_node("epic", epic_agent_node)
builder.add_node("story", story_agent_node)
builder.add_node("point", point_agent_node)
builder.add_node("question", user_question_node)
builder.add_node("done", lambda state: state)

# ❌ Edges
builder.set_entry_point("user_input")
builder.add_edge("user_input", "manager")

builder.add_conditional_edges(
    "manager",
    condition_key="next_action",
    conditional_edge_mapping={
        "epic": "epic",
        "story": "story",
        "point": "point",
        "question": "question",
        "done": "done",
    }
)

# Agent → Manager loop
builder.add_edge("epic", "manager")
builder.add_edge("story", "manager")
builder.add_edge("point", "manager")
builder.add_edge("question", "manager")

# Compile LangGraph
graph = builder.compile()
