"""Real-time LLM-powered structured extraction from conversations and text.

Unlike llm_features.py (which does post-hoc summarization), this module
extracts structured MemoryEntry objects from raw text during capture —
similar to how Mem0 extracts entities and facts from user conversations.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .core import MemoryEntry
from .llm import LLMClient, get_llm_client

SYSTEM_EXTRACTOR = (
    "You are a structured memory extraction engine. Given a conversation or text, "
    "extract atomic facts, decisions, actions, and errors as structured memory entries. "
    "Each entry should be concise (1-2 sentences) and self-contained. "
    "Output valid JSON only."
)

SYSTEM_TEMPORAL_EXTRACTOR = (
    "You are a temporal knowledge extraction engine. Given text, extract facts that have "
    "validity windows — e.g., 'used Redux until March 2024, then switched to Zustand'. "
    "For each fact, include valid_from and valid_until ISO timestamps when known. "
    "Output valid JSON only."
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize_json(text: str) -> str:
    """Strip markdown fences and extra whitespace from LLM JSON output."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def extract_memories_from_text(
    text: str,
    project: str = "default",
    session_id: str = "",
    source: str = "llm-extract",
    client: LLMClient | None = None,
) -> list[MemoryEntry]:
    """Extract structured MemoryEntry objects from arbitrary text using an LLM.

    Falls back to an empty list if no LLM is available.
    """
    client = client or get_llm_client()
    if not client.is_available():
        return []

    prompt = (
        "Extract structured memories from the following text. "
        "Return a JSON array of objects with these keys:\n"
        "- content (string, required): the atomic memory text\n"
        "- category (string, one of: fact, decision, action, preference, error)\n"
        "- confidence (float, 0.0-1.0): how certain this memory is\n"
        "- tags (string, comma-separated): relevant tags\n"
        "Only include meaningful, non-redundant entries.\n\n"
        f"TEXT:\n{text}"
    )

    resp = client.chat(prompt, system=SYSTEM_EXTRACTOR)
    raw = _sanitize_json(resp.text)

    entries: list[MemoryEntry] = []
    try:
        data = json.loads(raw)
        if not isinstance(data, list):
            return []
        for item in data:
            if not isinstance(item, dict):
                continue
            content = item.get("content", "").strip()
            if not content:
                continue
            entries.append(
                MemoryEntry(
                    project=project,
                    session_id=session_id,
                    timestamp=_now_iso(),
                    category=item.get("category", "fact"),
                    content=content,
                    confidence=float(item.get("confidence", 0.8)),
                    source=source,
                    tags=item.get("tags", "llm-extract"),
                )
            )
    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    return entries


def extract_memories_from_conversation(
    messages: list[dict[str, str]],
    project: str = "default",
    session_id: str = "",
    source: str = "llm-extract",
    client: LLMClient | None = None,
) -> list[MemoryEntry]:
    """Extract memories from a conversation (list of {role, content} dicts).

    Falls back to empty list if no LLM is available.
    """
    client = client or get_llm_client()
    if not client.is_available():
        return []

    lines = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")
    transcript = "\n".join(lines)

    if not transcript:
        return []

    return extract_memories_from_text(
        transcript,
        project=project,
        session_id=session_id,
        source=source,
        client=client,
    )


def extract_temporal_facts(
    text: str,
    project: str = "default",
    session_id: str = "",
    source: str = "llm-extract-temporal",
    client: LLMClient | None = None,
) -> list[MemoryEntry]:
    """Extract time-bound facts with validity windows.

    Example input: 'We used Redux until March 2024, then switched to Zustand.'
    Output: two MemoryEntry objects with valid_from/valid_until set.
    """
    client = client or get_llm_client()
    if not client.is_available():
        return []

    prompt = (
        "Extract temporal facts from the following text. "
        "Return a JSON array of objects with these keys:\n"
        "- content (string, required): the atomic fact\n"
        "- category (string, one of: fact, decision, action, preference, error)\n"
        "- confidence (float, 0.0-1.0)\n"
        "- valid_from (string, ISO 8601 or empty): when this fact became true\n"
        "- valid_until (string, ISO 8601 or empty): when this fact stopped being true\n"
        "- tags (string, comma-separated)\n"
        "Only include facts with explicit or inferable time bounds.\n\n"
        f"TEXT:\n{text}"
    )

    resp = client.chat(prompt, system=SYSTEM_TEMPORAL_EXTRACTOR)
    raw = _sanitize_json(resp.text)

    entries: list[MemoryEntry] = []
    try:
        data = json.loads(raw)
        if not isinstance(data, list):
            return []
        for item in data:
            if not isinstance(item, dict):
                continue
            content = item.get("content", "").strip()
            if not content:
                continue
            entries.append(
                MemoryEntry(
                    project=project,
                    session_id=session_id,
                    timestamp=_now_iso(),
                    category=item.get("category", "fact"),
                    content=content,
                    confidence=float(item.get("confidence", 0.8)),
                    source=source,
                    tags=item.get("tags", "llm-extract,temporal"),
                    valid_from=item.get("valid_from", ""),
                    valid_until=item.get("valid_until", ""),
                )
            )
    except (json.JSONDecodeError, ValueError, TypeError):
        pass

    return entries


def extract_and_store(
    text: str,
    engine: Any,
    project: str = "default",
    session_id: str = "",
    source: str = "llm-extract",
    use_temporal: bool = False,
    client: LLMClient | None = None,
) -> list[int]:
    """Convenience: extract memories from text and store them in the engine.

    Returns list of stored memory IDs.
    """
    client = client or get_llm_client()
    if use_temporal:
        entries = extract_temporal_facts(
            text, project=project, session_id=session_id, source=source, client=client
        )
    else:
        entries = extract_memories_from_text(
            text, project=project, session_id=session_id, source=source, client=client
        )

    ids: list[int] = []
    for entry in entries:
        mid = engine.store(entry)
        ids.append(mid)
    return ids
