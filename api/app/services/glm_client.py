from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any


class GLMClient:
    def __init__(self, api_key: str, base_url: str, model: str, timeout: int = 45) -> None:
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model = model.strip()
        self.timeout = timeout

    def _extract_json_payload(self, content: str) -> dict[str, Any]:
        content = content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if not match:
                raise ValueError("GLM response does not contain JSON payload.")
            return json.loads(match.group(0))

    def review(self, sentences: list[dict[str, str]]) -> list[dict[str, Any]]:
        if not self.api_key:
            return []

        prompt = (
            "You are an academic consistency reviewer. "
            "Analyze the sentence list and return JSON with shape: "
            '{"issues":[{"type":"term|logic|citation_figure","sentence_id":"s-1","severity":"low|medium|high","title":"...","detail":"..."}]}. '
            "Only return JSON."
        )

        user_payload = {"sentences": sentences}
        request_body = {
            "model": self.model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_object"},
        }

        encoded = json.dumps(request_body).encode("utf-8")
        req = urllib.request.Request(
            url=f"{self.base_url}/chat/completions",
            data=encoded,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except urllib.error.URLError:
            return []
        except urllib.error.HTTPError:
            return []

        try:
            payload = json.loads(body)
            content = payload["choices"][0]["message"]["content"]
            parsed = self._extract_json_payload(content)
            issues = parsed.get("issues", [])
            if not isinstance(issues, list):
                return []
            return [item for item in issues if isinstance(item, dict)]
        except (KeyError, IndexError, ValueError, TypeError, json.JSONDecodeError):
            return []

