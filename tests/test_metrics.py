import pytest

from quant_niche.metrics import (
    annualized_return,
    days_to_close,
    kelly_fraction,
    quarter_kelly,
    spread_pct,
)


def test_spread_pct():
    assert spread_pct(96.0, 100.0) == pytest.approx(4.1666, rel=1e-3)
    assert spread_pct(0, 100) is None
    assert spread_pct(100, None) is None


def test_days_to_close():
    assert days_to_close("2026-06-10", "2026-06-03") == 7
    assert days_to_close("", "2026-06-03") is None


def test_annualized():
    # 4% in 30 days ≈ 48.7%
    assert annualized_return(4.0, 30) == pytest.approx(48.666, rel=1e-3)
    assert annualized_return(4.0, 0) is None
    assert annualized_return(None, 30) is None


def test_kelly_quarter():
    f = kelly_fraction(0.9, 0.04, 0.30)
    assert f is not None and f > 0
    assert quarter_kelly(0.9, 0.04, 0.30) == pytest.approx(f / 4)
    # 음의 엣지 → 0 클램프
    assert quarter_kelly(0.5, 0.04, 0.30) == 0.0
