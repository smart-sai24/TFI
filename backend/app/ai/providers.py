from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings


@dataclass
class AiProviderResult:
    provider: str
    model: str
    text: str
    raw: dict[str, Any]


class AiProviderUnavailable(RuntimeError):
    pass


def live_provider_name() -> str:
    provider = settings.ai_provider.strip().lower()
    if provider in {'openai', 'gemini'}:
        return provider
    if settings.openai_api_key:
        return 'openai'
    if settings.gemini_api_key:
        return 'gemini'
    return 'local'


def live_ai_configured() -> bool:
    if not settings.ai_live_enabled:
        return False
    provider = live_provider_name()
    return (provider == 'openai' and bool(settings.openai_api_key)) or (provider == 'gemini' and bool(settings.gemini_api_key))


def generate_live_text(system_prompt: str, user_prompt: str) -> AiProviderResult:
    if not live_ai_configured():
        raise AiProviderUnavailable('Live AI is disabled or no provider API key is configured')

    provider = live_provider_name()
    if provider == 'openai':
        return _openai_response(system_prompt, user_prompt)
    if provider == 'gemini':
        return _gemini_response(system_prompt, user_prompt)
    raise AiProviderUnavailable(f'Unsupported AI provider: {provider}')


def _openai_response(system_prompt: str, user_prompt: str) -> AiProviderResult:
    payload = {
        'model': settings.openai_model,
        'input': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'max_output_tokens': 900,
    }
    with httpx.Client(timeout=settings.ai_request_timeout_seconds) as client:
        response = client.post(
            'https://api.openai.com/v1/responses',
            headers={
                'Authorization': f'Bearer {settings.openai_api_key}',
                'Content-Type': 'application/json',
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
    return AiProviderResult(provider='openai', model=settings.openai_model, text=_extract_openai_text(data), raw=data)


def _extract_openai_text(data: dict[str, Any]) -> str:
    output_text = data.get('output_text')
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    chunks: list[str] = []
    for item in data.get('output', []):
        if not isinstance(item, dict):
            continue
        for content in item.get('content', []):
            if isinstance(content, dict):
                text = content.get('text')
                if isinstance(text, str):
                    chunks.append(text)
    return '\n'.join(chunks).strip()


def _gemini_response(system_prompt: str, user_prompt: str) -> AiProviderResult:
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent'
    payload = {
        'systemInstruction': {'parts': [{'text': system_prompt}]},
        'contents': [{'role': 'user', 'parts': [{'text': user_prompt}]}],
        'generationConfig': {'maxOutputTokens': 900},
    }
    with httpx.Client(timeout=settings.ai_request_timeout_seconds) as client:
        response = client.post(url, params={'key': settings.gemini_api_key}, json=payload)
        response.raise_for_status()
        data = response.json()
    return AiProviderResult(provider='gemini', model=settings.gemini_model, text=_extract_gemini_text(data), raw=data)


def _extract_gemini_text(data: dict[str, Any]) -> str:
    chunks: list[str] = []
    for candidate in data.get('candidates', []):
        content = candidate.get('content') if isinstance(candidate, dict) else None
        if not isinstance(content, dict):
            continue
        for part in content.get('parts', []):
            if isinstance(part, dict) and isinstance(part.get('text'), str):
                chunks.append(part['text'])
    return '\n'.join(chunks).strip()
