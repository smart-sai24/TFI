import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings


ALGORITHM = 'HS256'

VALID_ROLES = {'Director', 'Host', 'Mentor', 'Admin'}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    'Director': {
        'dashboard:read',
        'reports:read',
        'reports:generate',
        'intelligence:read',
        'notifications:read',
        'notifications:send',
    },
    'Host': {
        'dashboard:read',
        'attendance:import',
        'attendance:read',
        'reports:read',
        'intelligence:read',
        'notifications:read',
        'notifications:send',
    },
    'Mentor': {
        'dashboard:read',
        'assignments:read',
        'reports:read',
        'intelligence:read',
        'notifications:read',
        'notifications:send',
    },
    'Admin': {
        'dashboard:read',
        'attendance:import',
        'attendance:read',
        'reports:read',
        'reports:generate',
        'intelligence:read',
        'notifications:read',
        'notifications:send',
        'system:admin',
    },
}


def normalize_role(role: str) -> str:
    cleaned = role.strip()
    for valid_role in VALID_ROLES:
        if cleaned.casefold() == valid_role.casefold():
            return valid_role
    raise ValueError(f'Invalid role: {role}')


def create_access_token(subject: str, email: str, role: str) -> tuple[str, int]:
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expires_at = datetime.now(timezone.utc) + expires_delta
    payload: dict[str, Any] = {
        'sub': subject,
        'email': email,
        'role': normalize_role(role),
        'exp': expires_at,
        'iat': datetime.now(timezone.utc),
        'iss': 'tfi-command-center',
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM), int(expires_delta.total_seconds())


def create_refresh_token(subject: str, email: str, role: str) -> tuple[str, int]:
    expires_delta = timedelta(minutes=settings.refresh_token_expire_minutes)
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        'sub': subject,
        'email': email,
        'role': normalize_role(role),
        'typ': 'refresh',
        'jti': base64.urlsafe_b64encode(os.urandom(18)).decode().rstrip('='),
        'exp': now + expires_delta,
        'iat': now,
        'iss': 'tfi-command-center',
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM), int(expires_delta.total_seconds())


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM], issuer='tfi-command-center')
    except JWTError:
        return None


def decode_refresh_token(token: str) -> dict[str, Any] | None:
    payload = decode_access_token(token)
    if not payload or payload.get('typ') != 'refresh':
        return None
    return payload


def role_has_permission(role: str, permission: str) -> bool:
    try:
        normalized_role = normalize_role(role)
    except ValueError:
        return False
    return permission in ROLE_PERMISSIONS.get(normalized_role, set())


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    iterations = 390000
    derived = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return f'pbkdf2_sha256${iterations}${base64.b64encode(salt).decode()}${base64.b64encode(derived).decode()}'


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        algorithm, iterations_value, salt_value, expected_value = password_hash.split('$', 3)
        if algorithm != 'pbkdf2_sha256':
            return False
        iterations = int(iterations_value)
        salt = base64.b64decode(salt_value)
        expected = base64.b64decode(expected_value)
        actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def verify_firebase_token(id_token: str) -> dict[str, Any]:
    if not settings.firebase_project_id or settings.firebase_project_id.startswith('your-'):
        raise RuntimeError('Firebase project is not configured')
    try:
        import firebase_admin
        from firebase_admin import auth, credentials
    except ImportError as exc:
        raise RuntimeError('firebase-admin dependency is not installed') from exc

    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.ApplicationDefault(), {'projectId': settings.firebase_project_id})
    return auth.verify_id_token(id_token)
