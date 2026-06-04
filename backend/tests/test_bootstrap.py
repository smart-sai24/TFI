import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.operations import Permission, Role, RolePermission
from app.models.user import User
from app.services.bootstrap import LOCAL_ROLE_PASSWORD, LOCAL_ROLE_USERS, bootstrap_initial_admin, bootstrap_local_role_users, bootstrap_rbac
from app.core.security import verify_password


class LocalRoleBootstrapTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine('sqlite:///:memory:', future=True)
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine, future=True)

    def test_local_role_users_are_seeded_in_local_environment(self):
        with self.Session() as session:
            for role, _, _ in LOCAL_ROLE_USERS:
                session.add(Role(name=role, description=role))
            session.commit()

            with patch('app.services.bootstrap.settings.environment', 'local'):
                bootstrap_local_role_users(session)

            users = session.scalars(select(User).order_by(User.email)).all()

        self.assertEqual(len(users), len(LOCAL_ROLE_USERS))
        self.assertEqual({user.role for user in users}, {'Director', 'Host', 'Mentor', 'Admin'})
        self.assertTrue(all(verify_password(LOCAL_ROLE_PASSWORD, user.password_hash) for user in users))

    def test_local_role_users_are_skipped_outside_local_environment(self):
        with self.Session() as session:
            for role, _, _ in LOCAL_ROLE_USERS:
                session.add(Role(name=role, description=role))
            session.commit()

            with patch('app.services.bootstrap.settings.environment', 'production'):
                bootstrap_local_role_users(session)

            user_count = session.scalar(select(func.count()).select_from(User))

        self.assertEqual(user_count, 0)

    def test_rbac_bootstrap_is_idempotent(self):
        with self.Session() as session:
            bootstrap_rbac(session)
            bootstrap_rbac(session)

            role_count = session.scalar(select(func.count()).select_from(Role))
            permission_count = session.scalar(select(func.count()).select_from(Permission))
            role_permission_count = session.scalar(select(func.count()).select_from(RolePermission))

        self.assertEqual(role_count, 4)
        self.assertGreater(permission_count, 0)
        self.assertGreater(role_permission_count, 0)

    def test_initial_admin_bootstrap_creates_and_updates_user(self):
        with self.Session() as session:
            session.add(Role(name='Admin', description='Administrator'))
            session.commit()

            with patch('app.services.bootstrap.settings.initial_admin_email', 'root@example.com'), \
                 patch('app.services.bootstrap.settings.initial_admin_password', 'Secret123!'), \
                 patch('app.services.bootstrap.settings.initial_admin_role', 'Admin'), \
                 patch('app.services.bootstrap.settings.initial_admin_name', 'Root User'):
                bootstrap_initial_admin(session)
                bootstrap_initial_admin(session)

            user = session.scalar(select(User).where(User.email == 'root@example.com'))
            user_count = session.scalar(select(func.count()).select_from(User))

        self.assertEqual(user_count, 1)
        self.assertEqual(user.role, 'Admin')
        self.assertTrue(verify_password('Secret123!', user.password_hash))


if __name__ == '__main__':
    unittest.main()
