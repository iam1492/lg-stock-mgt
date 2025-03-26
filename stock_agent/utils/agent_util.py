from dotenv import load_dotenv
from typing import TypedDict, Literal, Union
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from typing import Annotated, Any
from langchain_core.messages import AnyMessage, RemoveMessage, HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

load_dotenv()

class SubState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

def create_agent(llm, tools, system_prompt, last_message_count_to_transmission = 1, name=None):
    tool_node = ToolNode(tools)
    if tools:
        _llm = llm.bind_tools(tools)    
    else:
        _llm = llm
        
    def create_agent_node(state, llm , system_prompt):
        human_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        other_messages = [msg for msg in state["messages"] 
                        if not isinstance(msg, HumanMessage) and not isinstance(msg, SystemMessage)]
        system_messages = [SystemMessage(content=system_prompt)]
        messages = system_messages + human_messages + other_messages
        message = llm.invoke(messages)
        
        return {
            "messages": [message]
        }
        
    agent_node = lambda state: create_agent_node(state, _llm, system_prompt=system_prompt)
    
    def delete_messages(state, last_message_count):
        messages = state["messages"]
        if len(messages) > last_message_count:
            return {"messages": [RemoveMessage(id=message.id) for message in messages[:-last_message_count]]}
        return {"messages": []}
    
    def my_tools_condition(
        state: Union[list[AnyMessage], dict[str, Any], BaseModel],
        messages_key: str = "messages",
    ) -> Literal["tools", "delete_messages"]:
        if isinstance(state, list):
            ai_message = state[-1]
        elif isinstance(state, dict) and (messages := state.get(messages_key, [])):
            ai_message = messages[-1]
        elif messages := getattr(state, messages_key, []):
            ai_message = messages[-1]
        else:
            raise ValueError(f"No messages found in input state to tool_edge: {state}")
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "tools"
        return "delete_messages"
    
    delete_messages_node = lambda state: delete_messages(state, last_message_count = last_message_count_to_transmission)
    
    subgraph_builder = StateGraph(SubState)
    subgraph_builder.add_node("agent", agent_node)
    subgraph_builder.add_node("tools", tool_node)
    subgraph_builder.add_node("delete_messages", delete_messages_node)
    subgraph_builder.add_edge(START, "agent")
    subgraph_builder.add_conditional_edges("agent", my_tools_condition)
    subgraph_builder.add_edge("tools", "agent")
    subgraph = subgraph_builder.compile(name=name)
    
    return subgraph
