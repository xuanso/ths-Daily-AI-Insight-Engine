from __future__ import annotations

import json
from typing import Any

from backend.services.deepseek_client import DeepSeekClient


class Agent:
    name = "base_agent"

    def __init__(self, client: DeepSeekClient) -> None:
        self.client = client

    def call_json(self, system: str, user_payload: dict[str, Any], temperature: float = 0.2) -> dict:
        return self.client.chat_json(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False, indent=2)},
            ],
            temperature=temperature,
        )


def ensure_list(value: Any, fallback: list | None = None) -> list:
    if isinstance(value, list):
        return value
    return fallback or []


def ensure_str(value: Any, fallback: str = "") -> str:
    if isinstance(value, str):
        return value.strip()
    return fallback

