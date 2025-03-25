
from dotenv import load_dotenv
from typing import TypedDict, Literal, Union
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import Annotated, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, AnyMessage
from tools.custom_tools import financial_statements_from_polygon
from langgraph.prebuilt import ToolNode, tools_condition, create_react_agent
from pydantic import BaseModel
from graph.display_graph import save_mermaid_as_png
from utils.agent_utils import create_agent_node
from prompt.system_prompts import stock_fianacial_analyst_1_prompt

load_dotenv()

# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.0-pro-exp-02-05",
#     max_tokens=50000,
#     timeout=None,
#     max_retries=2
# )

llm = ChatOpenAI (
    model= "gpt-4o-mini"
)

tools = [financial_statements_from_polygon]
financial_tool_node = ToolNode(tools)
llm_with_tool = llm.bind_tools(tools)

class SubState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    
financial_analyst = lambda state: create_agent_node(state, llm_with_tool, system_prompt=stock_fianacial_analyst_1_prompt)

def get_financial_analyst_subgraph():
    subgraph_builder = StateGraph(SubState)
    subgraph_builder.add_node("financial_analyst", financial_analyst)
    subgraph_builder.add_node("tools", financial_tool_node)
    subgraph_builder.add_edge(START, "financial_analyst")
    subgraph_builder.add_conditional_edges("financial_analyst", tools_condition)
    subgraph_builder.add_edge("tools", "financial_analyst")
    subgraph = subgraph_builder.compile()
    
    return subgraph

