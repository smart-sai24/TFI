from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy.orm import Session

from app.ai.providers import AiProviderUnavailable, generate_live_text
from app.core.config import settings
from app.services.ai_intelligence import executive_ai_report


def generate_ai_report(db: Session, report_type: str = 'Weekly Report', output_format: str = 'markdown') -> dict[str, Any]:
    report = executive_ai_report(db)
    content = _render_markdown(report_type, report)
    content = _enhance_report_content(report_type, report, content)
    normalized_format = _normalize_format(output_format)
    file_path = _write_report_file(report_type, normalized_format, content, report)
    return {
        'report_type': report_type,
        'output_format': normalized_format,
        'status': 'completed',
        'content': content,
        'file_url': file_path,
        'payload': report,
        'exports': ['PDF', 'HTML', 'Markdown'],
    }


def _render_markdown(report_type: str, report: dict[str, Any]) -> str:
    recommendations = '\n'.join(f"- {item}" for item in report['recommendations'])
    forecast_mix = '\n'.join(f"- {name}: {count}" for name, count in report['performance_forecast_mix'].items()) or '- No forecast data yet'
    return (
        f"# {report_type}\n\n"
        f"## Executive Summary\n{report['narrative']}\n\n"
        f"## Health Score\n{report['health_score']}/100\n\n"
        f"## Performance Forecast Mix\n{forecast_mix}\n\n"
        f"## Recommendations\n{recommendations}\n"
    )


def _enhance_report_content(report_type: str, report: dict[str, Any], fallback_content: str) -> str:
    system_prompt = (
        'You are the TFI executive AI report generator. Use only supplied metrics. '
        'Return a board-ready markdown report with summary, trends, risks, and recommendations.'
    )
    try:
        live = generate_live_text(system_prompt, f'Report type: {report_type}\n\nMetrics: {report}')
    except (AiProviderUnavailable, Exception):
        return fallback_content
    return live.text or fallback_content


def _normalize_format(output_format: str) -> str:
    normalized = output_format.strip().lower()
    if normalized in {'pdf'}:
        return 'pdf'
    if normalized in {'html', 'htm'}:
        return 'html'
    return 'markdown'


def _report_dir() -> Path:
    path = Path(settings.ai_storage_dir) / 'reports'
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_slug(value: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', value.strip()).strip('-').lower()
    return slug or 'ai-report'


def _write_report_file(report_type: str, output_format: str, content: str, report: dict[str, Any]) -> str:
    filename = f"{_safe_slug(report_type)}-{report.get('health_score', 'snapshot')}"
    if output_format == 'pdf':
        path = _report_dir() / f'{filename}.pdf'
        _write_pdf(path, report_type, content)
        return str(path)
    if output_format == 'html':
        path = _report_dir() / f'{filename}.html'
        path.write_text(_render_html(report_type, content), encoding='utf-8')
        return str(path)

    path = _report_dir() / f'{filename}.md'
    path.write_text(content, encoding='utf-8')
    return str(path)


def _render_html(report_type: str, content: str) -> str:
    escaped = html.escape(content)
    body = escaped.replace('\n', '<br />\n')
    return (
        '<!doctype html><html><head><meta charset="utf-8" />'
        f'<title>{html.escape(report_type)}</title>'
        '<style>body{font-family:Inter,Arial,sans-serif;max-width:920px;margin:40px auto;line-height:1.6;color:#111827}'
        'h1,h2{color:#082f49}.meta{color:#64748b}</style></head><body>'
        f'<main>{body}</main></body></html>'
    )


def _write_pdf(path: Path, report_type: str, content: str) -> None:
    document = SimpleDocTemplate(str(path), pagesize=A4, title=report_type)
    styles = getSampleStyleSheet()
    story = [Paragraph(html.escape(report_type), styles['Title']), Spacer(1, 12)]
    for block in content.split('\n\n'):
        cleaned = block.strip()
        if not cleaned:
            continue
        if cleaned.startswith('# '):
            story.append(Paragraph(html.escape(cleaned[2:]), styles['Heading1']))
        elif cleaned.startswith('## '):
            story.append(Paragraph(html.escape(cleaned[3:]), styles['Heading2']))
        else:
            story.append(Paragraph(html.escape(cleaned).replace('\n', '<br />'), styles['BodyText']))
        story.append(Spacer(1, 10))
    document.build(story)
