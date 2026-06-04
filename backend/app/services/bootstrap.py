from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import ROLE_PERMISSIONS
from app.core.security import hash_password, normalize_role
from app.models.operations import Permission, Role, RolePermission
from app.models.user import User


ROLE_DESCRIPTIONS = {
    'Director': 'Executive access to program health, forecasts, and reports.',
    'Host': 'Operations access to sessions, attendance imports, and alerts.',
    'Mentor': 'Student success access to coaching queues, assignments, and insights.',
    'Admin': 'Platform administration access to security, RBAC, and audit workflows.',
}


def bootstrap_rbac(db: Session) -> None:
    for role_name, description in ROLE_DESCRIPTIONS.items():
        role = db.get(Role, role_name)
        if not role:
            db.add(Role(name=role_name, description=description))

    db.flush()

    for permissions in ROLE_PERMISSIONS.values():
        for permission_name in permissions:
            resource, action = permission_name.split(':', 1)
            permission = db.scalar(select(Permission).where(Permission.resource == resource, Permission.action == action))
            if not permission:
                permission = Permission(resource=resource, action=action, description=f'{action} access for {resource}')
                db.add(permission)
                db.flush()

    db.flush()

    for role_name, permissions in ROLE_PERMISSIONS.items():
        for permission_name in permissions:
            resource, action = permission_name.split(':', 1)
            permission = db.scalar(select(Permission).where(Permission.resource == resource, Permission.action == action))
            if not permission:
                continue
            existing = db.get(RolePermission, {'role_name': role_name, 'permission_id': permission.id})
            if not existing:
                db.add(RolePermission(role_name=role_name, permission_id=permission.id))

    db.commit()


def bootstrap_initial_admin(db: Session) -> None:
    if not settings.initial_admin_email or not settings.initial_admin_password:
        return

    role = normalize_role(settings.initial_admin_role)
    user = db.scalar(select(User).where(User.email == settings.initial_admin_email.lower()))
    if user:
        if not user.password_hash:
            user.password_hash = hash_password(settings.initial_admin_password)
        user.role = role
        user.is_active = True
    else:
        db.add(
            User(
                uid=f'local-admin:{settings.initial_admin_email.lower()}',
                email=settings.initial_admin_email.lower(),
                name=settings.initial_admin_name,
                role=role,
                password_hash=hash_password(settings.initial_admin_password),
                is_active=True,
            )
        )
    db.commit()
