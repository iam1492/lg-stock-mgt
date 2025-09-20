from typing import Any, Sequence
from uuid import UUID

from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.documents import Document
from langgraph.prebuilt import create_react_agent
from langchain_core.outputs import LLMResult
from ..tools.custom_tools import ( # Use relative import
    stock_news, financial_statements_from_polygon, financial_statements_finnhub,
    stock_price_1m, stock_price_1y, simple_moving_average, relative_strength_index,
    get_basic_financials, get_annual_financial_statements, get_quarterly_financial_statements
)
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from ..utils.agent_util import create_agent_with_tool # Use relative import
from ..utils.openrouter import ChatOpenRouter # Use relative import
# Remove local handler imports
# from langchain.callbacks.base import BaseCallbackHandler
# from langchain.callbacks import StdOutCallbackHandler
# Removed import of get_callback_handler as it's no longer used here
from ..prompt.system_prompts import ( # Use relative import
    stock_researcher_prompt,
    stock_fianacial_analyst_1_prompt,
    stock_financial_analyst_2_prompt,
    stock_financial_advisor_prompt,
    technical_analyst_prompt,
    hedge_fund_manager_prompt,
)

tavily_search_tool = TavilySearch(
    max_results=5,
    topic="finance"
)

# --- Remove local CallbackHandler definition and old getters ---
# class CallbackHandler(BaseCallbackHandler):
#     ... (removed) ...
#
# _llm_instance = None
# _callback_handler_instance = None
#
# def get_callback_handler():
#     ... (removed) ...

_llm_instance = None # Keep LLM instance holder

def get_llm():
    """Gets or creates the LLM instance. Callbacks are added during graph execution."""
    global _llm_instance
    if _llm_instance is None:
        # Initialize LLM WITHOUT callbacks here.
        # Callbacks will be provided via config in graph.stream/astream.
        _llm_instance = ChatGoogleGenerativeAI(model="gemini-2.5-pro", timeout=None, max_retries=2)
        # _llm_instance = ChatDeepSeek(model="deepseek-chat", max_tokens=8192)
        # _llm_instance = ChatOpenAI(model="gpt-4o-mini", max_completion_tokens=16384)
        print("DEBUG: Initialized LLM (in agents.py - no callbacks here)")
    return _llm_instance
# --- End Refactored Initialization ---


researcher = lambda state: create_agent_with_tool( # Keep original indentation
    llm=get_llm(), # Use getter
    tools=[stock_news, tavily_search_tool],
    system_prompt=stock_researcher_prompt.format(company=state["company"]),
    last_message_count_to_transmission=1,
    name="Researcher")

financial_analyst = lambda state: create_agent_with_tool(
    llm = get_llm(), # Use getter
    tools=[financial_statements_from_polygon],
    system_prompt=stock_fianacial_analyst_1_prompt.format(company=state["company"]),
    last_message_count_to_transmission=1,
    name="Financial Analyst")

financial_analyst_2 = lambda state: create_agent_with_tool(
    llm=get_llm(), # Use getter
    tools=[get_basic_financials, get_quarterly_financial_statements, get_annual_financial_statements],
    system_prompt=stock_financial_analyst_2_prompt.format(company=state["company"]),
    last_message_count_to_transmission=1,
    name="Financial Analyst 2")

financial_advisor = lambda state: create_agent_with_tool(
    llm=get_llm(), # Use getter
    tools=[],
    system_prompt=stock_financial_advisor_prompt.format(company=state["company"]),
    last_message_count_to_transmission=1,
    name="Financial Advisor")

technical_analyst = lambda state: create_agent_with_tool(
    llm=get_llm(), # Use getter
    tools=[stock_price_1m, stock_price_1y, simple_moving_average, relative_strength_index],
    system_prompt=technical_analyst_prompt.format(company=state["company"]),
    last_message_count_to_transmission=1,
    name="Technical Analyst")


hedge_fund_manager = lambda state: create_agent_with_tool(
    llm=get_llm(), # Use getter
    tools=[],
    system_prompt=hedge_fund_manager_prompt.format(company=state["company"]),
    last_message_count_to_transmission=1,
    name="Hedge Fund Manager")
