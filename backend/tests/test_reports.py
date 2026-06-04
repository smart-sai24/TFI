import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.deps import CurrentUser
from app.api.v1.reports import GenerateReportRequest, generate_report
from app.db.base import Base
from app.models.operations import AuditLog, Report, Role
from app.models.user import User


class ReportGenerationTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine('sqlite:///:memory:', future=True)
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine, future=True)

    def test_generate_report_persists_report_and_audit_log(self):
        with self.Session() as session:
            session.add(Role(name='Admin', description='Administrator'))
            session.add(
                User(
                    uid='admin-1',
                    email='admin@example.com',
                    name='Admin User',
                    role='Admin',
                    is_active=True,
                )
            )
            session.commit()

            response = generate_report(
                GenerateReportRequest(report_type='Weekly executive'),
                CurrentUser(uid='admin-1', email='admin@example.com', role='Admin'),
                session,
            )

            report = session.get(Report, response['id'])
            audit_log = session.query(AuditLog).filter_by(action='report.generated').one()

        self.assertEqual(response['report_type'], 'Weekly executive')
        self.assertEqual(response['status'], 'completed')
        self.assertIsNotNone(report)
        self.assertEqual(report.generated_by_uid, 'admin-1')
        self.assertEqual(audit_log.entity_id, str(response['id']))


if __name__ == '__main__':
    unittest.main()
