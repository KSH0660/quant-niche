"""Layer 0 결정론 수집기 — 공시 폴링·파싱(LLM 토큰 0).

각 수집기는 (a) fetch: 네트워크에서 원시 응답을 받고,
(b) parse: 순수 함수로 Event 리스트를 만든다.
parse 는 네트워크 없이 fixture 로 테스트 가능하게 분리한다.
"""
