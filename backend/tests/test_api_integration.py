import unittest
from datetime import date

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1 import attendance, auth, dashboard, intelligence, reports
from app.core import config
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.models.operations import Role
from app.models.user import User
from app.services.rate_limit import login_rate_limiter


class ApiIntegrationTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            'sqlite://',
            connect_args={'check_same_thread': False},
            poolclass=StaticPool,
            future=True,
        )
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine, future=True)
        self.app = FastAPI()
        self.app.include_router(auth.router, prefix='/api/v1/auth')
        self.app.include_router(dashboard.router, prefix='/api/v1/dashboard')
        self.app.include_router(attendance.router, prefix='/api/v1/attendance')
        self.app.include_router(intelligence.router, prefix='/api/v1/intelligence')
        self.app.include_router(reports.router, prefix='/api/v1/reports')

        def override_get_db():
            with self.Session() as session:
                yield session

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)
        login_rate_limiter._buckets.clear()

        with self.Session() as session:
            for role in ['Director', 'Host', 'Mentor', 'Admin']:
                session.add(Role(name=role, description=f'{role} role'))
            session.add(
                User(
                    uid='admin-1',
                    email='admin@example.com',
                    name='Admin User',
                    role='Admin',
                    password_hash=hash_password('Secret123!'),
                    is_active=True,
                )
            )
            session.add(
                User(
                    uid='host-1',
                    email='host@example.com',
                    name='Host User',
                    role='Host',
                    password_hash=hash_password('Secret123!'),
                    is_active=True,
                )
            )
            session.add(
                User(
                    uid='mentor-1',
                    email='mentor@example.com',
                    name='Mentor User',
                    role='Mentor',
                    password_hash=hash_password('Secret123!'),
                    is_active=True,
                )
            )
            session.commit()

    def login(self, email: str) -> str:
        response = self.client.post('/api/v1/auth/login', json={'email': email, 'password': 'Secret123!'})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['access_token']

    def test_login_refresh_dashboard_and_report_generation(self):
        login_response = self.client.post('/api/v1/auth/login', json={'email': 'admin@example.com', 'password': 'Secret123!'})
        self.assertEqual(login_response.status_code, 200, login_response.text)
        login_data = login_response.json()
        self.assertEqual(login_data['role'], 'Admin')
        self.assertIn('refresh_token', login_data)

        refresh_response = self.client.post('/api/v1/auth/refresh', json={'refresh_token': login_data['refresh_token']})
        self.assertEqual(refresh_response.status_code, 200, refresh_response.text)
        refreshed_token = refresh_response.json()['access_token']

        dashboard_response = self.client.get('/api/v1/dashboard/summary', headers={'Authorization': f'Bearer {refreshed_token}'})
        self.assertEqual(dashboard_response.status_code, 200, dashboard_response.text)
        self.assertIn('api_metrics', dashboard_response.json())

        report_response = self.client.post(
            '/api/v1/reports/generate',
            json={'report_type': 'Weekly executive'},
            headers={'Authorization': f'Bearer {refreshed_token}'},
        )
        self.assertEqual(report_response.status_code, 200, report_response.text)
        self.assertEqual(report_response.json()['status'], 'completed')

    def test_attendance_import_accepts_valid_csv_for_host(self):
        token = self.login('host@example.com')
        csv_content = '\n'.join(
            [
                'student_name,registration_number,email,join_time,leave_time',
                'Asha Rao,TFI001,asha@example.com,2026-06-05T09:00:00,2026-06-05T10:35:00',
            ]
        )
        response = self.client.post(
            '/api/v1/attendance/import',
            headers={'Authorization': f'Bearer {token}'},
            data={
                'batch_name': 'Batch A',
                'domain': 'Python',
                'session_title': 'Morning Lab',
                'platform': 'Zoom',
                'session_date': str(date(2026, 6, 5)),
            },
            files={'file': ('attendance.csv', csv_content, 'text/csv')},
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['summary']['full'], 1)

    def test_permission_failures_are_enforced(self):
        mentor_token = self.login('mentor@example.com')
        response = self.client.post(
            '/api/v1/reports/generate',
            json={'report_type': 'Mentor export'},
            headers={'Authorization': f'Bearer {mentor_token}'},
        )
        self.assertEqual(response.status_code, 403)

    def test_intelligence_routes_return_operational_payloads(self):
        token = self.login('admin@example.com')
        headers = {'Authorization': f'Bearer {token}'}

        students = self.client.get('/api/v1/intelligence/students', headers=headers)
        student_page = self.client.get('/api/v1/intelligence/students/page?limit=10&offset=0', headers=headers)
        insights = self.client.get('/api/v1/intelligence/insights', headers=headers)
        assistant = self.client.post('/api/v1/intelligence/assistant', json={'query': 'top performers'}, headers=headers)
        ai_overview = self.client.get('/api/v1/intelligence/ai/overview', headers=headers)
        assignment_eval = self.client.post(
            '/api/v1/intelligence/ai/assignment-evaluation',
            json={
                'title': 'API Reflection',
                'submission_text': 'I built an API function with validation, database tests, and error handling. ' * 10,
            },
            headers=headers,
        )

        self.assertEqual(students.status_code, 200, students.text)
        self.assertEqual(student_page.status_code, 200, student_page.text)
        self.assertEqual(insights.status_code, 200, insights.text)
        self.assertEqual(assistant.status_code, 200, assistant.text)
        self.assertEqual(ai_overview.status_code, 200, ai_overview.text)
        self.assertEqual(assignment_eval.status_code, 200, assignment_eval.text)
        self.assertIsInstance(students.json(), list)
        self.assertIn('has_more', student_page.json())
        self.assertIn('insights', insights.json())
        self.assertIn('summary', assistant.json())
        self.assertIn('executive_report', ai_overview.json())
        self.assertIn('score', assignment_eval.json())

    def test_login_rate_limit_blocks_repeated_failures(self):
        original_limit = config.settings.login_rate_limit_attempts
        config.settings.login_rate_limit_attempts = 2
        try:
            for _ in range(2):
                response = self.client.post('/api/v1/auth/login', json={'email': 'admin@example.com', 'password': 'wrong'})
                self.assertEqual(response.status_code, 401)

            blocked = self.client.post('/api/v1/auth/login', json={'email': 'admin@example.com', 'password': 'wrong'})
            self.assertEqual(blocked.status_code, 429)
        finally:
            config.settings.login_rate_limit_attempts = original_limit


if __name__ == '__main__':
    unittest.main()
