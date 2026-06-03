"""이벤트 대장(ledger) — Layer 0의 단일 진실 공급원.

설계 원칙(reports/01 §3): 사실(공시 필드·가격)은 코드가 ledger에,
판단(생존/기각 논리)은 LLM이 research/ideas/에. 둘을 섞지 않는다.

대장은 JSONL(한 줄 = 한 사건)로 data/ledger/events.jsonl 에 캐시된다
(data/ 는 git 제외). event_id 로 중복을 제거하고, state_hash 로 변경을
감지해 **신규/변경된 판단점만** 상위 층(LLM)으로 흘려보낸다.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict, fields
from pathlib import Path
from typing import Iterable

# state_hash 계산에 들어가는 필드 — 이 값들이 바뀌면 "변경된 사건"으로 보고
# LLM 재추론을 트리거한다. 파생/추적 메타(status, idea_file 등)는 제외해야
# 페이퍼 추적 상태 변화가 불필요한 재분류를 일으키지 않는다.
_HASH_FIELDS = (
    "market",
    "source",
    "form_type",
    "kind",
    "ticker",
    "filed_at",
    "deal_price",
    "deadline",
    "odd_lot_provision",
)

VALID_STATUS = ("new", "screened", "tracked", "rejected", "closed")


@dataclass
class Event:
    """사건성 기회 1건. 결정론 층(L0)이 사실만 채운다."""

    event_id: str  # 결정론적 키(소스+접수번호) → 중복제거 단위
    market: str  # "US" | "KR"
    source: str  # "EDGAR" | "DART"
    form_type: str  # 원문 폼/보고서명 (예: "SC TO-I", "공개매수신고서")
    kind: str | None = None  # merger_cash|odd_lot_tender|cef_liquidation|forced_burn|None
    ticker: str | None = None
    company: str | None = None
    filed_at: str | None = None  # YYYY-MM-DD
    deal_price: float | None = None
    deadline: str | None = None  # YYYY-MM-DD (확정 종료일)
    odd_lot_provision: bool | None = None  # 단주 안분면제 조항 유무 (L1/수동 확인)
    spread_pct: float | None = None  # L0가 가격 붙여 계산
    annualized: float | None = None
    state_hash: str = ""
    classified_by: str = "deterministic"  # deterministic|haiku|manual
    status: str = "new"
    idea_file: str | None = None  # L2 진입 시 research/ideas/<id>.md 연결
    url: str | None = None
    extra: dict = field(default_factory=dict)

    def compute_hash(self) -> str:
        payload = {k: getattr(self, k) for k in _HASH_FIELDS}
        blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]

    def finalize(self) -> "Event":
        """state_hash 를 채워 반환(체이닝용)."""
        self.state_hash = self.compute_hash()
        return self

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: dict) -> "Event":
        known = {f.name for f in fields(cls)}
        clean = {k: v for k, v in d.items() if k in known}
        return cls(**clean)


@dataclass
class DiffResult:
    """대장 대비 신규/변경/무변경 분류 — LLM은 new+changed 에만 깨운다."""

    new: list[Event] = field(default_factory=list)
    changed: list[Event] = field(default_factory=list)
    unchanged: list[Event] = field(default_factory=list)

    @property
    def actionable(self) -> list[Event]:
        return self.new + self.changed

    def summary(self) -> str:
        return f"new={len(self.new)} changed={len(self.changed)} unchanged={len(self.unchanged)}"


class EventLedger:
    """JSONL 기반 이벤트 대장. event_id 로 키잉."""

    def __init__(self, events: Iterable[Event] | None = None):
        self._by_id: dict[str, Event] = {}
        for e in events or []:
            self._by_id[e.event_id] = e

    # --- 영속화 ---------------------------------------------------------
    @classmethod
    def load(cls, path: str | Path) -> "EventLedger":
        p = Path(path)
        if not p.exists():
            return cls()
        evs: list[Event] = []
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                evs.append(Event.from_dict(json.loads(line)))
        return cls(evs)

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        # filed_at 내림차순으로 안정 정렬해 diff 가독성 확보
        rows = sorted(
            self._by_id.values(),
            key=lambda e: (e.filed_at or "", e.event_id),
            reverse=True,
        )
        p.write_text("\n".join(e.to_json() for e in rows) + "\n", encoding="utf-8")

    # --- 조회 -----------------------------------------------------------
    def __len__(self) -> int:
        return len(self._by_id)

    def __contains__(self, event_id: str) -> bool:
        return event_id in self._by_id

    def get(self, event_id: str) -> Event | None:
        return self._by_id.get(event_id)

    def all(self) -> list[Event]:
        return list(self._by_id.values())

    def tracked(self) -> list[Event]:
        return [e for e in self._by_id.values() if e.status == "tracked"]

    # --- 깔때기 핵심: diff & 병합 ---------------------------------------
    def diff(self, incoming: Iterable[Event]) -> DiffResult:
        """수집기가 가져온 사건들을 대장과 대조해 분류한다.

        - 처음 보는 event_id → new
        - 본 적 있으나 state_hash 변동 → changed (LLM 재추론 대상)
        - 동일 → unchanged ($0, 스킵)
        """
        res = DiffResult()
        for e in incoming:
            if not e.state_hash:
                e.finalize()
            prev = self._by_id.get(e.event_id)
            if prev is None:
                res.new.append(e)
            elif prev.state_hash != e.state_hash:
                res.changed.append(e)
            else:
                res.unchanged.append(e)
        return res

    def merge(self, diff: DiffResult) -> None:
        """신규/변경 사건을 대장에 반영. 기존 추적 메타(status, idea_file)는
        변경 사건에서도 보존한다 — 사실 갱신이 판단 상태를 지우면 안 된다."""
        for e in diff.new:
            self._by_id[e.event_id] = e
        for e in diff.changed:
            prev = self._by_id.get(e.event_id)
            if prev is not None:
                # 사실 필드는 갱신하되 판단 메타는 유지
                e.status = prev.status if prev.status != "new" else e.status
                e.idea_file = prev.idea_file or e.idea_file
            self._by_id[e.event_id] = e
