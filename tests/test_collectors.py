import json
from pathlib import Path

from quant_niche.collectors import dart, edgar

FIX = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def test_edgar_parse_maps_forms_to_kinds():
    evs = edgar.parse(load("edgar_search.json"))
    assert len(evs) == 3
    by_form = {e.form_type: e for e in evs}
    assert by_form["SC TO-I"].kind == "odd_lot_tender"
    assert by_form["DEFM14A"].kind == "merger_cash"
    assert by_form["N-2"].kind == "cef_liquidation"


def test_edgar_extracts_ticker_and_id():
    evs = edgar.parse(load("edgar_search.json"))
    acme = next(e for e in evs if e.form_type == "SC TO-I")
    assert acme.ticker == "ACME"
    assert acme.company == "Acme Industries Inc."
    assert acme.event_id == "us-edgar-0001193125-26-000111"
    assert acme.market == "US" and acme.source == "EDGAR"
    assert acme.state_hash  # finalize 됨


def test_dart_parse_filters_targets_only():
    evs = dart.parse(load("dart_list.json"))
    # 공개매수 + 합병 2건만, 분기보고서는 제외
    kinds = sorted(e.kind for e in evs)
    assert kinds == ["merger_cash", "odd_lot_tender"]


def test_dart_fields_and_id():
    evs = dart.parse(load("dart_list.json"))
    pub = next(e for e in evs if e.kind == "odd_lot_tender")
    assert pub.ticker == "005930"
    assert pub.company == "가나기업"
    assert pub.filed_at == "2026-05-30"
    assert pub.event_id == "kr-dart-20260530000111"
    assert pub.url and "rcpNo=20260530000111" in pub.url


def test_dart_classify():
    assert dart.classify_report("공개매수신고서") == "odd_lot_tender"
    assert dart.classify_report("주요사항보고서(회사합병결정)") == "merger_cash"
    assert dart.classify_report("자기주식소각결정") == "forced_burn"
    assert dart.classify_report("분기보고서") is None
