# RUNBOOK — 자동화 파이프라인 운영

운영자 결정(2026-06 개정): **자동화 우선**. 과거 "수동 우선" 방침은 폐기. 아래 체인은 `.claude/workflows/idea-pipeline` 워크플로로 자동 오케스트레이션되고 **매일 cron**으로 백그라운드에서 돈다. 자동화 범위·실거래 게이트는 `CLAUDE.md` §운영 모델을 따른다(판정까지 자동 + Opus 투입, 실거래 집행은 `HUMAN_APPROVAL` 게이트 — 운영자가 토글).

> 사전지식: `reports/00-prior-art-synthesis.md` · 헌법: `CLAUDE.md` · 후보: `INDEX.md`

## 파이프라인 (이벤트 1건 또는 후보 1건당)

```
1. 수집/발굴   inefficiency-hunter   신규 이벤트·후보 → ideas/<id>-<slug>.md 초안 (기원·생존·용량)
2. 데이터정찰  data-scout            검증·추적에 필요한 무료 데이터/공시 소스 매핑
3. 레드팀      red-team             steelman → deal-break·역선택·꼬리 반론
4. 검증설계    validation-designer  forward 검증 설계 + kill criteria (백테스트는 반증용만)
5. 마찰·용량   friction-capacity    비용 차감 후 기대수익, 용량, 켈리 1/4, 코어/위성 분류
6. 판정        Opus 종합            판정(active/rejected/parked) + 사이징 권고 + INDEX 갱신 + 브리프 적재
```

각 에이전트는 대상 `ideas/` 파일을 읽고 자기 섹션만 채운 뒤 다음으로 넘긴다(이 배턴 넘기기를 워크플로가 자동 전달). `rejected`도 파일·INDEX에 보존(기각 논리·다음 단서 필수). 6단계 판정은 **가장 똑똑한 모델(Opus)**이 맡고, 결과는 최상단 브리프(`data/brief/`)에 권고로 적재된다 — 실거래 주문 전송만 게이트를 거친다.

## 이벤트 수집 — 무료 공시 소스 (양 시장)

| 시장 | 소스 | 노리는 이벤트 |
|---|---|---|
| 한국 | DART (dart.fss.or.kr) | 공개매수(단주 우대 확인), 합병, 자사주 의무소각, 정리매매 |
| 미국 | SEC EDGAR (SC TO-I/TO-T, DEFM14A, S-4, N-2) | 현금 합병, 단주 공개매수(odd-lot proration), CEF 청산/전환 |
| 가격/유동성 | yfinance, Stooq | 스프레드·ADV·체결 가능성(용량 판정용) |
| 매크로/금리 | FRED | 국면·캐리 판단 |

## 1차 착수 순서 (우선순위)

1. **INDEX 010 단주 공개매수 우대** — 가장 무위험에 가까움(코어 시드). 양 시장 현재 진행 공개매수에 100주 미만 안분 면제 조항이 있는지 확인부터.
2. **INDEX 011 합병 차익거래(현금)** — 코어 본체 후보. 진행 중 현금 인수 딜의 스프레드·deal-break 위험 스크리닝.
3. **INDEX 012 만기형 CEF 청산** — 미국 한정 코어 보강.

→ 위 3개로 코어 엔진을 먼저 세우고, 확신 높은 단일 딜을 위성(위험 예산)으로 별도 관리.

## 자동화 구성 (현행)

- **매일 cron**: L0 수집기(`make collect`, 코드·키 불필요분) → 신규/변경 actionable 이벤트 산출.
- **이벤트 트리거**: actionable 이벤트마다 `idea-pipeline` 워크플로 자동 소환(발굴→정찰→레드팀→검증→마찰→Opus 판정).
- **브리프 갱신**: 판정 결과를 `data/brief/`의 "지금 기회 + 최종 행동 조언"으로 랭킹·적재. 운영자는 이 브리프만 본다.
- **실거래 게이트**: `CLAUDE.md` §운영 모델의 스위치(`HUMAN_APPROVAL` 기본 / `FULL_AUTO`). 기본값에서 주문 전송은 운영자 승인이 유일 트리거.
- **건강성 점검(권장)**: 레드팀 기각률·페이퍼 추적 슬리피지가 메커니즘과 어긋나면 브리프 상단에 경고. 괴리 크면 해당 전략 자동 일시중단.

> **토큰-검약 루프 설계**: `reports/01-agent-harness-architecture.md` (4층 깔때기 — 감시는 코드가 $0으로, 판단만 LLM이. 비싼 층은 event-driven 트리거).
> **루프 운영 플레이북(산출물·등록법)**: `reports/02-loop-operations-playbook.md` (하루종일 돌리면 뭐가 나오나, `/loop`·cron 등록, 정직한 한계).
