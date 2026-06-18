import unittest
import tempfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1 import attendance, auth, dashboard, intelligence, notifications, reports
from app.core import config
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.models.operations import AiConversation, AiReport, Assignment, AssignmentAuthenticityCheck, AssignmentEvaluation, Batch, Notification, Role, Student, Submission
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
        self.app.include_router(notifications.router, prefix='/api/v1/notifications')
        self.app.include_router(reports.router, prefix='/api/v1/reports')

        def override_get_db():
            with self.Session() as session:
                yield session

        self.app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(self.app)
        login_rate_limiter._buckets.clear()
        self.storage_dir = tempfile.TemporaryDirectory()
        self.original_ai_storage_dir = config.settings.ai_storage_dir
        config.settings.ai_storage_dir = self.storage_dir.name

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

    def tearDown(self):
        config.settings.ai_storage_dir = self.original_ai_storage_dir
        self.storage_dir.cleanup()

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

    def test_attendance_import_accepts_zoom_style_csv(self):
        token = self.login('host@example.com')
        csv_content = '\n'.join(
            [
                'Topic,ID,Host,Duration (minutes),Start time,End time,Participants',
                'TFI Summer Internship 2026,81796405615,SIP_Tutor (technofuture.email@gmail.com),77,"06/16/2026 03:10:26 PM","06/16/2026 04:26:31 PM",67',
                '',
                'Name (original name),Email,Total duration (minutes),Guest',
                '24JR1A05q6,,76,Yes',
                '24JR1A05G0,,64,Yes',
                'Neha Chowdary,,59,Yes',
                '24JR1A05L3(Gorige MahaLakshmi),,77,Yes',
                'SIP_Tutor,technofuture.email@gmail.com,15,No',
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
        data = response.json()
        self.assertEqual(len(data['records']), 5)
        # Check that we parsed the names and reg numbers correctly
        records_map = {r['student_name']: r for r in data['records']}
        self.assertIn('24JR1A05Q6', records_map)
        self.assertIn('24JR1A05G0', records_map)
        self.assertIn('Gorige MahaLakshmi', records_map)
        self.assertIn('Neha Chowdary', records_map)
        self.assertIn('SIP_Tutor', records_map)

    def test_notification_nudges_queue_and_track_responses(self):
        token = self.login('admin@example.com')
        headers = {'Authorization': f'Bearer {token}'}

        with self.Session() as session:
            batch = Batch(name='AIML June', domain='AIML', status='active', mentor_uid='mentor-1')
            session.add(batch)
            session.flush()
            student = Student(
                batch_id=batch.id,
                registration_number='TFI-NUDGE-001',
                full_name='Asha Rao',
                email='asha@example.com',
                phone='+919999999999',
                domain='AIML',
                metadata_json={'parent_email': 'parent@example.com'},
            )
            session.add(student)
            session.flush()
            assignment = Assignment(
                batch_id=batch.id,
                title='Python recovery task',
                assignment_type='programming',
                due_at=datetime.now(timezone.utc) - timedelta(days=1),
                max_score=100,
            )
            session.add(assignment)
            session.flush()
            session.add(Submission(assignment_id=assignment.id, student_id=student.id, status='missing', is_late=True))
            session.commit()

        run_response = self.client.post('/api/v1/notifications/nudges/run', json={'auto_send': False}, headers=headers)
        self.assertEqual(run_response.status_code, 200, run_response.text)
        payload = run_response.json()
        self.assertEqual(payload['status'], 'completed')
        self.assertGreaterEqual(payload['created_notifications'], 1)

        list_response = self.client.get('/api/v1/notifications', headers=headers)
        self.assertEqual(list_response.status_code, 200, list_response.text)
        notification_id = list_response.json()['items'][0]['id']

        track_response = self.client.post(
            f'/api/v1/notifications/{notification_id}/response',
            json={'response_status': 'replied', 'notes': 'Student confirmed submission by evening.'},
            headers=headers,
        )
        self.assertEqual(track_response.status_code, 200, track_response.text)
        self.assertEqual(track_response.json()['response_status'], 'replied')

        duplicate_response = self.client.post('/api/v1/notifications/nudges/run', json={'auto_send': False}, headers=headers)
        self.assertEqual(duplicate_response.status_code, 200, duplicate_response.text)
        self.assertEqual(duplicate_response.json()['created_notifications'], 0)

        with self.Session() as session:
            self.assertGreaterEqual(session.query(Notification).count(), 1)

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
        attendance_prediction = self.client.get('/api/v1/intelligence/ai/attendance-prediction', headers=headers)
        performance_forecast = self.client.get('/api/v1/intelligence/ai/performance-forecast', headers=headers)
        risk_analysis = self.client.get('/api/v1/intelligence/ai/risk-analysis', headers=headers)
        model_status = self.client.get('/api/v1/intelligence/ai/model-status', headers=headers)
        model_retraining = self.client.post('/api/v1/intelligence/ai/model-retraining', headers=headers)
        mentor_chat = self.client.post('/api/v1/intelligence/ai/mentor-chat', json={'query': 'students at risk'}, headers=headers)
        ai_report = self.client.post(
            '/api/v1/intelligence/ai/report-generation',
            json={'report_type': 'Weekly executive', 'output_format': 'pdf'},
            headers=headers,
        )
        assignment_eval = self.client.post(
            '/api/v1/intelligence/ai/assignment-evaluation',
            json={
                'title': 'API Reflection',
                'submission_text': 'I built an API function with validation, database tests, and error handling. ' * 10,
            },
            headers=headers,
        )
        authenticity_check = self.client.post(
            '/api/v1/intelligence/ai/authenticity-check',
            json={
                'title': 'API Reflection',
                'submission_text': 'I built an API route with database validation, tests, error handling, and React integration. ' * 10,
                'github_url': 'https://github.com/example/tfi-project',
            },
            headers=headers,
        )

        self.assertEqual(students.status_code, 200, students.text)
        self.assertEqual(student_page.status_code, 200, student_page.text)
        self.assertEqual(insights.status_code, 200, insights.text)
        self.assertEqual(assistant.status_code, 200, assistant.text)
        self.assertEqual(ai_overview.status_code, 200, ai_overview.text)
        self.assertEqual(attendance_prediction.status_code, 200, attendance_prediction.text)
        self.assertEqual(performance_forecast.status_code, 200, performance_forecast.text)
        self.assertEqual(risk_analysis.status_code, 200, risk_analysis.text)
        self.assertEqual(model_status.status_code, 200, model_status.text)
        self.assertEqual(model_retraining.status_code, 200, model_retraining.text)
        self.assertEqual(mentor_chat.status_code, 200, mentor_chat.text)
        self.assertEqual(ai_report.status_code, 200, ai_report.text)
        self.assertEqual(assignment_eval.status_code, 200, assignment_eval.text)
        self.assertEqual(authenticity_check.status_code, 200, authenticity_check.text)
        self.assertIsInstance(students.json(), list)
        self.assertIn('has_more', student_page.json())
        self.assertIn('insights', insights.json())
        self.assertIn('summary', assistant.json())
        self.assertIn('executive_report', ai_overview.json())
        self.assertIn('model_status', ai_overview.json())
        self.assertIn('provider_status', ai_overview.json())
        self.assertIsInstance(attendance_prediction.json(), list)
        self.assertIsInstance(performance_forecast.json(), list)
        self.assertIsInstance(risk_analysis.json(), list)
        self.assertIn('artifacts', model_status.json())
        self.assertIn(model_retraining.json()['status'], {'completed', 'insufficient_data'})
        self.assertIn('summary', mentor_chat.json())
        self.assertEqual(ai_report.json()['status'], 'completed')
        self.assertTrue(Path(ai_report.json()['file_url']).exists())
        self.assertIn('score', assignment_eval.json())
        self.assertIn('originality_score', authenticity_check.json())
        self.assertIn('github_evidence', authenticity_check.json())
        with self.Session() as session:
            self.assertEqual(session.query(AiConversation).count(), 2)
            self.assertEqual(session.query(AiReport).count(), 1)
            self.assertEqual(session.query(AssignmentEvaluation).count(), 1)
            self.assertEqual(session.query(AssignmentAuthenticityCheck).count(), 1)

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
