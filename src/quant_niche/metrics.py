"""차익 지표 계산 — 전부 결정론 코드(LLM 토큰 0).

스프레드/연율화/잔여일수/켈리는 산술이므로 절대 LLM에 시키지 않는다
(reports/01 §1 책임 경계).
"""

from __future__ import annotations

from datetime import date, datetime


def _parse_date(d: str | date) -> date:
    if isinstance(d, date):
        return d
    return datetime.strptime(d, "%Y-%m-%d").date()


def days_to_close(deadline: str | date, asof: str | date | None = None) -> int | None:
    """확정 종료일까지 남은 일수. deadline 미정이면 None."""
    if not deadline:
        return None
    end = _parse_date(deadline)
    today = _parse_date(asof) if asof else date.today()
    return (end - today).days


def spread_pct(price: float, deal_price: float) -> float | None:
    """현재가 대비 인수가까지의 차익(%) = (deal/price - 1) * 100.

    양수면 인수가가 더 높음(롱 차익 여지). 음수면 프리미엄 초과 거래.
    """
    if not price or price <= 0 or deal_price is None:
        return None
    return (deal_price / price - 1.0) * 100.0


def annualized_return(spread_percent: float | None, days: int | None) -> float | None:
    """잔여 기간 스프레드를 단순 연율화(%) — 365/days 선형.

    deal-break 확률을 반영하지 않은 *총* 연율이다(음의 왜도 미차감).
    실제 기대수익은 friction-capacity 층에서 파산확률·비용을 차감해 구한다.
    """
    if spread_percent is None or not days or days <= 0:
        return None
    return spread_percent * (365.0 / days)


def kelly_fraction(p_win: float, gain: float, loss: float) -> float | None:
    """켈리 비중 f* = p/loss - (1-p)/gain (배당률 표기).

    gain = 성공 시 수익률(예: 0.04), loss = 실패 시 손실률(예: 0.30, 양수).
    헌법상 실제 사이징은 이 값의 1/4 이하로 제한한다.
    """
    if gain <= 0 or loss <= 0 or not (0.0 <= p_win <= 1.0):
        return None
    f = p_win / loss - (1.0 - p_win) / gain
    return f


def quarter_kelly(p_win: float, gain: float, loss: float) -> float | None:
    """헌법 기본 사이징: 켈리 1/4 (음수면 0으로 클램프)."""
    f = kelly_fraction(p_win, gain, loss)
    if f is None:
        return None
    return max(0.0, f / 4.0)
