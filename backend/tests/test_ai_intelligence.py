import unittest
from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.operations import Assignment, AttendanceRecord, AttendanceSession, Batch, Submission
from app.models.operations import Student
from app.ai.authenticity import run_authenticity_check
from app.services.ai_intelligence import (
    ai_module_overview,
    attendance_drop_predictions,
    evaluate_assignment_submission,
    executive_ai_report,
    performance_forecasts,
)


class AiIntelligenceTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine('sqlite:///:memory:', future=True)
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine, future=True)

    def seed_student(self, session):
        batch = Batch(name='AIML June', domain='AIML', status='active')
        session.add(batch)
        session.flush()
        student = Student(
            batch_id=batch.id,
            registration_number='TFI-AI-001',
            full_name='Asha Rao',
            email='asha@example.com',
            domain='AIML',
            metadata_json={},
        )
        session.add(student)
        session.flush()
        attendance_session = AttendanceSession(
            batch_id=batch.id,
            title='Prediction lab',
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
                duration_minutes=45,
                attendance_percentage=50,
                status='Partial',
                late_joining=True,
                early_leaving=True,
                engagement_score=45,
                raw_payload={},
            )
        )
        assignment = Assignment(
            batch_id=batch.id,
            title='Model reflection',
            assignment_type='reflection',
            due_at=datetime.now(timezone.utc),
            max_score=100,
        )
        session.add(assignment)
        session.flush()
        session.add(
            Submission(
                assignment_id=assignment.id,
                student_id=student.id,
                status='missing',
                is_late=True,
            )
        )
        session.commit()

    def test_ai_predictions_forecasts_and_report_use_student_signals(self):
        with self.Session() as session:
            self.seed_student(session)

            predictions = attendance_drop_predictions(session)
            forecasts = performance_forecasts(session)
            report = executive_ai_report(session)
            overview = ai_module_overview(session)

        self.assertEqual(predictions[0]['risk_level'], 'High')
        self.assertGreaterEqual(predictions[0]['drop_probability'], 65)
        self.assertEqual(forecasts[0]['forecast_outcome'], 'High risk completion')
        self.assertIn('high attendance-drop probability', report['narrative'])
        self.assertIn('attendance_predictions', overview)

    def test_assignment_evaluation_scores_submission_text(self):
        result = evaluate_assignment_submission(
            'API assignment',
            'I created a function and API validation flow with database tests. '
            'I debugged an error, improved the component, and tested the result with pytest. ' * 8,
        )

        self.assertGreaterEqual(result['score'], 80)
        self.assertIn(result['grade'], {'A', 'B'})
        self.assertIn('strengths', result)

    def test_authenticity_check_flags_similar_submission_and_scores_originality(self):
        original = (
            'I built a FastAPI route with validation, database persistence, pytest coverage, '
            'error handling, and a React component that shows the result. '
        ) * 4
        copy = (
            'I built a FastAPI route with validation, database persistence, pytest coverage, '
            'error handling, and a React component that shows the result. '
        ) * 4

        with self.Session() as session:
            first = run_authenticity_check(session, 'API Project', original, assignment_id=1, student_id=1)
            second = run_authenticity_check(session, 'API Project', copy, assignment_id=1, student_id=2)

        self.assertGreaterEqual(first['originality_score'], 70)
        self.assertGreaterEqual(second['similarity_score'], 90)
        self.assertIn(second['risk_level'], {'High', 'Critical'})
        self.assertIn('recommendations', second)


if __name__ == '__main__':
    unittest.main()
