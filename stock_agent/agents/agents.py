from typing import Any
from uuid import UUID

from langchain_core.agents import AgentAction, AgentFinish
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
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks import StdOutCallbackHandler
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

class CallbackHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized: dict[str, Any], prompts: list[str], *, run_id: UUID, parent_run_id: UUID | None = None, tags: list[str] | None = None, metadata: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        print("----------------------------------")
        print("[Callback] on_llm_start:", str(serialized)[:50])
    
    def on_llm_end(self, response: LLMResult, *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any) -> Any:
        print("----------------------------------")
        print("[Callback] on_llm_end:", str(response.llm_output)[:50])
        
    def on_chat_model_start(self, serialized, messages, **kwargs):
        print("----------------------------------")
        print("[Callback] Chat model start:", str(messages)[:50])
        
    def on_chat_model_end(self, response, **kwargs):
        print("----------------------------------")
        print("[Callback] Chat model end:", str(response)[:50])
        
    
    def on_tool_start(self, serialized: dict[str, Any], input_str: str, *, run_id: UUID, parent_run_id: UUID | None = None, tags: list[str] | None = None, metadata: dict[str, Any] | None = None, inputs: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        print("----------------------------------")
        print("[Callback] on_tool_start:", str(serialized)[:10])
        
    
    def on_tool_end(self, output: Any, *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any) -> Any:
        print("----------------------------------")
        print("[Callback] on_tool_end:", str(output)[:10])
        
    
    def on_agent_action(self, action: AgentAction, *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any) -> Any:
        print("----------------------------------")
        print(f"[Callback] on_agent_action: tool: {str(action.tool)[:10]} input: {str(action.tool_input)[:10]}")
        
        
    def on_agent_finish(self, finish: AgentFinish, *, run_id: UUID, parent_run_id: UUID | None = None, **kwargs: Any) -> Any:
        print("----------------------------------")
        print("[Callback] on_agent_finish:", str(finish.return_values)[:10])
        
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-pro-exp-03-25",
#     timeout=None,
#     max_retries=2,
#     callbacks=[CallbackHandler()]
# )
llm = ChatDeepSeek(model="deepseek-chat", max_tokens=8192)#,callbacks=[CallbackHandler()])

# llm = ChatOpenAI(model="gpt-4o-mini", max_completion_tokens=16384)

researcher = lambda state: create_agent_with_tool(
    llm=llm, 
    tools=[stock_news, tavily_search_tool],
    system_prompt=stock_researcher_prompt.format(company=state["company"]),
    last_message_count_to_transmission=1,
    name="Researcher")

financial_analyst = lambda state: create_agent_with_tool(
    llm = llm, 
    tools=[financial_statements_from_polygon],
    system_prompt=stock_fianacial_analyst_1_prompt.format(company=state["company"]),
    last_message_count_to_transmission=1,
    name="Financial Analyst")

# financial_analyst_2 = lambda state: create_react_agent(
#     model=llm,
#     tools=[financial_statements_finnhub],
#     prompt=PromptTemplate.from_template(stock_financial_analyst_2_prompt).format(company=state["company"]),
#     name="Financial Analyst 2"
# )

financial_analyst_2 = lambda state: create_agent_with_tool(
    llm=llm,
    tools=[get_basic_financials, get_quarterly_financial_statements, get_annual_financial_statements],
    system_prompt=stock_financial_analyst_2_prompt.format(company=state["company"]),
    last_message_count_to_transmission=1,
    name="Financial Analyst 2"
)

financial_advisor = lambda state: create_agent_with_tool(
    llm=llm,
    tools=[],
    system_prompt=stock_financial_advisor_prompt.format(company=state["company"]),
    last_message_count_to_transmission=1,
    name="Financial Advisor"
)

# financial_advisor = lambda state: create_react_agent(
#     model=llm,
#     tools=[],
#     prompt=PromptTemplate.from_template(stock_financial_advisor_prompt).format(company=state["company"]),
#     name="Financial Advisor"
# )

technical_analyst = lambda state: create_agent_with_tool(
    llm=llm,
    tools=[stock_price_1m, stock_price_1y, simple_moving_average, relative_strength_index],
    system_prompt=technical_analyst_prompt.format(company=state["company"]),
    last_message_count_to_transmission=1,
    name="Technical Analyst"
)


hedge_fund_manager = lambda state: create_agent_with_tool(
    llm=llm,
    tools=[],
    system_prompt=hedge_fund_manager_prompt.format(company=state["company"]),
    last_message_count_to_transmission=1,
    name="Hedge Fund Manager"
)
