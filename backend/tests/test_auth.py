import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.auth import FirebaseSessionRequest, create_session
from app.db.base import Base
from app.models.operations import Role
from app.models.user import User


class FirebaseSessionTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine('sqlite:///:memory:', future=True)
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine, future=True)

    def test_firebase_session_uses_database_role_not_client_role(self):
        with self.Session() as session:
            session.add(Role(name='Mentor', description='Student success'))
            session.add(
                User(
                    uid='firebase-uid-1',
                    email='mentor@example.com',
                    name='Mentor User',
                    role='Mentor',
                    is_active=True,
                )
            )
            session.commit()

            with patch(
                'app.api.v1.auth.verify_firebase_token',
                return_value={'uid': 'firebase-uid-1', 'email': 'mentor@example.com'},
            ):
                response = create_session(FirebaseSessionRequest(id_token='token', role='Admin'), session)

        self.assertEqual(response['uid'], 'firebase-uid-1')
        self.assertEqual(response['email'], 'mentor@example.com')
        self.assertEqual(response['role'], 'Mentor')
        self.assertIn('access_token', response)

    def test_firebase_session_rejects_unprovisioned_user(self):
        with self.Session() as session:
            with patch(
                'app.api.v1.auth.verify_firebase_token',
                return_value={'uid': 'new-firebase-uid', 'email': 'new@example.com'},
            ):
                with self.assertRaises(HTTPException) as raised:
                    create_session(FirebaseSessionRequest(id_token='token', role='Admin'), session)

        self.assertEqual(raised.exception.status_code, 403)


if __name__ == '__main__':
    unittest.main()
