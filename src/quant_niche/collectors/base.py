"""수집기 공통 HTTP 유틸 — 표준 라이브러리만(urllib).

외부 의존성 없이 어디서나 구동. EDGAR 는 식별 User-Agent 를 요구하므로
호출자가 연락처 UA 를 넘길 수 있게 한다. 네트워크가 막힌 환경에서는
NetworkError 로 깔끔히 실패한다(파싱 로직은 영향 없음).
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request


class NetworkError(RuntimeError):
    """네트워크 호출 실패(차단/타임아웃/HTTP 오류)."""


def http_get(
    url: str,
    *,
    user_agent: str = "quant-niche research (contact: set UA)",
    timeout: float = 15.0,
    retries: int = 3,
    backoff: float = 2.0,
    accept: str = "application/json",
) -> str:
    """GET 본문을 문자열로 반환. 실패 시 지수 백오프 재시도 후 NetworkError."""
    headers = {"User-Agent": user_agent, "Accept": accept}
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                return resp.read().decode(charset, errors="replace")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            last = e
            if attempt < retries - 1:
                time.sleep(backoff * (2**attempt))
    raise NetworkError(f"GET failed: {url} ({last})")


def http_get_json(url: str, **kw) -> dict:
    return json.loads(http_get(url, **kw))
