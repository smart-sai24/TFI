from dataclasses import dataclass
from typing import Annotated, Any, Callable

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.security import decode_access_token, normalize_role, role_has_permission


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    uid: str
    email: str
    role: str


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    x_tfi_role: Annotated[str | None, Header(alias='X-TFI-Role')] = None,
) -> CurrentUser:
    if credentials:
        payload = decode_access_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired token')
        try:
            role = normalize_role(str(payload.get('role') or ''))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid role')
        return CurrentUser(
            uid=str(payload.get('sub', '')),
            email=str(payload.get('email', '')),
            role=role,
        )

    if settings.demo_mode:
        try:
            role = normalize_role(x_tfi_role or 'Director')
        except ValueError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid demo role')
        return CurrentUser(uid='demo-user', email='demo@techofutureindia.com', role=role)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required')


def require_permission(permission: str) -> Any:
    def dependency(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if not role_has_permission(user.role, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Insufficient permissions')
        return user

    return Depends(dependency)
