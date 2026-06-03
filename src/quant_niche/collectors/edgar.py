"""SEC EDGAR 수집기 — 미국 사건성 공시.

full-text search(efts.sec.gov/LATEST/search-index)로 폼타입별 신규 제출을
받아 Event 로 변환한다. 노리는 폼(reports/01, RUNBOOK):
  · SC TO-I / SC TO-T → 공개매수(단주 안분면제 후보: odd_lot_tender)
  · DEFM14A / S-4     → 현금 합병(merger_cash)
  · N-2               → CEF(폐쇄형) 청산/전환(cef_liquidation)

odd_lot_provision(단주 안분면제 조항)은 리스트만으로 알 수 없으므로 None.
→ Layer 1(Haiku) 또는 수동이 원문에서 확인한다(reports/01 정직성 가드레일).
"""

from __future__ import annotations

import re
import urllib.parse

from ..ledger import Event
from .base import http_get_json

EFTS_URL = "https://efts.sec.gov/LATEST/search-index"

# 폼타입 → (kind, market 은 항상 US)
_FORM_KIND = {
    "SC TO-I": "odd_lot_tender",
    "SC TO-T": "odd_lot_tender",
    "DEFM14A": "merger_cash",
    "S-4": "merger_cash",
    "N-2": "cef_liquidation",
}

# display_names 예: "Apple Inc. (AAPL) (CIK 0000320193)"
_TICKER_RE = re.compile(r"\(([A-Z][A-Z0-9.\-]{0,6})\)")


def build_url(forms: list[str], q: str = '"odd-lot"', date_from: str | None = None,
              date_to: str | None = None) -> str:
    params = {"forms": ",".join(forms)}
    if q:
        params["q"] = q
    if date_from:
        params["dateRange"] = "custom"
        params["startdt"] = date_from
        params["enddt"] = date_to or date_from
    return f"{EFTS_URL}?{urllib.parse.urlencode(params)}"


def _ticker_from_display(names: list[str]) -> str | None:
    for n in names:
        # CIK 괄호는 제외하고 첫 티커형 토큰만
        for m in _TICKER_RE.finditer(n):
            tok = m.group(1)
            if not tok.startswith("CIK"):
                return tok
    return None


def parse(payload: dict, *, default_form: str | None = None) -> list[Event]:
    """EDGAR full-text search JSON → Event 리스트(순수 함수, 테스트 대상)."""
    out: list[Event] = []
    hits = (payload.get("hits") or {}).get("hits") or []
    for h in hits:
        src = h.get("_source") or {}
        # _id 형식: "0001193125-24-000123:d123.htm"
        raw_id = h.get("_id") or ""
        accession = raw_id.split(":", 1)[0] if raw_id else ""
        forms = src.get("root_forms") or ([src["file_type"]] if src.get("file_type") else [])
        form_type = (forms[0] if forms else default_form) or "UNKNOWN"
        kind = _FORM_KIND.get(form_type)
        names = src.get("display_names") or []
        company = names[0].split(" (")[0] if names else None
        ticker = _ticker_from_display(names)
        cik = (src.get("ciks") or [""])[0]
        url = (
            f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}"
            if cik else None
        )
        ev = Event(
            event_id=f"us-edgar-{accession}" if accession else f"us-edgar-{raw_id}",
            market="US",
            source="EDGAR",
            form_type=form_type,
            kind=kind,
            ticker=ticker,
            company=company,
            filed_at=src.get("file_date"),
            url=url,
            extra={"cik": cik, "accession": accession},
        ).finalize()
        out.append(ev)
    return out


def fetch(forms: list[str], *, user_agent: str, q: str = "",
          date_from: str | None = None, date_to: str | None = None) -> list[Event]:
    """라이브 호출 → Event. 네트워크 allowlist 필요(이 샌드박스에선 차단)."""
    url = build_url(forms, q=q, date_from=date_from, date_to=date_to)
    payload = http_get_json(url, user_agent=user_agent)
    return parse(payload)
