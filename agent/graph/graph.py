from langgraph.graph import StateGraph, END
from agent.graph.state import AgentState
from agent.graph.nodes import llm_node, tool_node, decide_node
from agent.graph.edges import route_after_llm, route_after_decide


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("llm_node", llm_node)
    builder.add_node("tool_node", tool_node)
    builder.add_node("decide_node", decide_node)

    builder.set_entry_point("llm_node")

    builder.add_conditional_edges(
        "llm_node",
        route_after_llm,
        {
            "tool_node": "tool_node",
            "decide_node": "decide_node",
        },
    )

    builder.add_edge("tool_node", "llm_node")

    builder.add_conditional_edges(
        "decide_node",
        route_after_decide,
        {
            "END": END,
            "llm_node": "llm_node",
        },
    )

    return builder.compile()

agent_graph = build_graph()
