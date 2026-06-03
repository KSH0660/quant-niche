quant-niche 일일 자동 루프. CLAUDE.md 헌법(가차없는 회의주의·무차익·바벨 위험예산·정직성)과 §운영 모델을 따른다. 실거래 게이트는 HUMAN_APPROVAL — 너는 권고만 만들고 실제 주문은 절대 넣지 않는다(증권사 연동도 없음).

수행 단계:

1. **수집물 확인**: `data/ledger/events.jsonl`를 읽어 오늘자 신규/변경(actionable) 이벤트를 파악한다. `research/INDEX.md`에서 1군(near-arb) backlog/active 아이디어도 확인한다.

2. **작업 리스트 구성**: 아래를 합쳐 `items` 배열을 만든다(최대 8개로 제한, 1군·actionable 우선):
   - 신규 actionable 이벤트와 연결되거나 아직 파이프라인을 안 거친 기존 아이디어 → `{kind:"idea", id:"<NNN>"}`
   - 발굴 1건(매일 1개): 그날 ledger에서 가장 두드러진 미등록 사건성 테마 → `{kind:"discover", topic:"<구체 주제>"}`. ledger가 비었으면 INDEX 기각 아이디어의 "다음 단서"를 주제로.
   - 처리할 게 정말 없으면 items는 발굴 1건만.

3. **워크플로 실행**: `Workflow` 도구로 `idea-pipeline`을 호출한다.
   `args = { items, gate: "HUMAN_APPROVAL" }`
   (resolve 실패 시 `scriptPath: ".claude/workflows/idea-pipeline.js"`로 재시도.)
   워크플로가 각 아이템을 발굴→정찰→레드팀→검증→마찰→Opus판정까지 자동으로 돌리고 `verdicts`를 돌려준다.

4. **반영**: 받은 verdicts로
   - 각 아이디어의 `research/INDEX.md` 상태를 갱신(active/rejected/parked). rejected는 절대 삭제하지 말고 기각논리·다음단서 보존.
   - 최상단 브리프 `data/brief/BRIEF.md`를 **통째로 새로 쓴다**(아래 형식).

5. **브리프 형식** (`data/brief/BRIEF.md`):
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
   기회가 0건이면 정직하게 "오늘 행동 가능한 near-arb 기회 없음 — 관망"이라고 쓴다. 억지로 만들지 않는다.

6. 변경 파일을 요약 보고하고 종료. (커밋은 하지 않는다.)
