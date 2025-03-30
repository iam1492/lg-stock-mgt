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

@cached(cache=TTLCache(maxsize=1024, ttl=3600))
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

@tool
def get_basic_financials(ticker: str):
    """Get basic financial data for a company."""
    finnhub_client = finnhub.Client(api_key=os.environ["FINNHUB_API_KEY"])
    return _get_basic_financials(ticker, finnhub_client)

@tool
def get_annual_financial_statements(ticker: str):
    """Get annual financial statements for a company."""
    finnhub_client = finnhub.Client(api_key=os.environ["FINNHUB_API_KEY"])
    start_date = (datetime.now() - timedelta(days=1095)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    return _get_annual_financial_statements(ticker, finnhub_client, start_date, end_date)

@tool
def get_quarterly_financial_statements(ticker: str):
    """Get quarterly financial statements for a company."""
    finnhub_client = finnhub.Client(api_key=os.environ["FINNHUB_API_KEY"])
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    return _get_quarterly_financial_statements(ticker, finnhub_client, start_date, end_date)

@cached(cache=TTLCache(maxsize=1024, ttl=3600))
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

@cached(cache=TTLCache(maxsize=1024, ttl=3600))
def _get_basic_financials(ticker, finnhub_client):
    """Get basic financial data for a company."""
    return finnhub_client.company_basic_financials(ticker, 'all')

@cached(cache=TTLCache(maxsize=1024, ttl=3600))
def _get_annual_financial_statements(ticker, finnhub_client, start_date, end_date):
    """Get annual financial statements for a company."""
    params = {
        'symbol': ticker,
        'freq': 'annual',
        'to': end_date,
        'from': start_date
    }
    return finnhub_client.financials_reported(**params)

@cached(cache=TTLCache(maxsize=1024, ttl=3600))
def _get_quarterly_financial_statements(ticker, finnhub_client, start_date, end_date):
    """Get quarterly financial statements for a company."""
    params = {
        'symbol': ticker,
        'freq': 'quarterly',
        'to': end_date,
        'from': start_date
    }
    return finnhub_client.financials_reported(**params)

@tool(description="Stock Price - last 1 Month")
def stock_price_1m(ticker: str):
    """Useful to get stock price data for the last month.
    
    Input paramter:
    - ticker: The ticker of a company.
    """
    ticker = yf.Ticker(ticker)
    return ticker.history(period="1mo")

@tool(description="Stock Price - last 1 Year")
def stock_price_1y(ticker: str):
    """
    Useful to get stock price data for the last year.
    
    Input paramters:
    - ticker: The ticker of a company.
    """
    ticker = yf.Ticker(ticker)
    return ticker.history(period="1y")

@cached(cache=TTLCache(maxsize=1024, ttl=3600))
def fetch_technical_indicator(ticker: str, timespan: str, window_size: int, limit: int, type: str):
    api_key = os.environ["POLYGON_API_KEY"]
    url = f"https://api.polygon.io/v1/indicators/{type}/{ticker}?timespan={timespan}&adjusted=true&window={window_size}&series_type=close&order=desc&limit={limit}&apiKey={api_key}"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to fetch data: {response.status_code}"}

@tool(description="Simple Moving Average")
def simple_moving_average(ticker: str, timespan: str, window_size: int, limit: int):
    """
    Get historical simple moving average data for a stock ticker.
    
    The input parameter of this tool is as follows:
    - ticker(type:str): The ticker of a company..
    - timespan(type:str): The size of the aggregate time window. Use one of [day, week, month, quarter, year].
    - window_size(type:int): The window size used to calculate the simple moving average (SMA). i.e. a window size of 30 with daily aggregates would result in a 30 day moving average.
    - limit(type:int): Limit the number of results returned.(maximum 5000)
    Usage Example: simple_moving_average("AAPL", "month", 14, 100)
    
    The output of this tool offer the simple moving average json object which contains list of simple moving average.
    """
    _timespan = validate_timespan(timespan)
    return fetch_technical_indicator(ticker, _timespan, window_size, limit, "sma")

@tool(description="Relative Strength Index")
def relative_strength_index(ticker: str, timespan: str, window_size: int, limit: int):
    """
    Get historical relative strength index data for a stock ticker.
    
    The input parameter of this tool is as follows:
    - ticker(type:str): ticker of a company..
    - timespan(type:str): The size of the aggregate time window. Use one of [day, week, month, quarter, year].
    - window_size(type:int): The window size used to calculate the relative strength index (RSI). i.e. a window size of 30 with daily aggregates would result in a 30 day RSI.
    - limit(type:int): Limit the number of results returned.(maximum 5000)
    Usage Example: relative_strength_index("AAPL", "month", 14, 100)
    
    The output of this tool offer the relative strength index json object which contains list of relative strength index.
    """
    _timespan = validate_timespan(timespan)
    return fetch_technical_indicator(ticker, _timespan, window_size, limit, "rsi")

def validate_timespan(timespan: str) -> str:
    new_timespan = timespan
    # 입력 timespan 값 검증 및 수정
    valid_timespans = ["day", "week", "month", "quarter", "year"]
    timespan_mapping = {
        "1d": "day", "d": "day", "daily": "day",
        "1w": "week", "w": "week", "weekly": "week",
        "1m": "month", "m": "month", "monthly": "month",
        "1q": "quarter", "q": "quarter", "quarterly": "quarter",
        "1y": "year", "y": "year", "yearly": "year", "annual": "year"
    }
    
    if timespan not in valid_timespans:
        if timespan.lower() in timespan_mapping:
            new_timespan = timespan_mapping[timespan.lower()]
            print(f"Timespan 값이 자동으로 '{new_timespan}'으로 변환되었습니다.")
        else:
            print(f"경고: 유효하지 않은 timespan 값 '{timespan}'입니다. 'day', 'week', 'month', 'quarter', 'year' 중 하나를 사용해야 합니다.")
            # 기본값으로 설정하거나 오류 처리
            new_timespan = "month"
            print(f"기본값 '{timespan}'으로 진행합니다.")
    return new_timespan

@tool(description="Expectations Investing")
def calculate_intrinsic_value_dcf_v2(
    current_fcff: float,          # 현재(또는 예측 시작점) FCFF (특정 통화 단위)
    growth_rates_forecast: list,  # 예측 기간 동안의 연간 FCFF 성장률 리스트 (예: [0.10, 0.08, 0.06])
    terminal_growth_rate: float,  # 영구 성장률 (보통 장기 경제 성장률 이하)
    wacc: float,                  # 가중평균자본비용 (할인율, 예: 0.09)
    total_debt: float,            # 총 부채 (current_fcff와 동일한 통화 단위)
    cash_and_equivalents: float,  # 현금 및 현금성 자산 (current_fcff와 동일한 통화 단위)
    shares_outstanding: float     # 실제 총 발행 주식 수 (단위 없음, 예: 10,000,000)
) -> float:
    """
    다단계 FCFF 할인 모델을 사용하여 주식의 주당 내재가치를 계산합니다.

    **단위 일관성 중요:**
    - `current_fcff`, `total_debt`, `cash_and_equivalents`는 반드시 **동일한 통화 단위**로 입력해야 합니다.
      (예: 모두 '원' 단위, 또는 모두 '억원' 단위, 또는 모두 '백만 달러' 단위)
    - `shares_outstanding`은 반드시 **실제 총 발행 주식 수** (숫자)로 입력해야 합니다. (예: 10,000,000)
    - 반환되는 주당 내재가치의 단위는 입력된 통화 단위와 동일합니다.
      (예: 금전 입력을 '원'으로 했다면 결과는 '원/주', '억원'으로 했다면 '억원/주')

    Args:
        current_fcff: 현재 또는 예측 시작점의 FCFF.
        growth_rates_forecast: 예측 기간 동안의 연간 FCFF 성장률 리스트.
        terminal_growth_rate: 예측 기간 이후의 영구 성장률.
        wacc: 가중평균자본비용 (할인율). 예: 10% -> 0.10
        total_debt: 회사의 총 부채. (current_fcff와 동일 단위)
        cash_and_equivalents: 회사의 현금 및 현금성 자산. (current_fcff와 동일 단위)
        shares_outstanding: 실제 총 발행 주식 수 (단위 없는 숫자).

    Returns:
        계산된 주당 내재가치 (입력된 통화 단위 기준).

    Raises:
        ValueError: WACC가 영구 성장률보다 작거나 같으면 계산할 수 없습니다.
        ValueError: shares_outstanding이 0보다 작거나 같으면 계산할 수 없습니다.
    """

    if wacc <= terminal_growth_rate:
        raise ValueError("WACC는 영구 성장률(terminal_growth_rate)보다 커야 합니다.")
    if shares_outstanding <= 0:
        raise ValueError("발행 주식 수(shares_outstanding)는 0보다 커야 합니다.")

    forecast_years = len(growth_rates_forecast)
    projected_fcff = []
    last_fcff = current_fcff

    # 1. 예측 기간 동안의 FCFF 계산
    print("\n--- FCFF 예측 ---")
    for i in range(forecast_years):
        next_fcff = last_fcff * (1 + growth_rates_forecast[i])
        projected_fcff.append(next_fcff)
        print(f"Year {i+1} FCFF: {next_fcff:,.2f} (Growth: {growth_rates_forecast[i]:.2%})") # 천 단위 쉼표 추가
        last_fcff = next_fcff

    # 2. 예측 기간 FCFF의 현재가치(PV) 계산
    pv_forecast_fcff = 0
    print("\n--- 예측 기간 FCFF 현재가치 계산 ---")
    for i in range(forecast_years):
        discount_factor = (1 + wacc) ** (i + 1)
        pv = projected_fcff[i] / discount_factor
        pv_forecast_fcff += pv
        print(f"Year {i+1} PV(FCFF): {pv:,.2f} (Discount Factor: {discount_factor:.4f})")
    print(f"예측 기간 FCFF의 총 현재가치: {pv_forecast_fcff:,.2f}")

    # 3. 영구 가치(Terminal Value) 계산
    terminal_fcff = last_fcff * (1 + terminal_growth_rate)
    terminal_value = terminal_fcff / (wacc - terminal_growth_rate)
    print("\n--- 영구 가치 계산 ---")
    print(f"Terminal Year FCFF (Year {forecast_years+1} estimate): {terminal_fcff:,.2f}")
    print(f"Terminal Value at Year {forecast_years}: {terminal_value:,.2f}")

    # 4. 영구 가치의 현재가치 계산
    pv_terminal_value = terminal_value / ((1 + wacc) ** forecast_years)
    print(f"영구 가치의 현재가치(PV): {pv_terminal_value:,.2f} (Discount Factor: {(1 + wacc) ** forecast_years:.4f})")

    # 5. 기업 가치(Enterprise Value) 계산
    enterprise_value = pv_forecast_fcff + pv_terminal_value
    print("\n--- 기업 가치 및 주당 내재가치 계산 ---")
    print(f"총 기업 가치 (Enterprise Value): {enterprise_value:,.2f}")

    # 6. 자기자본 가치(Equity Value) 계산
    equity_value = enterprise_value - total_debt + cash_and_equivalents
    print(f"자기자본 가치 (Equity Value): {equity_value:,.2f} (EV - Debt + Cash)")

    # 7. 주당 내재가치 계산
    intrinsic_value_per_share = equity_value / shares_outstanding
    # 결과 출력 시 주당 가치가 너무 작거나 크면 지수 표기법이 나올 수 있으므로 f-string 포맷팅 개선
    print(f"발행 주식 수: {shares_outstanding:,.0f}")
    print(f"주당 내재가치: {intrinsic_value_per_share:,.2f} (입력된 통화 단위 기준)")

    return intrinsic_value_per_share

"""
# --- 예제 사용법 (단위를 '원'으로 통일) ---
# 실제 분석 시에는 해당 기업의 정확한 데이터를 사용해야 합니다.

# 가정: 모든 금전 단위는 '원' (KRW)
current_fcff_example_krw = 100_000_000_000  # 1000억원
growth_forecast_example = [0.15, 0.12, 0.10, 0.08, 0.06] # 5년간 성장률 예측
terminal_growth_example = 0.025 # 영구 성장률 2.5%
wacc_example = 0.09           # WACC 9%
debt_example_krw = 500_000_000_000          # 총 부채 5000억원
cash_example_krw = 50_000_000_000           # 현금 500억원
shares_example_count = 10_000_000         # 실제 발행 주식 수 10,000,000주

print("="*40)
print("예제 내재가치 계산 시작 (단위: 원, 주)")
print("="*40)

try:
    intrinsic_value = calculate_intrinsic_value_dcf_v2(
        current_fcff=current_fcff_example_krw,
        growth_rates_forecast=growth_forecast_example,
        terminal_growth_rate=terminal_growth_example,
        wacc=wacc_example,
        total_debt=debt_example_krw,
        cash_and_equivalents=cash_example_krw,
        shares_outstanding=shares_example_count
    )
    print("\n" + "="*40)
    # 결과는 '원/주' 단위로 나옴
    print(f"계산된 주당 내재가치: {intrinsic_value:,.2f} 원/주")
    print("="*40)

    # 이전 예제와 비교:
    # 이전 예제에서는 입력 단위를 '억원', '백만주'로 혼용하여 결과가 '만원/주'로 나왔었음.
    # (1150.15 억원 / 10 백만주 = 11.5015 만원/주)
    # 현재 예제에서는 입력을 '원', '주'로 통일하여 결과가 '원/주'로 나옴.
    # (11,501,519,366,498.89 원 / 10,000,000 주 = 115,015.19 원/주)
    # 값은 동일하며 단위만 명확해짐.

except ValueError as e:
    print(f"\n오류 발생: {e}")
except Exception as e:
    print(f"\n예상치 못한 오류 발생: {e}")
    
"""

def calculate_capm(
    risk_free_rate: float,    # 무위험 수익률 (예: 국채 금리)
    beta: float,              # 주식의 베타 값
    market_risk_premium: float # 시장 위험 프리미엄 (Expected Market Return - Risk-Free Rate)
) -> float:
    """
    CAPM(Capital Asset Pricing Model)을 사용하여 자기자본비용(Cost of Equity)을 계산합니다.

    Args:
        risk_free_rate: 무위험 수익률 (소수점 형태, 예: 3% -> 0.03).
        beta: 해당 주식의 베타 값.
        market_risk_premium: 시장 위험 프리미엄 (소수점 형태, 예: 5% -> 0.05).

    Returns:
        계산된 자기자본비용 (Cost of Equity) (소수점 형태).
    """
    if beta < 0:
        print("Warning: Beta is negative. This is unusual but calculation will proceed.")
        # 음수 베타도 이론적으로는 가능하나, 실제로는 드뭅니다.

    cost_of_equity = risk_free_rate + beta * market_risk_premium
    return cost_of_equity

@tool(description="calculate_wacc")
def calculate_wacc(
    market_cap_equity: float,  # 자기자본의 시장가치 (시가총액)
    market_value_debt: float,  # 타인자본(부채)의 시장가치 (보통 장부가치 이자 발생 부채 사용)
    cost_of_equity: float,     # 자기자본비용 (Re, 소수점 형태, 예: 0.10) - CAPM 등으로 계산
    cost_of_debt: float,       # 타인자본비용 (Rd, 세전 평균 이자율, 소수점 형태, 예: 0.05)
    tax_rate: float            # 법인세율 (Tc, 소수점 형태, 예: 0.25)
) -> float:
    """
    WACC(가중평균자본비용)를 계산합니다.

    **단위 일관성:**
    - `market_cap_equity`와 `market_value_debt`는 동일한 통화 단위여야 합니다.

    Args:
        market_cap_equity: 자기자본의 시장가치 (시가총액).
        market_value_debt: 타인자본(부채)의 시장가치.
                           (주의: 실제 시장가치를 알기 어려워, 이자 발생 부채의 장부가치를
                            사용하는 경우가 많습니다.)
        cost_of_equity: 자기자본비용 (Cost of Equity), 보통 CAPM으로 계산 (소수점).
        cost_of_debt: 세전 타인자본비용 (Cost of Debt), 회사의 평균 차입 이자율 (소수점).
        tax_rate: 유효 법인세율 (소수점).

    Returns:
        계산된 WACC (가중평균자본비용) (소수점 형태).

    Raises:
        ValueError: 총 기업 가치(V)가 0 이하일 경우.
        ValueError: 세율이 0 미만이거나 1 초과일 경우.
    """

    # 입력 값 검증
    if market_cap_equity < 0 or market_value_debt < 0:
        raise ValueError("자기자본 및 타인자본 가치는 0 이상이어야 합니다.")
    if not (0 <= tax_rate <= 1):
        raise ValueError("세율은 0과 1 사이의 값이어야 합니다 (예: 25% -> 0.25).")
    if cost_of_equity < 0 or cost_of_debt < 0:
        print("Warning: cost_of_equity 또는 cost_of_debt가 음수입니다. 계산은 진행되지만 확인이 필요합니다.")


    # 총 기업 가치 계산
    total_value = market_cap_equity + market_value_debt

    if total_value <= 0:
        # 자기자본과 부채가 모두 0인 경우는 거의 없지만, 에러 방지
        raise ValueError("총 기업 가치(자기자본 + 타인자본)는 0보다 커야 합니다.")

    # 자기자본과 타인자본의 가중치 계산
    weight_equity = market_cap_equity / total_value
    weight_debt = market_value_debt / total_value # 또는 1 - weight_equity

    # 세후 타인자본비용 계산
    after_tax_cost_of_debt = cost_of_debt * (1 - tax_rate)

    # WACC 계산
    wacc = (weight_equity * cost_of_equity) + (weight_debt * after_tax_cost_of_debt)

    print("\n--- WACC 계산 상세 ---")
    print(f"자기자본 시장가치 (E): {market_cap_equity:,.2f}")
    print(f"타인자본 시장가치 (D): {market_value_debt:,.2f}")
    print(f"총 기업 가치 (V = E + D): {total_value:,.2f}")
    print(f"자기자본 가중치 (E/V): {weight_equity:.4f}")
    print(f"타인자본 가중치 (D/V): {weight_debt:.4f}")
    print(f"자기자본비용 (Re): {cost_of_equity:.4f}")
    print(f"세전 타인자본비용 (Rd): {cost_of_debt:.4f}")
    print(f"법인세율 (Tc): {tax_rate:.4f}")
    print(f"세후 타인자본비용 (Rd * (1-Tc)): {after_tax_cost_of_debt:.4f}")
    print(f"WACC = (E/V * Re) + (D/V * Rd * (1-Tc))")
    print(f"     = ({weight_equity:.4f} * {cost_of_equity:.4f}) + ({weight_debt:.4f} * {after_tax_cost_of_debt:.4f})")
    print(f"     = {weight_equity * cost_of_equity:.4f} + {weight_debt * after_tax_cost_of_debt:.4f}")
    print(f"     = {wacc:.4f}")

    return wacc

"""
# --- 예제 사용법 ---

# 1. 자기자본비용(Cost of Equity) 계산 (CAPM 사용 예시)
risk_free_rate_example = 0.03  # 무위험 수익률 3%
beta_example = 1.2             # 베타 1.2
market_risk_premium_example = 0.05 # 시장 위험 프리미엄 5%

cost_of_equity_calculated = calculate_capm(
    risk_free_rate=risk_free_rate_example,
    beta=beta_example,
    market_risk_premium=market_risk_premium_example
)
print(f"--- CAPM 계산 결과 ---")
print(f"계산된 자기자본비용 (Cost of Equity): {cost_of_equity_calculated:.4f} ({cost_of_equity_calculated:.2%})")

# 2. WACC 계산 (위에서 계산된 자기자본비용 사용)
# 가정: 모든 금전 단위는 '억원'
market_cap_example = 1500.0  # 시가총액 1500억원
debt_value_example = 500.0   # 이자 발생 부채 500억원 (시장가치 대신 장부가치 사용 가정)
cost_of_debt_example = 0.045 # 평균 차입 이자율 4.5%
tax_rate_example = 0.22      # 법인세율 22%

print("\n" + "="*40)
print("WACC 계산 시작")
print("="*40)

try:
    wacc_calculated = calculate_wacc(
        market_cap_equity=market_cap_example,
        market_value_debt=debt_value_example,
        cost_of_equity=cost_of_equity_calculated, # CAPM 결과 사용
        cost_of_debt=cost_of_debt_example,
        tax_rate=tax_rate_example
    )
    print("\n" + "="*40)
    print(f"최종 계산된 WACC: {wacc_calculated:.4f} ({wacc_calculated:.2%})")
    print("="*40)

    # 이제 이 wacc_calculated 값을 이전의 DCF 함수 `calculate_intrinsic_value_dcf_v2`의
    # `wacc` 인자로 사용할 수 있습니다.

except ValueError as e:
    print(f"\n오류 발생: {e}")
except Exception as e:
    print(f"\n예상치 못한 오류 발생: {e}")
    
"""