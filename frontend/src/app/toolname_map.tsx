export class ToolNameMapper {
    private mapping: Record<string, string>;

    constructor(ticker: string) {
        this.mapping = {
            "get_financial_statement": `${ticker} 재무재표 분석`,
            "financial_statements_from_polygon": `${ticker} 재무재표 불러오기`,
            "simple_moving_average": `${ticker} 차트 기술적 분석`, 
            "stock_news": `${ticker} 관련 뉴스 분석`, 
            "financial_statements_finnhub": `${ticker} 재무재표 분석`,
            "get_basic_financials": `${ticker} 기본 정보 분석`,
            "get_annual_financial_statements": `${ticker} 연간 재무재표 분석`,
            "get_quarterly_financial_statements": `${ticker} 분기 재무재표 분석`,
            "stock_price_1m": `${ticker} 1달간 주가 정보 분석`,
            "stock_price_1y": `${ticker} 1년간 주가 정보 분석`,
            "relative_strength_index" : `${ticker} 차트 기술 분석`,
        };
    }

    getMapping(key: string): string | undefined {
        return this.mapping[key];
    }
}
