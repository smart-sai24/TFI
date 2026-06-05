from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.operations import AssignmentAuthenticityCheck

MODEL_VERSION = 'authenticity-v1'


def run_authenticity_check(
    db: Session,
    title: str,
    submission_text: str,
    github_url: str | None = None,
    assignment_id: int | None = None,
    submission_id: int | None = None,
    student_id: int | None = None,
) -> dict[str, Any]:
    normalized_text = normalize_text(submission_text)
    fingerprint = text_fingerprint(normalized_text)
    content_hash = hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()
    similarity = similarity_check(db, fingerprint, assignment_id, student_id)
    ai_risk = ai_generated_content_risk(submission_text)
    code_quality = code_quality_score(submission_text)
    github_evidence = github_activity_check(github_url)
    github_score = float(github_evidence['score'])
    originality_score = calculate_originality_score(similarity['similarity_score'], ai_risk['score'], code_quality['score'], github_score)
    risk_level = risk_level_for(originality_score, similarity['similarity_score'], ai_risk['score'])
    findings = build_findings(similarity, ai_risk, code_quality, github_evidence, originality_score)
    recommendations = build_recommendations(similarity, ai_risk, code_quality, github_evidence, risk_level)

    check = AssignmentAuthenticityCheck(
        assignment_id=assignment_id,
        submission_id=submission_id,
        student_id=student_id,
        title=title.strip() or 'Assignment submission',
        content_hash=content_hash,
        similarity_score=similarity['similarity_score'],
        ai_generated_risk=ai_risk['score'],
        code_quality_score=code_quality['score'],
        github_activity_score=github_score,
        originality_score=originality_score,
        risk_level=risk_level,
        matched_submission_id=similarity.get('matched_submission_id'),
        fingerprint=fingerprint,
        github_evidence=github_evidence,
        findings=findings,
        recommendations=recommendations,
        model_version=MODEL_VERSION,
    )
    db.add(check)
    db.commit()
    db.refresh(check)

    return {
        'id': check.id,
        'title': check.title,
        'similarity_score': check.similarity_score,
        'ai_generated_risk': check.ai_generated_risk,
        'code_quality_score': check.code_quality_score,
        'github_activity_score': check.github_activity_score,
        'originality_score': check.originality_score,
        'risk_level': check.risk_level,
        'matched_submission_id': check.matched_submission_id,
        'github_evidence': check.github_evidence,
        'findings': check.findings,
        'recommendations': check.recommendations,
        'model_version': check.model_version,
    }


def normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text.strip().lower())


def text_fingerprint(text: str) -> list[str]:
    tokens = re.findall(r'[a-zA-Z0-9_]+', text)
    if len(tokens) < 5:
        return [hashlib.sha256(' '.join(tokens).encode('utf-8')).hexdigest()]
    shingles = [' '.join(tokens[index:index + 5]) for index in range(len(tokens) - 4)]
    return sorted({hashlib.sha256(shingle.encode('utf-8')).hexdigest()[:16] for shingle in shingles})


def similarity_check(db: Session, fingerprint: list[str], assignment_id: int | None, student_id: int | None) -> dict[str, Any]:
    current = set(fingerprint)
    if not current:
        return {'similarity_score': 0.0, 'matched_submission_id': None}

    query = select(AssignmentAuthenticityCheck)
    if assignment_id is not None:
        query = query.where(AssignmentAuthenticityCheck.assignment_id == assignment_id)
    checks = db.scalars(query.order_by(AssignmentAuthenticityCheck.created_at.desc()).limit(250)).all()

    best_score = 0.0
    best_submission_id = None
    best_check_id = None
    for check in checks:
        if student_id is not None and check.student_id == student_id:
            continue
        prior = set(check.fingerprint or [])
        if not prior:
            continue
        score = round((len(current & prior) / max(len(current | prior), 1)) * 100, 1)
        if score > best_score:
            best_score = score
            best_submission_id = check.submission_id
            best_check_id = check.id

    return {'similarity_score': best_score, 'matched_submission_id': best_submission_id, 'matched_check_id': best_check_id}


def ai_generated_content_risk(text: str) -> dict[str, Any]:
    lower_text = text.lower()
    words = re.findall(r'[a-zA-Z]+', lower_text)
    unique_ratio = len(set(words)) / max(len(words), 1)
    risk = 15.0
    signals: list[str] = []

    generic_phrases = [
        'in conclusion',
        'this project demonstrates',
        'it is important to note',
        'as an ai language model',
        'overall this assignment',
        'various aspects',
        'comprehensive understanding',
    ]
    matches = [phrase for phrase in generic_phrases if phrase in lower_text]
    if matches:
        risk += min(len(matches) * 12, 36)
        signals.append(f"Generic AI-style phrases found: {', '.join(matches[:3])}")
    if len(words) > 120 and unique_ratio < 0.42:
        risk += 18
        signals.append('Low vocabulary diversity for a long submission')
    if not any(marker in lower_text for marker in ['i built', 'i fixed', 'commit', 'screenshot', 'tested', 'bug', 'debug']):
        risk += 15
        signals.append('Lacks personal implementation evidence')
    if lower_text.count('therefore') + lower_text.count('furthermore') + lower_text.count('moreover') >= 3:
        risk += 10
        signals.append('Overuses formal connector language')
    if re.search(r'\b(api|database|component|function|class|test|route|schema)\b', lower_text):
        risk -= 8
        signals.append('Includes concrete technical terms')
    if re.search(r'\b(error|debug|fixed|issue|challenge|commit|pytest|unit test)\b', lower_text):
        risk -= 10
        signals.append('Includes implementation process evidence')

    return {'score': round(min(max(risk, 0), 100), 1), 'signals': signals or ['No strong AI-generated content signals detected']}


def code_quality_score(text: str) -> dict[str, Any]:
    lower_text = text.lower()
    score = 35.0
    signals: list[str] = []
    code_markers = ['def ', 'function ', 'class ', 'const ', 'let ', 'import ', 'return ', 'try:', 'except', 'catch', 'select ', 'public ']
    if any(marker in lower_text for marker in code_markers):
        score += 18
        signals.append('Contains recognizable code structure')
    if re.search(r'\b(test|pytest|unit test|jest|validation|assert)\b', lower_text):
        score += 18
        signals.append('Mentions tests or validation')
    if re.search(r'\b(error handling|try|catch|except|rollback|edge case)\b', lower_text):
        score += 12
        signals.append('Mentions error handling or edge cases')
    if re.search(r'\b(component|api|database|model|schema|route|algorithm)\b', lower_text):
        score += 10
        signals.append('Uses relevant engineering concepts')
    if len(text.strip()) < 250:
        score -= 18
        signals.append('Submission is too short for deep code-quality confidence')
    if lower_text.count('todo') >= 3:
        score -= 10
        signals.append('Multiple TODO markers reduce completeness confidence')
    return {'score': round(min(max(score, 0), 100), 1), 'signals': signals or ['No code-quality evidence found']}


def github_activity_check(github_url: str | None) -> dict[str, Any]:
    parsed = parse_github_url(github_url)
    if not parsed:
        return {'score': 0.0, 'status': 'no_repo_provided', 'signals': ['No GitHub repository URL provided']}

    owner, repo = parsed
    headers = {'Accept': 'application/vnd.github+json'}
    if settings.github_api_token:
        headers['Authorization'] = f'Bearer {settings.github_api_token}'

    evidence: dict[str, Any] = {'score': 20.0, 'status': 'unverified', 'owner': owner, 'repo': repo, 'signals': ['GitHub URL was provided']}
    try:
        with httpx.Client(timeout=settings.github_request_timeout_seconds) as client:
            repo_response = client.get(f'https://api.github.com/repos/{owner}/{repo}', headers=headers)
            repo_response.raise_for_status()
            repo_data = repo_response.json()
            commits_response = client.get(f'https://api.github.com/repos/{owner}/{repo}/commits', headers=headers, params={'per_page': 10})
            commits_response.raise_for_status()
            commits = commits_response.json()
    except Exception as exc:
        evidence['signals'].append(f'GitHub activity could not be verified: {exc}')
        return evidence

    pushed_at = repo_data.get('pushed_at')
    commit_count = len(commits) if isinstance(commits, list) else 0
    score = 45.0
    if commit_count >= 3:
        score += 25
        evidence['signals'].append(f'{commit_count} recent commits found')
    if repo_data.get('stargazers_count', 0) >= 0:
        score += 5
    if pushed_at:
        score += 15 if is_recent_iso_datetime(str(pushed_at)) else 5
        evidence['signals'].append(f'Repository last pushed at {pushed_at}')
    evidence.update(
        {
            'score': round(min(score, 100), 1),
            'status': 'verified',
            'repo_url': repo_data.get('html_url'),
            'default_branch': repo_data.get('default_branch'),
            'recent_commit_count': commit_count,
            'pushed_at': pushed_at,
        }
    )
    return evidence


def parse_github_url(github_url: str | None) -> tuple[str, str] | None:
    if not github_url:
        return None
    parsed = urlparse(github_url.strip())
    if parsed.netloc.lower() not in {'github.com', 'www.github.com'}:
        return None
    parts = [part for part in parsed.path.strip('/').split('/') if part]
    if len(parts) < 2:
        return None
    return parts[0], parts[1].replace('.git', '')


def is_recent_iso_datetime(value: str) -> bool:
    try:
        pushed_at = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return False
    return (datetime.now(timezone.utc) - pushed_at).days <= 45


def calculate_originality_score(similarity_score: float, ai_risk: float, code_quality: float, github_score: float) -> float:
    originality = 100 - similarity_score * 0.55 - ai_risk * 0.25 + code_quality * 0.12 + github_score * 0.08
    return round(min(max(originality, 0), 100), 1)


def risk_level_for(originality_score: float, similarity_score: float, ai_risk: float) -> str:
    if similarity_score >= 75 or originality_score < 35 or ai_risk >= 80:
        return 'Critical'
    if similarity_score >= 50 or originality_score < 55 or ai_risk >= 60:
        return 'High'
    if similarity_score >= 30 or originality_score < 72 or ai_risk >= 40:
        return 'Medium'
    return 'Low'


def build_findings(
    similarity: dict[str, Any],
    ai_risk: dict[str, Any],
    code_quality: dict[str, Any],
    github_evidence: dict[str, Any],
    originality_score: float,
) -> list[str]:
    return [
        f"Similarity score is {similarity['similarity_score']}%.",
        f"AI-generated content risk is {ai_risk['score']}%.",
        f"Code quality evidence score is {code_quality['score']}%.",
        f"GitHub activity score is {github_evidence['score']}%.",
        f"Overall originality score is {originality_score}%.",
        *ai_risk['signals'][:3],
        *code_quality['signals'][:3],
        *github_evidence['signals'][:3],
    ]


def build_recommendations(
    similarity: dict[str, Any],
    ai_risk: dict[str, Any],
    code_quality: dict[str, Any],
    github_evidence: dict[str, Any],
    risk_level: str,
) -> list[str]:
    recommendations: list[str] = []
    if risk_level in {'High', 'Critical'}:
        recommendations.append('Send this submission for mentor manual review before approval.')
    if similarity['similarity_score'] >= 40:
        recommendations.append('Ask the student to explain implementation choices in a short viva.')
    if ai_risk['score'] >= 45:
        recommendations.append('Request proof of work such as commits, screenshots, tests, or demo video.')
    if code_quality['score'] < 60:
        recommendations.append('Ask for improved code structure, testing evidence, and error handling notes.')
    if github_evidence['status'] != 'verified':
        recommendations.append('Ask for a valid GitHub repository link or commit history evidence.')
    return recommendations or ['Submission appears authentic enough for normal mentor review.']
