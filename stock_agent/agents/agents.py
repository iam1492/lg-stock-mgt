from tools.custom_tools import (
    stock_news, financial_statements_from_polygon, financial_statements_finnhub
)
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from prompt.system_prompts import (
    stock_researcher_prompt, 
    stock_fianacial_analyst_1_prompt,
    stock_financial_analyst_2_prompt, 
    stock_financial_advisor_prompt, 
    hedge_fund_manager_prompt
)

tavily_search_tool = TavilySearch(
    max_results=5,
    topic="finance"
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-pro-exp-02-05",
    max_tokens=50000,
    timeout=None,
    max_retries=2
)

researcher = lambda state: create_react_agent(
    model=llm, 
    tools=[stock_news, tavily_search_tool],
    prompt=PromptTemplate.from_template(stock_researcher_prompt).format(company=state["company"]),
    name="Researcher")

financial_analyst = lambda state: create_react_agent(
    model=llm,
    tools=[financial_statements_from_polygon],
    prompt=PromptTemplate.from_template(stock_fianacial_analyst_1_prompt).format(company=state["company"]),
    name="Financial Analyst"
)

financial_analyst_2 = lambda state: create_react_agent(
    model=llm,
    tools=[financial_statements_finnhub],
    prompt=PromptTemplate.from_template(stock_financial_analyst_2_prompt).format(company=state["company"]),
    name="Financial Analyst 2"
)

financial_advisor = lambda state: create_react_agent(
    model=llm,
    tools=[],
    prompt=PromptTemplate.from_template(stock_financial_advisor_prompt).format(company=state["company"]),
    name="Financial Advisor"
)

hedge_fund_manager = lambda state: create_react_agent(
    model=llm,
    tools=[],
    prompt=PromptTemplate.from_template(hedge_fund_manager_prompt).format(company=state["company"]),
    name="Hedge Fund Manager"
)