"""가격 스냅샷 — Stooq CSV(키 불필요, urllib). yfinance 의존 회피.

추적 중 딜의 현재가를 받아 스프레드·연율화를 *코드로* 계산해 ledger 에
채운다(LLM 토큰 0). 네트워크 막힌 환경에선 None 반환.
"""

from __future__ import annotations

from .collectors.base import NetworkError, http_get
from .metrics import annualized_return, days_to_close, spread_pct

STOOQ_URL = "https://stooq.com/q/l/?s={sym}&f=sd2t2ohlcv&h&e=csv"


def _stooq_symbol(ticker: str, market: str) -> str:
    t = ticker.lower()
    if market == "US":
        return f"{t}.us"
    if market == "KR":
        # 코스피/코스닥 구분 없이 Stooq 는 .kr 접미사 사용(종목코드 기준)
        return f"{t}.kr"
    return t


def last_price(ticker: str, market: str, *, user_agent: str = "quant-niche") -> float | None:
    """Stooq 일별 마지막 종가. 실패/비가용 시 None."""
    if not ticker:
        return None
    url = STOOQ_URL.format(sym=_stooq_symbol(ticker, market))
    try:
        body = http_get(url, user_agent=user_agent, accept="text/csv")
    except NetworkError:
        return None
    lines = [ln for ln in body.splitlines() if ln.strip()]
    if len(lines) < 2:
        return None
    header = [h.strip().lower() for h in lines[0].split(",")]
    row = lines[1].split(",")
    try:
        close = row[header.index("close")].strip()
        return float(close)
    except (ValueError, IndexError):
        return None


def enrich_spread(event, *, asof: str | None = None, user_agent: str = "quant-niche"):
    """Event 에 현재가 기반 spread_pct/annualized 를 채워 반환.

    deal_price/ticker/deadline 이 있어야 의미가 있다. 없으면 무변경.
    """
    if event.deal_price is None or not event.ticker:
        return event
    px = last_price(event.ticker, event.market, user_agent=user_agent)
    if px is None:
        return event
    sp = spread_pct(px, event.deal_price)
    event.spread_pct = round(sp, 3) if sp is not None else None
    d = days_to_close(event.deadline, asof) if event.deadline else None
    ann = annualized_return(sp, d)
    event.annualized = round(ann, 2) if ann is not None else None
    return event
