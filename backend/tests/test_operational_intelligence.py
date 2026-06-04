import unittest
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.operations import AttendanceRecord, AttendanceSession, Batch, Student
from app.services.operational_intelligence import dashboard_summary


class OperationalIntelligenceTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine('sqlite:///:memory:', future=True)
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine, future=True)

    def test_dashboard_uses_database_records(self):
        with self.Session() as session:
            batch = Batch(name='AIML June', domain='AIML', status='active')
            session.add(batch)
            session.flush()
            student = Student(
                batch_id=batch.id,
                registration_number='TFI-AIML-001',
                full_name='Aarav Mehta',
                email='aarav@example.com',
                domain='AIML',
                metadata_json={},
            )
            session.add(student)
            session.flush()
            attendance_session = AttendanceSession(
                batch_id=batch.id,
                title='Model lab',
                platform='Zoom',
                session_date=date.today(),
                required_minutes=90,
            )
            session.add(attendance_session)
            session.flush()
            session.add(
                AttendanceRecord(
                    session_id=attendance_session.id,
                    student_id=student.id,
                    duration_minutes=90,
                    attendance_percentage=100,
                    status='Full',
                    late_joining=False,
                    early_leaving=False,
                    engagement_score=95,
                    raw_payload={},
                )
            )
            session.commit()

            summary = dashboard_summary(session, 'Director')
            self.assertEqual(summary['total_interns'], 1)
            self.assertEqual(summary['total_batches'], 1)
            self.assertEqual(summary['attendance_rate'], 100)
            self.assertEqual(summary['top_performers'][0]['registration_number'], 'TFI-AIML-001')


if __name__ == '__main__':
    unittest.main()
