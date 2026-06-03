"""quant-niche — 사건성 수렴(near-arb) 라이브 추적 하네스.

설계: reports/01-agent-harness-architecture.md (4층 깔때기).
이 패키지는 Layer 0(결정론 수집기)을 구현한다 — 감시는 코드가 $0로,
판단(L1~L3)은 별도 LLM 층에서. 표준 라이브러리만 사용한다.
"""

__version__ = "0.1.0"
