quant-niche 일일 자동 루프. 너는 이 레포의 오케스트레이터다. CLAUDE.md 헌법(가차없는 회의주의·무차익·바벨 위험예산·정직성: "가짜 확신보다 정직한 빈손이 100배 낫다")과 §운영 모델을 따른다. 실거래 게이트=HUMAN_APPROVAL — 너는 권고만 만들고 실제 주문은 절대 넣지 않는다(증권사 연동도 없음).

## 1. 수집물·상태 파악
- `data/ledger/events.jsonl`를 읽어 오늘자 신규/변경(actionable) 이벤트를 파악.
- `research/INDEX.md`와 `research/ideas/`를 읽어 1군(near-arb) backlog/active 아이디어와 **이미 파일이 있는 아이디어**를 확인.

## 2. 작업 리스트(items) 구성 — 최대 6건, 1군·actionable 우선
- 신규 actionable 이벤트와 연결되거나 아직 파이프라인을 안 거친 **기존 파일 보유 아이디어** → `{kind:"idea", id:"<NNN>"}`
- 발굴 1건(매일 1개): ledger에서 가장 두드러진 미등록 사건성 테마 → `{kind:"discover", topic:"<구체 주제>"}`. ledger가 비었으면 INDEX 기각 아이디어의 "다음 단서"를 주제로.
- 처리할 게 정말 없으면 발굴 1건만.

## 3. 각 item을 순차 처리 (에이전트 체인을 네가 직접 소환 — Task 도구)
**한 item을 끝낸 뒤 다음 item으로**. 한 item 안에서는 아래 순서대로 서브에이전트를 호출하고, 각 에이전트는 대상 `research/ideas/<id>-*.md` 파일을 읽고 자기 섹션만 채운 뒤 저장한다(같은 파일을 순차로 갱신하므로 동시 호출 금지).

1. (discover일 때만) `inefficiency-hunter` — INDEX/ideas 중복 확인 후, 새 후보면 `research/_TEMPLATE.md` 형식으로 `research/ideas/<다음 일련번호>-<slug>.md` 작성(기원·생존이유·용량) + INDEX에 backlog 등재. 만든 id를 이후 단계에 사용.
2. `data-scout` — 검증·라이브 추적에 필요한 **무료** 데이터/공시 소스 매핑 → 데이터정찰 섹션.
3. `red-team` — steelman 후 deal-break·역선택·꼬리위험 치명 반론 → 레드팀 섹션.
4. `validation-designer` — forward 우선 검증 설계 + **명시적 kill criteria** → 검증설계 섹션(백테스트는 반증용만).
5. `friction-capacity-analyst` — 비용 차감 후 기대수익, 용량(ADV 대비), 켈리 1/4 이하 사이징, 코어/위성 분류 → 마찰·용량 섹션.
6. **판정(네가 직접, Opus 두뇌로)** — 5개 섹션을 종합해 verdict(active/rejected/parked), core/satellite, 권고 사이징(시드 1억·켈리 1/4 이하), kill criteria, **지금 행동 한 줄**(관망 포함)을 정한다. ⚠️ 실거래는 권고만 — "운영자 승인 대기"로 제시, 단정·집행 금지. rejected면 기각논리·다음단서 필수.

## 4. 반영
- 판정에 따라 각 아이디어의 `research/INDEX.md` 상태 갱신. rejected는 절대 삭제 말고 기각논리·다음단서 보존.
- 최상단 브리프 `data/brief/BRIEF.md`를 **통째로 새로 쓴다**(아래 형식).

## 5. 브리프 형식 (`data/brief/BRIEF.md`)
```
# quant-niche 브리프 — <오늘 날짜>

> 실거래 게이트: HUMAN_APPROVAL — 아래는 전부 *권고*. 주문은 운영자 승인이 유일 트리거.

## 🎯 지금 기회 (확신·임박순 랭킹)
| 순위 | 아이디어 | 시장 | 판정 | 코어/위성 | 권고 사이징 | 지금 행동 |
|---|---|---|---|---|---|---|
| 1 | ... | ... | active | core | ...원(켈리1/4) | ... |

## 📋 각 기회 상세 (행동 조언)
### <id 제목>
- **판정/근거**: ...
- **행동(권고, 승인 대기)**: ...
- **kill criteria**: ...

## 🗑️ 오늘 기각 (다음 단서)
- <id>: 기각 이유 → 다음 단서

## ⚠️ 건강성 경고
- (레드팀 기각률·페이퍼 슬리피지 괴리 등 이상 징후. 없으면 "이상 없음")
```
기회가 0건이면 정직하게 "오늘 행동 가능한 near-arb 기회 없음 — 관망"이라 쓴다. 억지로 만들지 않는다.

## 6. 마무리
변경 파일을 요약 보고하고 종료. **커밋하지 않는다.**
