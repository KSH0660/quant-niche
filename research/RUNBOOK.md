# RUNBOOK — 수동 파이프라인 운영

운영자 결정: **수동 파이프라인 우선**(자동 cron 루프는 흐름 검증 후). 메인 세션이 오케스트레이터로 아래 체인을 on-demand 실행한다. 흐름이 안정되면 같은 단계를 스케줄러로 자동화한다.

> 사전지식: `reports/00-prior-art-synthesis.md` · 헌법: `CLAUDE.md` · 후보: `INDEX.md`

## 파이프라인 (이벤트 1건 또는 후보 1건당)

```
1. 수집/발굴   inefficiency-hunter   신규 이벤트·후보 → ideas/<id>-<slug>.md 초안 (기원·생존·용량)
2. 데이터정찰  data-scout            검증·추적에 필요한 무료 데이터/공시 소스 매핑
3. 레드팀      red-team             steelman → deal-break·역선택·꼬리 반론
4. 검증설계    validation-designer  forward 검증 설계 + kill criteria (백테스트는 반증용만)
5. 마찰·용량   friction-capacity    비용 차감 후 기대수익, 용량, 켈리 1/4, 코어/위성 분류
6. 종합        (메인 세션)          판정(active/rejected/parked) + INDEX 갱신 + 필요시 reports/
```

각 에이전트는 대상 `ideas/` 파일을 읽고 자기 섹션만 채운 뒤 다음으로 넘긴다. `rejected`도 파일·INDEX에 보존(기각 논리·다음 단서 필수).

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

## 자동화 전환 기준 (나중)

수동 파이프라인이 (a) 신규 이벤트를 안정적으로 포착하고 (b) 레드팀 기각률이 합리적이며 (c) 페이퍼 추적 결과가 메커니즘과 일치할 때, 1~2단계(수집·정찰)부터 `schedule`(cron)로 자동화한다. 판정·실거래 결정은 자동화하지 않는다(운영자 승인 유지).

> **토큰-검약 루프 설계**: `reports/01-agent-harness-architecture.md` (4층 깔때기 — 감시는 코드가 $0으로, 판단만 LLM이. 비싼 층은 event-driven 트리거).
