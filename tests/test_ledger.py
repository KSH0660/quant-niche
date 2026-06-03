from quant_niche.ledger import Event, EventLedger


def mk(event_id="e1", deal_price=10.0, status="new"):
    return Event(
        event_id=event_id, market="US", source="EDGAR", form_type="DEFM14A",
        kind="merger_cash", ticker="ABC", deal_price=deal_price, status=status,
    ).finalize()


def test_hash_stable_and_excludes_tracking_meta():
    a = mk(status="new")
    b = mk(status="tracked")  # status 는 해시에 미포함
    assert a.state_hash == b.state_hash
    c = mk(deal_price=11.0)  # deal_price 는 해시에 포함 → 달라야
    assert a.state_hash != c.state_hash


def test_diff_new_changed_unchanged():
    led = EventLedger([mk(deal_price=10.0)])
    incoming = [mk(deal_price=10.0), mk("e2"), mk(deal_price=12.0)]
    # e1 동일가 → unchanged, e1 12.0 도 같은 id라 마지막이 changed 판정 대상
    d = led.diff([mk(deal_price=10.0)])
    assert len(d.unchanged) == 1 and not d.new and not d.changed

    d2 = led.diff([mk("e2"), mk(deal_price=12.0)])
    assert len(d2.new) == 1  # e2
    assert len(d2.changed) == 1  # e1 가격 변동
    assert d2.actionable and len(d2.actionable) == 2


def test_merge_preserves_judgment_meta():
    led = EventLedger([mk(deal_price=10.0, status="tracked")])
    led.get("e1").idea_file = "research/ideas/011-x.md"
    d = led.diff([mk(deal_price=12.0)])  # 사실(가격) 변동
    led.merge(d)
    merged = led.get("e1")
    assert merged.deal_price == 12.0  # 사실은 갱신
    assert merged.status == "tracked"  # 판단 메타는 보존
    assert merged.idea_file == "research/ideas/011-x.md"


def test_jsonl_roundtrip(tmp_path):
    p = tmp_path / "events.jsonl"
    led = EventLedger([mk(), mk("e2")])
    led.save(p)
    again = EventLedger.load(p)
    assert len(again) == 2
    assert again.get("e1").state_hash == led.get("e1").state_hash


def test_load_missing_file_returns_empty(tmp_path):
    assert len(EventLedger.load(tmp_path / "nope.jsonl")) == 0
