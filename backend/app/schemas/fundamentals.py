from pydantic import BaseModel


class FundamentalsResponse(BaseModel):
    symbol: str
    # Valuation
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    ps_ratio: float | None = None
    ev_ebitda: float | None = None
    # Profitability
    roe: float | None = None
    roa: float | None = None
    net_margin: float | None = None
    gross_margin: float | None = None
    # Growth
    revenue_growth_yoy: float | None = None
    eps_growth_yoy: float | None = None
    # Dividends
    dividend_yield: float | None = None
    dividend_per_share: float | None = None
    # Balance
    debt_to_equity: float | None = None
    current_ratio: float | None = None
    # Price
    week_52_high: float | None = None
    week_52_low: float | None = None
    beta: float | None = None