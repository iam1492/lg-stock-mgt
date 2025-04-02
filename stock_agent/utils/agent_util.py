from dotenv import load_dotenv
from typing import TypedDict, Literal, Union
from langgraph.graph import StateGraph, START, END # Ensure END is imported
from langgraph.graph.message import add_messages
from typing import Annotated, Any
from langchain_core.messages import AnyMessage, RemoveMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

load_dotenv()

class SubState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def create_agent_with_tool(llm, tools, system_prompt, last_message_count_to_transmission = 1, name=None):
    has_tool = len(tools) > 0
    tool_node = ToolNode(tools)

    if has_tool:
        _llm = llm.bind_tools(tools)
    else:
        _llm = llm

    # Agent node function
    def agent_node_func(state: SubState):
        messages = state['messages']
        # Inject system prompt before invoking - ensure it doesn't duplicate if already present
        # A simple approach: filter out previous system messages and add the current one
        filtered_messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]
        current_system_message = SystemMessage(content=system_prompt)
        final_messages = [current_system_message] + filtered_messages

        response = _llm.invoke(final_messages)
        return {"messages": [response]}

    # Message pruning node function
    def delete_messages_func(state: SubState):
        messages = state["messages"]
        # Keep the first HumanMessage (initial query) and the last AIMessage (agent's response)
        # This is a basic strategy, might need refinement based on graph logic
        if not messages:
            return {"messages": []}

        # Find first human message and last AI message
        first_human = next((msg for msg in messages if isinstance(msg, HumanMessage)), None)
        last_ai = next((msg for msg in reversed(messages) if isinstance(msg, AIMessage)), None)

        keep_messages = []
        if first_human:
            keep_messages.append(first_human)
        if last_ai:
            # Avoid adding the same message twice if it's the only one
            if not first_human or first_human.id != last_ai.id:
                 keep_messages.append(last_ai)

        # Identify messages to remove (those not in keep_messages)
        # Use IDs for reliable removal
        keep_ids = {msg.id for msg in keep_messages}
        to_remove_ids = [msg.id for msg in messages if msg.id not in keep_ids]

        if to_remove_ids:
            # Return RemoveMessage objects for LangGraph to handle deletion
            return {"messages": [RemoveMessage(id=msg_id) for msg_id in to_remove_ids]}
        else:
            # If no messages need removal, return empty list to signify no change needed here
            return {"messages": []}


    # Conditional edge function
    def should_continue(state: SubState) -> Literal["tools", "delete_messages"]:
        messages = state['messages']
        if not messages:
            return "delete_messages" # Or END? Let's route to delete for cleanup.
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "delete_messages" # Route to message deletion if no tools called

    # Build the subgraph
    subgraph_builder = StateGraph(SubState)
    subgraph_builder.add_node("agent", agent_node_func)
    subgraph_builder.add_node("delete_messages", delete_messages_func) # Add the node back

    if has_tool:
        subgraph_builder.add_node("tools", tool_node)
        subgraph_builder.add_edge(START, "agent")
        subgraph_builder.add_conditional_edges(
            "agent",
            should_continue,
            {"tools": "tools", "delete_messages": "delete_messages"} # Route to tools or delete
        )
        subgraph_builder.add_edge("tools", "agent") # Loop back after tools
        subgraph_builder.add_edge("delete_messages", END) # End after deleting messages
    else:
        # If no tools, agent -> delete_messages -> END
        subgraph_builder.add_edge(START, "agent")
        subgraph_builder.add_edge("agent", "delete_messages")
        subgraph_builder.add_edge("delete_messages", END)

    # Compile the subgraph
    subgraph = subgraph_builder.compile()
    subgraph.name = name
    return subgraph
