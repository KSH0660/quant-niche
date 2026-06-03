"""Layer 0 진입점 — `quant-niche collect`.

깔때기 입구: 수집기로 공시를 받아 ledger 와 diff 한 뒤, **신규/변경된
사건만** 요약 출력하고 대장에 병합한다. 비싼 LLM 층(L1~L3)은 이 출력의
actionable 목록을 트리거로 별도 소환한다(이 CLI 는 LLM 을 부르지 않는다).

샌드박스처럼 네트워크가 막힌 환경에서는 각 수집기가 깔끔히 실패하고,
오프라인 fixture 모드(--fixture)로 전체 흐름을 검증할 수 있다.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from .collectors import dart, edgar
from .collectors.base import NetworkError
from .ledger import Event, EventLedger

DEFAULT_LEDGER = "data/ledger/events.jsonl"
EDGAR_FORMS = ["SC TO-I", "SC TO-T", "DEFM14A", "S-4", "N-2"]


def _collect_us(args) -> list[Event]:
    try:
        return edgar.fetch(EDGAR_FORMS, user_agent=args.user_agent,
                           date_from=args.date_from, date_to=args.date_to)
    except NetworkError as e:
        print(f"[US/EDGAR] 네트워크 차단/실패: {e}", file=sys.stderr)
        return []


def _collect_kr(args) -> list[Event]:
    try:
        return dart.fetch(args.date_from, args.date_to)
    except (NetworkError, RuntimeError) as e:
        print(f"[KR/DART] 수집 불가: {e}", file=sys.stderr)
        return []


def _collect_fixture(path: str) -> list[Event]:
    """오프라인 검증: EDGAR/DART 원시 응답 JSON 을 읽어 parse 만 수행."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    evs: list[Event] = []
    if "hits" in payload:
        evs += edgar.parse(payload)
    if "list" in payload or payload.get("status"):
        evs += dart.parse(payload)
    return evs


def cmd_collect(args) -> int:
    incoming: list[Event] = []
    if args.fixture:
        incoming = _collect_fixture(args.fixture)
    else:
        if args.market in ("us", "all"):
            incoming += _collect_us(args)
        if args.market in ("kr", "all"):
            incoming += _collect_kr(args)

    ledger = EventLedger.load(args.ledger)
    diff = ledger.diff(incoming)
    print(f"수집 {len(incoming)}건 → {diff.summary()}  (대장 기존 {len(ledger)}건)")
    for e in diff.actionable:
        flag = "NEW" if e in diff.new else "CHG"
        print(f"  [{flag}] {e.market} {e.kind or '?':16} {e.form_type:18} "
              f"{e.ticker or '-':8} {e.company or ''}  ({e.filed_at})")
    ledger.merge(diff)
    if not args.dry_run:
        ledger.save(args.ledger)
        print(f"대장 저장: {args.ledger} (총 {len(ledger)}건)")
    else:
        print("--dry-run: 대장 미저장")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="quant-niche", description="사건성 수렴 라이브 추적 하네스 (Layer 0)")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="공시 수집 → ledger diff/merge")
    c.add_argument("--market", choices=["us", "kr", "all"], default="all")
    c.add_argument("--days", type=int, default=7, help="조회 기간(오늘로부터 N일 전)")
    c.add_argument("--date-from", default=None)
    c.add_argument("--date-to", default=None)
    c.add_argument("--ledger", default=DEFAULT_LEDGER)
    c.add_argument("--fixture", default=None, help="오프라인 검증용 원시 응답 JSON 경로")
    c.add_argument("--user-agent", default="quant-niche research (contact: ksunho0660@gmail.com)")
    c.add_argument("--dry-run", action="store_true")
    c.set_defaults(func=cmd_collect)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "date_from", None) is None:
        args.date_to = date.today().isoformat()
        args.date_from = (date.today() - timedelta(days=args.days)).isoformat()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
