from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.core.security import create_access_token, normalize_role, verify_firebase_token, verify_password
from app.db.session import get_db
from app.models.user import User

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class FirebaseSessionRequest(BaseModel):
    id_token: str
    role: str

class UserTokenResponse(BaseModel):
    uid: str
    email: EmailStr
    role: str
    access_token: str
    token_type: str = 'bearer'
    expires_in: int

@router.post('/login', response_model=UserTokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(request.email).lower()))
    if not user or not user.is_active or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Invalid email or password')

    token, expires_in = create_access_token(user.uid, user.email, user.role)
    return {
        'uid': user.uid,
        'email': user.email,
        'role': user.role,
        'access_token': token,
        'expires_in': expires_in,
    }

@router.post('/session', response_model=UserTokenResponse)
def create_session(request: FirebaseSessionRequest):
    try:
        firebase_user = verify_firebase_token(request.id_token)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid Firebase token')

    role = normalize_role(request.role)
    email = firebase_user.get('email')
    uid = firebase_user.get('uid')
    if not email or not uid:
        raise HTTPException(status_code=401, detail='Firebase token must include uid and email')
    token, expires_in = create_access_token(str(uid), str(email), role)
    return {'uid': str(uid), 'email': str(email), 'role': role, 'access_token': token, 'expires_in': expires_in}

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
