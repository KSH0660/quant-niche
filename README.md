# quant-niche

거대 자본이 시장 충격 때문에 진입 못 하는 **소용량·사건성 시장 비효율**을 발굴·검증하고,
**확정 종료일/메커니즘이 수렴을 강제하는 기회**를 루프 에이전트로 라이브 추적하는
회의주의 퀀트 워크벤치.

- 프로젝트 헌법·원칙: [`CLAUDE.md`](CLAUDE.md)
- 사전지식(4개 모델 수렴): [`reports/00-prior-art-synthesis.md`](reports/00-prior-art-synthesis.md)
- 토큰-검약 하네스 설계: [`reports/01-agent-harness-architecture.md`](reports/01-agent-harness-architecture.md)
- **루프 운영 플레이북(하루종일 돌리면 뭐가 나오나·어떻게 등록하나)**: [`reports/02-loop-operations-playbook.md`](reports/02-loop-operations-playbook.md)
- 아이디어 레지스트리: [`research/INDEX.md`](research/INDEX.md) · 운영절차: [`research/RUNBOOK.md`](research/RUNBOOK.md)

## Layer 0 — 결정론 수집기 (이 패키지)

설계의 핵심: **감시는 코드가 $0로, 판단만 LLM이.** 이 패키지(`src/quant_niche/`)는
공시 폴링·중복제거·변경감지·스프레드 계산까지의 결정론 층을 표준 라이브러리만으로 구현한다.

```
src/quant_niche/
  ledger.py          # Event 스키마 + JSONL 대장(중복제거·diff·변경감지)
  metrics.py         # 스프레드/연율화/잔여일수/켈리 (전부 코드, 토큰 0)
  prices.py          # Stooq CSV 가격 → 스프레드 enrich
  collectors/
    base.py          # urllib HTTP(UA·재시도)
    edgar.py         # SEC EDGAR full-text search 파서
    dart.py          # DART OpenAPI 목록 파서
  cli.py             # `quant-niche collect` — 수집→diff→merge
```

### 사용

```bash
uv venv && uv pip install -e ".[dev]"
uv run pytest                                   # 오프라인 결정론 테스트
uv run quant-niche collect --fixture tests/fixtures/edgar_search.json --dry-run
uv run quant-niche collect --market all --days 7   # 라이브(네트워크 allowlist 필요)
```

### 네트워크·키 요구사항 (정직성 노트)

- **EDGAR**: 무료·키 불필요. 식별 User-Agent 필요(이메일 포함).
- **DART**: 무료지만 **API 키 필요** — `opendart.fss.or.kr` 발급 후 `DART_API_KEY` 환경변수.
- 호스트 allowlist 가 막힌 샌드박스에서는 라이브 수집이 차단되므로, 파싱 로직은
  `tests/fixtures/` 의 원시 응답으로 오프라인 검증한다.

비싼 LLM 층(L1 분류 → L2 회의주의 → L3 변화 재추론)은 이 CLI 의 `actionable`(신규/변경)
출력만 트리거로 별도 소환한다. 판정·실거래는 자동화하지 않는다(운영자 승인 유지).
