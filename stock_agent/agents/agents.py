from tools.custom_tools import (
    stock_news, financial_statements_from_polygon, financial_statements_finnhub,
    stock_price_1m, stock_price_1y, simple_moving_average, relative_strength_index
)
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from utils.agent_util import create_agent
from prompt.system_prompts import (
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

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro-exp-03-25",
    max_tokens=50000,
    timeout=None,
    max_retries=2
)

researcher = lambda state: create_agent(
    llm=llm, 
    tools=[stock_news, tavily_search_tool],
    system_prompt=PromptTemplate.from_template(stock_researcher_prompt).format(company=state["company"]),
    last_message_count_to_transmission=1,
    name="Researcher")

financial_analyst = lambda state: create_agent(
    llm = llm, 
    tools=[financial_statements_from_polygon],
    system_prompt=stock_fianacial_analyst_1_prompt.format(company=state["company"]),
    last_message_count_to_transmission=1,
    name="Financial Analyst")

financial_analyst_2 = lambda state: create_react_agent(
    model=llm,
    tools=[financial_statements_finnhub],
    prompt=PromptTemplate.from_template(stock_financial_analyst_2_prompt).format(company=state["company"]),
    name="Financial Analyst 2"
)

financial_advisor = lambda state: create_agent(
    llm=llm,
    tools=[],
    system_prompt=stock_financial_advisor_prompt.format(company=state["company"]),
    last_message_count_to_transmission=3,
    name="Financial Advisor"
)

technical_analyst = lambda state: create_agent(
    llm=llm,
    tools=[stock_price_1m, stock_price_1y, simple_moving_average, relative_strength_index],
    system_prompt=technical_analyst_prompt.format(company=state["company"]),
    last_message_count_to_transmission=1,
    name="Technical Analyst"
)

hedge_fund_manager = lambda state: create_agent(
    llm=llm,
    tools=[],
    system_prompt=hedge_fund_manager_prompt.format(company=state["company"]),
    last_message_count_to_transmission=1,
    name="Hedge Fund Manager"
)

