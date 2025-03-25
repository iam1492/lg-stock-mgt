import yfinance as yf
from langchain_core.tools import tool
from datetime import datetime, timedelta
import requests
import os
import finnhub
from cachetools import cached, LRUCache, TTLCache

@tool(description="Get Financial Statement")
def get_financial_statement(ticker: str):
    """
    Tool for getting financial statements from Yahoo Finance.
    The tool returns a dictionary of yearly and quaterly imcome statement, balance sheet, cash flow, etc.
    
    Input paramter:
    - ticker(type:str): The ticker of a company.
    """
    
    print(f"Getting financial statement for {ticker}...")
    _ticker = yf.Ticker(ticker)
    income_stmt = _ticker.income_stmt
    balance_sheet = _ticker.balance_sheet
    cash_flow = _ticker.cash_flow
    
    financial_statement = {
        "income_stmt": income_stmt,
        "balance_sheet": balance_sheet,
        "cash_flow": cash_flow
    }
    
    return financial_statement

@cached(cache=TTLCache(maxsize=1024, ttl=600))
def fetch_financial_data(ticker: str, days: int, timeframe: str, limit: int):
    today = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    api_key = os.environ["POLYGON_API_KEY"]
    
    url = f"https://api.polygon.io/vX/reference/financials?ticker={ticker}&filing_date.gte={start_date}&filing_date.lt={today}&limit={limit}&timeframe={timeframe}&apiKey={api_key}"
    
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to fetch data: {response.status_code}"}
    
@tool(description="Financial Statements From Polygon")
def financial_statements_from_polygon(ticker: str):
    """
    Get financial statements from Polygon.io API.
    
    Input paramter:
    - ticker: The ticker of a company.
    
    Returns:
    - financial_statements: Financial statements for last 3 years.
    - financial_statements_quaterly: Quaterly financial statements for last 3 years.
    """
    
    annual_3_years = fetch_financial_data(ticker, days=1095, timeframe="annual", limit=30)
    quaterly_3_years = fetch_financial_data(ticker, days=1095, timeframe="quarterly", limit=30)
    
    return {
        "financial_statements": annual_3_years,
        "financial_statements_quaterly": quaterly_3_years
    }

@tool(description="Stock News")
def stock_news(ticker: str):
    """Useful to get news about a stock.
    
    Args:
        ticker: The ticker of a company str
    
    """
    ticker = yf.Ticker(ticker)
    return ticker.news

@tool(description="Financial Statements from Finnhub")
def financial_statements_finnhub(ticker: str):
    """
    Get historical financial data for a stock ticker for last 3 years.
    This API is from Finnhub
    
    Input paramter:
    - ticker: The ticker of a company.
    
    Returns:
    - basic_financials: Basic financial data for a stock ticker.
    - financial_statements: Financial statements for last 3 years.
    - financial_statements_quaterly: Quaterly financial statements for last 3 years.
    """
    finnhub_client = finnhub.Client(api_key=os.environ["FINNHUB_API_KEY"])
    start_date = (datetime.now() - timedelta(days=1095)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    financial_data = _retrieve_financial_statements_finnhub(ticker, finnhub_client, start_date, end_date)
    
    return financial_data

@cached(cache=TTLCache(maxsize=1024, ttl=600))
def _retrieve_financial_statements_finnhub(ticker, finnhub_client, start_date, end_date):
    basic_financials = finnhub_client.company_basic_financials(ticker, 'all')
    
    params = {
        'symbol': ticker,
        'freq': 'annual',
        'to': end_date,
        'from': start_date
    }
    financial_statements_3_years = finnhub_client.financials_reported(**params)
    
    params_2 = {
        'symbol': ticker,
        'freq': 'quarterly',
        'to': end_date,
        'from': start_date
    }
    financial_statements_quaterly_3_years = finnhub_client.financials_reported(**params_2)
    
    financial_data = {
        "basic_financials": basic_financials,
        "financial_statements": financial_statements_3_years,
        "financial_statements_quaterly": financial_statements_quaterly_3_years
    }
    
    return financial_data