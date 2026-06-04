"""Thin async wrapper around the Anthropic Messages API.

Every outgoing payload must pass through `_strip_persons()` before being sent.
Provider errors are always wrapped in `AIServiceError`; raw SDK exceptions never
escape this module.
"""
from __future__ import annotations

import asyncio
import json as _json
import logging
from typing import Any

from anthropic import APIError, AsyncAnthropic, AuthenticationError, RateLimitError

from app.config import settings

logger = logging.getLogger("einsatzleiter.ai")

_PERSON_KEYS: frozenset[str] = frozenset({
    "name",
    "member",
    "member_id",
    "commander",
    "commander_member_id",
    "commander_id",
    "leader",
    "leader_member",
    "incident_leader_user_id",
    "incident_leader_member_id",
    "created_by_user_id",
    "user",
    "user_id",
    "email",
    "phone",
    "contact",
    "first_name",
    "last_name",
    "fullname",
    "username",
})


class AIServiceError(Exception):
    """Raised when the AI provider call fails; never exposes raw provider errors."""


def is_enabled() -> bool:
    """Return True only when AI_ENABLED=true AND an API key is configured."""
    return settings.AI_ENABLED and bool(settings.ANTHROPIC_API_KEY)


def _strip_persons(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively remove known person-data keys from a payload dict."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        if key in _PERSON_KEYS:
            continue
        if isinstance(value, dict):
            result[key] = _strip_persons(value)
        elif isinstance(value, list):
            result[key] = [
                _strip_persons(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


async def complete(
    system: str,
    user: str,
    *,
    fast: bool = False,
    max_tokens: int | None = None,
) -> str:
    """Call the Anthropic Messages API and return the text response.

    Raises AIServiceError on any provider failure or timeout.
    Never raises raw SDK exceptions.
    """
    if not is_enabled():
        raise AIServiceError("KI-Dienst ist nicht aktiviert.")

    model = settings.AI_MODEL_FAST if fast else settings.AI_MODEL_DEFAULT
    tokens = max_tokens or settings.AI_MAX_TOKENS
    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    try:
        response = await asyncio.wait_for(
            client.messages.create(
                model=model,
                max_tokens=tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            ),
            timeout=float(settings.AI_TIMEOUT),
        )
    except TimeoutError:
        logger.warning("AI provider timeout after %ss (model=%s)", settings.AI_TIMEOUT, model)
        raise AIServiceError("KI-Dienst hat nicht rechtzeitig geantwortet (Timeout).")
    except AuthenticationError:
        logger.error("AI provider authentication failed")
        raise AIServiceError("KI-Dienst: Authentifizierungsfehler – API-Key prüfen.")
    except RateLimitError:
        logger.warning("AI provider rate limit exceeded (model=%s)", model)
        raise AIServiceError("KI-Dienst: Rate-Limit überschritten, bitte kurz warten.")
    except APIError as exc:
        logger.error("AI provider error: %s", exc)
        raise AIServiceError("KI-Dienst temporär nicht verfügbar.") from exc

    if not response.content:
        raise AIServiceError("KI-Dienst hat eine leere Antwort geliefert.")

    return response.content[0].text


_REPORT_SYSTEM = (
    "Du bist ein sachlicher Berichtsassistent der Feuerwehr. "
    "Erstelle aus den gelieferten Einsatzdaten einen strukturierten deutschen Verlaufsbericht "
    "(3–8 Sätze Fließtext, de-AT, sachlich, unpersönlich). "
    "Nutze ausschließlich die gelieferten Fakten. "
    "Was unbekannt oder nicht dokumentiert ist, bezeichnest du als 'nicht dokumentiert'. "
    "Keine Erfindungen, keine Spekulation. "
    "Ausgabe: nur der Berichtstext, ohne Überschrift, ohne Formatierung."
)


async def generate_report_draft(incident_data: dict) -> str:
    """Generate a German prose incident report draft from structured incident data."""
    safe_data = _strip_persons(incident_data)
    user_msg = f"Einsatzdaten (JSON):\n{_json.dumps(safe_data, ensure_ascii=False, indent=2)}"
    return await complete(_REPORT_SYSTEM, user_msg)
