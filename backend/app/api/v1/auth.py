from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_refresh_token, verify_firebase_token, verify_password
from app.db.session import get_db
from app.models.user import User
from app.services.rate_limit import login_rate_limit_key, login_rate_limiter

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class FirebaseSessionRequest(BaseModel):
    id_token: str
    role: str | None = None

class UserTokenResponse(BaseModel):
    uid: str
    email: EmailStr
    role: str
    access_token: str
    refresh_token: str | None = None
    token_type: str = 'bearer'
    expires_in: int
    refresh_expires_in: int | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


def issue_user_tokens(user: User) -> dict[str, object]:
    access_token, expires_in = create_access_token(user.uid, user.email, user.role)
    refresh_token, refresh_expires_in = create_refresh_token(user.uid, user.email, user.role)
    return {
        'uid': user.uid,
        'email': user.email,
        'role': user.role,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': expires_in,
        'refresh_expires_in': refresh_expires_in,
    }

@router.post('/login', response_model=UserTokenResponse)
def login(request: LoginRequest, http_request: Request, db: Session = Depends(get_db)):
    email = str(request.email).lower()
    rate_limit_key = login_rate_limit_key(http_request, email)
    login_rate_limiter.check(
        rate_limit_key,
        limit=settings.login_rate_limit_attempts,
        window_seconds=settings.login_rate_limit_window_seconds,
    )
    user = db.scalar(select(User).where(User.email == email))
    if not user or not user.is_active or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Invalid email or password')

    login_rate_limiter.reset(rate_limit_key)
    return issue_user_tokens(user)

@router.post('/session', response_model=UserTokenResponse)
def create_session(request: FirebaseSessionRequest, db: Session = Depends(get_db)):
    try:
        firebase_user = verify_firebase_token(request.id_token)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid Firebase token')

    email = firebase_user.get('email')
    uid = firebase_user.get('uid')
    if not email or not uid:
        raise HTTPException(status_code=401, detail='Firebase token must include uid and email')

    email_normalized = str(email).lower()
    user = db.scalar(
        select(User).where(
            (User.uid == str(uid)) | (User.email == email_normalized)
        )
    )
    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail='Firebase user is not provisioned for TFI Command Center')

    return issue_user_tokens(user)


@router.post('/refresh', response_model=UserTokenResponse)
def refresh_session(request: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_refresh_token(request.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail='Invalid or expired refresh token')

    user = db.scalar(select(User).where(User.uid == str(payload.get('sub', ''))))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail='User session is no longer active')

    return issue_user_tokens(user)

@router.get('/me', response_model=UserTokenResponse)
def me(user: CurrentUser = require_permission('dashboard:read')):
    token, expires_in = create_access_token(user.uid, user.email, user.role)
    return {
        'uid': user.uid,
        'email': user.email,
        'role': user.role,
        'access_token': token,
        'expires_in': expires_in,
    }
