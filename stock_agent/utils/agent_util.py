from dotenv import load_dotenv
from typing import TypedDict, Literal, Union
from langgraph.graph import StateGraph, START
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
    
    def create_agent_node(state, illm , system_prompt):
        human_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        ai_messages = [msg for msg in state["messages"] if isinstance(msg, AIMessage)]
        other_messages = [msg for msg in state["messages"] 
                        if not isinstance(msg, HumanMessage) and not isinstance(msg, SystemMessage)
                        and not isinstance(msg, AIMessage)]
        
        system_messages = [SystemMessage(content=system_prompt)]
        messages = system_messages + human_messages + ai_messages + other_messages
        
        for i, msg in enumerate(messages):
            msg_type = type(msg).__name__
            content = getattr(msg, 'content', None)
            has_tool_calls = hasattr(msg, 'tool_calls')
            print(f"[{i}] {msg_type} Input({name}): {'비어있음' if not content and not has_tool_calls else '내용 있음'}")
            
        message = illm.invoke(messages)
        if isinstance(message, AIMessage) and not message.content:
            print(f"message is empty({name})")
        
        return {
            "messages": [message]
        }
        
    agent_node = lambda state: create_agent_node(state, _llm, system_prompt=system_prompt)
    
    def delete_messages(state, last_message_count):
        messages = state["messages"]
        
        # 빈 메시지 필터링
        valid_messages = [msg for msg in messages if hasattr(msg, 'content') and msg.content or hasattr(msg, 'tool_calls')]
        
        if not valid_messages:
            # 유효한 메시지가 없으면 기본 메시지 생성
            if "company" in state:
                return {"messages": [HumanMessage(content=f"Analyze {state['company']} stock.")]}
            return {"messages": []}
        
        # 도구 호출 결과 및 중요 메시지 보존
        human_messages = [msg for msg in valid_messages if isinstance(msg, HumanMessage)]
        ai_messages = [msg for msg in valid_messages if isinstance(msg, AIMessage)]
        tool_messages = [msg for msg in valid_messages if hasattr(msg, 'tool_call_id')]
        
        # 보존할 메시지 결정
        keep_messages = []
        
        # 항상 최소 하나의 인간 메시지 유지
        if human_messages:
            keep_messages.append(human_messages[0])
            
        
        # 마지막 AI 메시지 유지 (내용이 있는 경우만)
        if ai_messages:
            for msg in reversed(ai_messages):
                if msg.content or hasattr(msg, 'tool_calls'):
                    keep_messages.append(msg)
                    break
        
        # 삭제할 메시지 결정
        to_remove = [msg for msg in messages if msg not in keep_messages]
        
        for i, msg in enumerate(keep_messages):
            msg_type = type(msg).__name__
            content = getattr(msg, 'content', None)
            has_tool_calls = hasattr(msg, 'tool_calls')
            print(f"[{i}] {msg_type} Keep_messages({name}): {'비어있음' if not content and not has_tool_calls else '내용 있음'} has_tool_calls: {has_tool_calls}")
        
        if to_remove:
            return {"messages": [RemoveMessage(id=msg.id) for msg in to_remove]}
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
    
    if has_tool:
        subgraph_builder.add_node("tools", tool_node)
    subgraph_builder.add_node("delete_messages", delete_messages_node)
    subgraph_builder.add_edge(START, "agent")
    if has_tool:
        subgraph_builder.add_conditional_edges("agent", my_tools_condition)
        subgraph_builder.add_edge("tools", "agent")
    subgraph = subgraph_builder.compile(name=name)
    
    return subgraph
