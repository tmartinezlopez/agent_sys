#!/usr/bin/env python3
"""Normaliza el uso de tokens que Codex CLI expone en JSON."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

FIELDS = {
    "inputTokens": ("input_tokens", "inputTokens", "prompt_tokens"),
    "outputTokens": ("output_tokens", "outputTokens", "completion_tokens"),
    "reasoningTokens": ("reasoning_tokens", "reasoningTokens"),
    "cachedInputTokens": ("cached_input_tokens", "cachedInputTokens", "cached_tokens"),
    "totalTokens": ("total_tokens", "totalTokens"),
}


def _integer(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _find(raw: dict[str, Any], keys: Iterable[str]) -> int | None:
    for key in keys:
        value = _integer(raw.get(key))
        if value is not None:
            return value
    return None


def normalize(raw: dict[str, Any], source: str = "codex-json") -> dict[str, Any]:
    result = {name: _find(raw, keys) for name, keys in FIELDS.items()}
    details = raw.get("output_tokens_details")
    if isinstance(details, dict) and result["reasoningTokens"] is None:
        result["reasoningTokens"] = _integer(details.get("reasoning_tokens"))
    input_details = raw.get("input_tokens_details")
    if isinstance(input_details, dict) and result["cachedInputTokens"] is None:
        result["cachedInputTokens"] = _integer(input_details.get("cached_tokens"))
    if result["totalTokens"] is None and result["inputTokens"] is not None and result["outputTokens"] is not None:
        result["totalTokens"] = result["inputTokens"] + result["outputTokens"]
    reported = any(value is not None for value in result.values())
    return {"status": "reported" if reported else "unknown", "source": source, **result}


def unknown(source: str = "codex-json") -> dict[str, Any]:
    return {"status": "unknown", "source": source,
            "inputTokens": None, "outputTokens": None,
            "reasoningTokens": None, "cachedInputTokens": None, "totalTokens": None}


def total_for(events: Iterable[dict[str, Any]]) -> tuple[int, int]:
    total = 0
    unknown_count = 0
    for event in events:
        usage = event.get("usage")
        value = usage.get("totalTokens") if isinstance(usage, dict) else None
        if isinstance(value, int) and value >= 0:
            total += value
        else:
            unknown_count += 1
    return total, unknown_count
