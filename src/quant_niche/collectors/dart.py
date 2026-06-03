"""DART(전자공시) 수집기 — 한국 사건성 공시.

OpenAPI list.json 으로 기간 내 공시 목록을 받아, 보고서명(report_nm)
키워드로 노리는 사건을 선별한다(reports/01, RUNBOOK):
  · 공개매수            → odd_lot_tender / merger 관련
  · 합병               → merger_cash
  · 자기주식 ... 소각   → forced_burn (자사주 의무소각)
  · 정리매매           → (상폐 수렴, 참고)

API 키 필요: 환경변수 DART_API_KEY (무료 발급, opendart.fss.or.kr).
키/네트워크 없으면 fetch 는 실패하지만 parse 는 fixture 로 테스트된다.
"""

from __future__ import annotations

import os
import urllib.parse

from ..ledger import Event
from .base import http_get_json

LIST_URL = "https://opendart.fss.or.kr/api/list.json"

# 보고서명 키워드 → kind (우선순위 순서대로 첫 매치)
_KEYWORD_KIND = [
    ("공개매수", "odd_lot_tender"),
    ("합병", "merger_cash"),
    ("소각", "forced_burn"),
    ("정리매매", "cef_liquidation"),  # 상폐 수렴(분류상 청산형으로 묶음)
]


def classify_report(report_nm: str) -> str | None:
    for kw, kind in _KEYWORD_KIND:
        if kw in report_nm:
            return kind
    return None


def build_url(api_key: str, date_from: str, date_to: str,
              page_no: int = 1, page_count: int = 100) -> str:
    params = {
        "crtfc_key": api_key,
        "bgn_de": date_from.replace("-", ""),
        "end_de": date_to.replace("-", ""),
        "page_no": page_no,
        "page_count": page_count,
    }
    return f"{LIST_URL}?{urllib.parse.urlencode(params)}"


def parse(payload: dict, *, only_targets: bool = True) -> list[Event]:
    """DART list.json → Event 리스트(순수 함수, 테스트 대상).

    only_targets=True 면 노리는 사건 키워드에 매칭되는 공시만 남긴다.
    """
    if payload.get("status") not in (None, "000"):
        # 013(데이터 없음) 등은 빈 리스트로 처리, 그 외 오류는 그대로 빈 리스트
        return []
    out: list[Event] = []
    for row in payload.get("list") or []:
        report_nm = row.get("report_nm", "")
        kind = classify_report(report_nm)
        if only_targets and kind is None:
            continue
        rcept_no = row.get("rcept_no", "")
        rcept_dt = row.get("rcept_dt", "")
        filed_at = (
            f"{rcept_dt[:4]}-{rcept_dt[4:6]}-{rcept_dt[6:8]}" if len(rcept_dt) == 8 else rcept_dt
        )
        url = (
            f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}" if rcept_no else None
        )
        ev = Event(
            event_id=f"kr-dart-{rcept_no}",
            market="KR",
            source="DART",
            form_type=report_nm,
            kind=kind,
            ticker=row.get("stock_code") or None,
            company=row.get("corp_name") or None,
            filed_at=filed_at or None,
            url=url,
            extra={"corp_code": row.get("corp_code"), "rcept_no": rcept_no},
        ).finalize()
        out.append(ev)
    return out


def fetch(date_from: str, date_to: str, *, api_key: str | None = None,
          only_targets: bool = True) -> list[Event]:
    """라이브 호출 → Event. DART_API_KEY 필요, 네트워크 allowlist 필요."""
    key = api_key or os.environ.get("DART_API_KEY")
    if not key:
        raise RuntimeError("DART_API_KEY 미설정 — opendart.fss.or.kr 무료 발급 후 환경변수 지정")
    url = build_url(key, date_from, date_to)
    payload = http_get_json(url)
    return parse(payload, only_targets=only_targets)
