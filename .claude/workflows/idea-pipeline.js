export const meta = {
  name: 'idea-pipeline',
  description: 'quant-niche 아이디어 자동 파이프라인: 발굴→정찰→레드팀→검증→마찰→Opus판정. 실거래는 HUMAN_APPROVAL 게이트(권고만).',
  whenToUse: '신규 사건성 이벤트/후보를 발굴·검증·판정해 최상단 브리프 권고를 만들 때. cron 일일 루프가 호출.',
  phases: [
    { title: 'Discover', detail: 'inefficiency-hunter — 신규 후보 발굴(해당 시)' },
    { title: 'Scout', detail: 'data-scout — 무료 데이터/공시 소스 매핑' },
    { title: 'RedTeam', detail: 'red-team — steelman→deal-break·꼬리 반론' },
    { title: 'Validate', detail: 'validation-designer — forward 검증 + kill criteria' },
    { title: 'Friction', detail: 'friction-capacity-analyst — 비용차감·용량·켈리' },
    { title: 'Judge', detail: 'Opus 종합 판정 + 사이징 권고', model: 'opus' },
  ],
}

// args = {
//   items: [ {kind:'idea', id:'010'} | {kind:'discover', topic:'...'} , ... ],
//   gate: 'HUMAN_APPROVAL' | 'FULL_AUTO'   // 기본 HUMAN_APPROVAL
// }
const items = (args && Array.isArray(args.items)) ? args.items : []
const gate = (args && args.gate) || 'HUMAN_APPROVAL'

if (!items.length) {
  log('처리할 아이템이 없습니다. args.items 예: [{"kind":"idea","id":"010"},{"kind":"discover","topic":"진행중 단주 공개매수"}]')
  return { gate, verdicts: [] }
}

const DISCOVER_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    idea_id: { type: 'string', description: 'INDEX 일련번호(예: 014). 새로 작성한 아이디어 id' },
    idea_file: { type: 'string', description: '작성한 파일 경로' },
    title: { type: 'string' },
    created: { type: 'boolean', description: '실제로 새 파일을 만들었으면 true. 중복이라 안 만들었으면 false' },
  },
  required: ['idea_id', 'created'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    idea_id: { type: 'string' },
    verdict: { type: 'string', enum: ['active', 'rejected', 'parked'] },
    core_or_satellite: { type: 'string', enum: ['core', 'satellite', 'none'] },
    recommended_sizing: { type: 'string', description: '시드 1억 기준 권고 금액·% (켈리 1/4 이하). 없으면 "해당없음"' },
    kelly_note: { type: 'string' },
    kill_criteria: { type: 'string', description: '이 조건이면 폐기' },
    action_now: { type: 'string', description: '지금 취할 행동 한 줄 (관망 포함). 실거래는 권고만 — 단정 금지' },
    rationale: { type: 'string' },
    next_clue: { type: 'string', description: 'rejected면 다음 단서 필수' },
    requires_operator_approval: { type: 'boolean' },
  },
  required: ['idea_id', 'verdict', 'action_now', 'recommended_sizing', 'rationale', 'requires_operator_approval'],
}

const GATE_NOTE =
  gate === 'FULL_AUTO'
    ? '실거래 게이트=FULL_AUTO지만, 이 레포엔 증권사 연동이 없으므로 실제 주문은 불가하다. 권고안만 제시하라.'
    : '실거래 게이트=HUMAN_APPROVAL. 너는 권고만 한다. 실제 주문을 넣거나 넣었다고 단정하지 말고, "운영자 승인 대기" 권고안으로 제시하라.'

const verdicts = []

// 순차 처리: discover가 INDEX 일련번호를 잡으므로 동시 실행 시 번호 충돌 위험 → 안전하게 직렬.
for (let i = 0; i < items.length; i++) {
  const item = items[i]
  let ideaId = item.id || null

  phase('Discover')
  if (item.kind === 'discover') {
    const d = await agent(
      `주제 "${item.topic}"로, 거대 자본이 시장충격 때문에 못 들어오는 소용량 비효율 또는 확정 사건성 수렴(near-arb) 후보 1건을 발굴하라. ` +
      `먼저 research/INDEX.md와 research/ideas/를 읽어 **중복을 피한다**(이미 있으면 만들지 말고 그 id를 반환, created=false). ` +
      `새 후보면 research/_TEMPLATE.md 형식으로 research/ideas/<다음 일련번호>-<slug>.md 를 작성(기원·생존이유·용량 섹션 채움)하고 research/INDEX.md 표에 backlog로 등재한 뒤, id/경로를 반환하라.`,
      { agentType: 'inefficiency-hunter', phase: 'Discover', label: `discover:${item.topic}`, schema: DISCOVER_SCHEMA }
    )
    if (!d || !d.idea_id) { log(`[${i}] 발굴 실패 — 스킵`); continue }
    ideaId = d.idea_id
  }
  if (!ideaId) { log(`[${i}] id 없음 — 스킵`); continue }

  const target = `대상: research/ideas/ 에서 파일명이 "${ideaId}-"로 시작하는 아이디어 파일. 그 파일을 읽고 자기 섹션만 채운 뒤 저장하라.`

  phase('Scout')
  await agent(`${target}\n이 아이디어의 검증·라이브 추적에 필요한 **무료** 데이터/공시 소스(EDGAR·DART·yfinance·Stooq·FRED 등)를 항목별로 매핑해 데이터정찰 섹션을 채워라.`,
    { agentType: 'data-scout', phase: 'Scout', label: `scout:${ideaId}` })

  phase('RedTeam')
  await agent(`${target}\nsteelman(최강 옹호)을 세운 뒤 그것을 무너뜨리는 deal-break·역선택·꼬리위험 치명적 반론으로 레드팀 섹션을 채워라.`,
    { agentType: 'red-team', phase: 'RedTeam', label: `redteam:${ideaId}` })

  phase('Validate')
  await agent(`${target}\nforward 우선 검증 설계와 **명시적 kill criteria**로 검증설계 섹션을 채워라. 백테스트는 반증용으로만.`,
    { agentType: 'validation-designer', phase: 'Validate', label: `validate:${ideaId}` })

  phase('Friction')
  await agent(`${target}\n왕복 수수료·호가스프레드·슬리피지·세금 차감 후 기대수익, 용량(종목별 ADV 대비 주문크기), 켈리 1/4 이하 사이징, 코어/위성 분류로 마찰·용량 섹션을 채워라.`,
    { agentType: 'friction-capacity-analyst', phase: 'Friction', label: `friction:${ideaId}` })

  phase('Judge')
  const v = await agent(
    `당신은 quant-niche의 최종 판정자다. CLAUDE.md 헌법(가차없는 회의주의·무차익·바벨 위험예산·정직성: "가짜 확신보다 정직한 빈손이 100배 낫다")을 따른다.\n${target}\n` +
    `채워진 5개 섹션(기원/정찰/레드팀/검증/마찰)을 읽고 종합 판정하라:\n` +
    `- verdict: active / rejected / parked (rejected면 next_clue 필수)\n` +
    `- core_or_satellite + 시드 1억 기준 권고 사이징(켈리 1/4 이하) + kill_criteria\n` +
    `- action_now: 지금 취할 행동 한 줄(관망도 가능)\n` +
    `${GATE_NOTE}\n판정 결과를 구조화해 반환하라. INDEX 갱신·브리프 적재는 메인 세션이 한다.`,
    { model: 'opus', phase: 'Judge', label: `judge:${ideaId}`, schema: VERDICT_SCHEMA }
  )
  verdicts.push({ kind: item.kind, ...v, idea_id: v.idea_id || ideaId })
  log(`[${i}] ${ideaId} 판정: ${v.verdict} / ${v.action_now}`)
}

log(`판정 완료: ${verdicts.length}건 (게이트=${gate})`)
return { gate, verdicts }
