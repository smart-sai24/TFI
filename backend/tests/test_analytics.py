import unittest

from app.services.analytics import compute_attendance_quality, compute_attendance_summary


class AttendanceAnalyticsTests(unittest.TestCase):
    def test_summary_counts_statuses(self):
        summary = compute_attendance_summary(
            [
                {'attendance_status': 'Full'},
                {'attendance_status': 'Partial'},
                {'attendance_status': 'Absent'},
                {'attendance_status': 'Full'},
            ]
        )
        self.assertEqual(summary['full'], 2)
        self.assertEqual(summary['partial'], 1)
        self.assertEqual(summary['absent'], 1)
        self.assertEqual(summary['total_records'], 4)

    def test_quality_metrics_are_calculated(self):
        quality = compute_attendance_quality(
            [
                {'email': 'a@example.com', 'attendance_percentage': 100, 'engagement_score': 95, 'late_joining': False, 'early_leaving': False},
                {'email': 'b@example.com', 'attendance_percentage': 50, 'engagement_score': 40, 'late_joining': True, 'early_leaving': True},
            ]
        )
        self.assertEqual(quality['average_attendance_percentage'], 75)
        self.assertEqual(quality['late_joining_count'], 1)
        self.assertEqual(quality['identity_match_rate'], 100)


if __name__ == '__main__':
    unittest.main()
