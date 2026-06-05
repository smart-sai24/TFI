from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.ai.providers import AiProviderUnavailable, generate_live_text
from app.services.operational_intelligence import answer_assistant_query


def answer_mentor_query(db: Session, query: str) -> dict[str, Any]:
    deterministic = answer_assistant_query(db, query)
    context_rows = deterministic['results'][:12]
    system_prompt = (
        'You are the TFI Mentor AI assistant. Answer using only the supplied platform data. '
        'Be concise, operational, and include next actions when useful.'
    )
    user_prompt = (
        f'Mentor question: {query}\n\n'
        f'Matching platform records: {context_rows}\n\n'
        'Return a helpful mentor-facing summary and action guidance.'
    )
    try:
        live = generate_live_text(system_prompt, user_prompt)
    except (AiProviderUnavailable, Exception) as exc:
        deterministic['ai_provider'] = 'local'
        deterministic['ai_status'] = 'fallback'
        deterministic['ai_error'] = str(exc)
        return deterministic

    deterministic['summary'] = live.text or deterministic['summary']
    deterministic['ai_provider'] = live.provider
    deterministic['ai_model'] = live.model
    deterministic['ai_status'] = 'live'
    return deterministic
