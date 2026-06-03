# quant-niche — 자주 쓰는 명령 모음
# 그냥 `make` 만 치면 무엇을 할 수 있는지 목록이 나옵니다.
#
# 처음이라면 이 순서:  make setup  →  make test  →  make demo  →  (키 있으면) make collect

.DEFAULT_GOAL := help

# .env 가 있으면 라이브 수집 레시피에서 셸로 source 한다(따옴표 안전).
LOAD_ENV = set -a; [ -f .env ] && . ./.env; set +a;

DAYS    ?= 7
LEDGER  ?= data/ledger/events.jsonl

.PHONY: help setup test demo collect collect-us collect-kr collect-dry ledger check-key clean loop brief cron-show cron-install cron-remove

CRON_LINE = 0 7 * * 1-5 cd $(CURDIR) && /bin/zsh scripts/daily.sh >> data/brief/cron.log 2>&1

help: ## 이 도움말 출력 (기본)
	@echo "quant-niche — make <명령>"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "예) make collect DAYS=14    (조회 기간 바꾸기)"

setup: ## 가상환경 생성 + 패키지/개발도구 설치 (처음 1회)
	uv venv
	uv pip install -e ".[dev]"

test: ## 오프라인 결정론 테스트 (네트워크 불필요)
	uv run pytest

demo: ## 네트워크 없이 fixture 로 전체 흐름 체험 (대장 미저장)
	uv run quant-niche collect --fixture tests/fixtures/edgar_search.json --dry-run
	uv run quant-niche collect --fixture tests/fixtures/dart_list.json --dry-run

collect: ## 라이브 수집(미국+한국) → 대장 갱신.  DAYS=N 로 기간 조절
	@$(LOAD_ENV) uv run quant-niche collect --market all --days $(DAYS) --ledger $(LEDGER)

collect-us: ## 라이브 수집 — 미국(EDGAR)만. 키 불필요
	@$(LOAD_ENV) uv run quant-niche collect --market us --days $(DAYS) --ledger $(LEDGER)

collect-kr: ## 라이브 수집 — 한국(DART)만. DART_API_KEY 필요
	@$(LOAD_ENV) uv run quant-niche collect --market kr --days $(DAYS) --ledger $(LEDGER)

collect-dry: ## 라이브 수집을 돌려보되 대장에 저장하지 않음
	@$(LOAD_ENV) uv run quant-niche collect --market all --days $(DAYS) --dry-run

ledger: ## 현재 대장에 쌓인 사건 건수/내용 보기
	@if [ -f $(LEDGER) ]; then \
		echo "대장: $(LEDGER) ($$(wc -l < $(LEDGER) | tr -d ' ')건)"; \
		cat $(LEDGER); \
	else \
		echo "대장 없음 ($(LEDGER)). 먼저 make collect 를 돌리세요."; \
	fi

check-key: ## DART_API_KEY 가 .env 에 잡히는지 확인
	@$(LOAD_ENV) if [ -n "$$DART_API_KEY" ]; then \
		echo "DART_API_KEY 설정됨 (끝 4자리: ...$${DART_API_KEY: -4})"; \
	else \
		echo "DART_API_KEY 미설정 — .env 에 넣거나 opendart.fss.or.kr 에서 발급하세요."; \
	fi

loop: ## 일일 자동 루프 1회 수동 실행 (수집→에이전트 워크플로→브리프)
	@bash scripts/daily.sh

brief: ## 최상단 브리프(지금 기회 + 행동 조언) 보기
	@if [ -f data/brief/BRIEF.md ]; then cat data/brief/BRIEF.md; \
	else echo "브리프 없음. 먼저 make loop 를 돌리세요."; fi

cron-show: ## 등록할 crontab 라인 출력 (매 평일 07:00)
	@echo "$(CRON_LINE)"

cron-install: ## 위 crontab 라인을 등록 (중복 시 건너뜀)
	@( crontab -l 2>/dev/null | grep -vF 'scripts/daily.sh'; echo "$(CRON_LINE)" ) | crontab -
	@echo "등록 완료. 확인: crontab -l"

cron-remove: ## quant-niche cron 라인 제거
	@( crontab -l 2>/dev/null | grep -vF 'scripts/daily.sh' ) | crontab - || true
	@echo "제거 완료."

clean: ## 캐시 정리 (.pytest_cache, __pycache__ 등)
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +
