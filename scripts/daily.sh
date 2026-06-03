#!/usr/bin/env bash
# quant-niche 일일 자동 루프 (로컬 맥 crontab용)
#   1) L0 수집기(코드, $0): make collect — 신규 공시 diff → ledger
#   2) 에이전트 루프(헤드리스 Claude): idea-pipeline 워크플로 → 판정 → 브리프 갱신
#
# crontab 등록:  make cron-install   (또는 make cron-show 로 라인만 확인)
# 수동 1회 실행:  make loop
#
# 전제: `claude` CLI가 비대화식으로 인증돼 있어야 한다(로그인 1회). uv 설치 필요.

set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

mkdir -p data/brief
STAMP="$(date '+%Y-%m-%d %H:%M:%S')"
echo "===== daily loop $STAMP =====" >> data/brief/loop.log

# 1) 결정론 수집 (네트워크 막혀도 깔끔히 실패 → 계속 진행)
echo "[1/2] make collect" >> data/brief/loop.log
make collect DAYS=3 >> data/brief/loop.log 2>&1 || echo "  collect 실패(네트워크?) — 계속" >> data/brief/loop.log

# 2) 헤드리스 에이전트 루프
echo "[2/2] claude headless loop" >> data/brief/loop.log
if command -v claude >/dev/null 2>&1; then
  claude -p "$(cat scripts/daily-prompt.md)" \
    --permission-mode acceptEdits \
    >> data/brief/loop.log 2>&1 \
    && echo "  완료 $STAMP" >> data/brief/loop.log \
    || echo "  claude 루프 실패 — loop.log 확인" >> data/brief/loop.log
else
  echo "  claude CLI 없음 — 설치/인증 후 재시도" >> data/brief/loop.log
fi

echo "브리프: $REPO/data/brief/BRIEF.md"
