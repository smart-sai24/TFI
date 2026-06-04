import unittest

from app.services.observability import ApiMetricsCollector


class ObservabilityTests(unittest.TestCase):
    def test_snapshot_reports_live_runtime_metrics(self):
        collector = ApiMetricsCollector()
        collector.record(25.0, 200)
        collector.record(120.0, 503)

        snapshot = collector.snapshot()
        by_name = {item['name']: item for item in snapshot}

        self.assertEqual(by_name['Requests served']['value'], '2')
        self.assertEqual(by_name['P95 latency']['value'], '120 ms')
        self.assertEqual(by_name['Error rate']['value'], '50.00%')
        self.assertEqual(by_name['Error rate']['status'], 'Watch')


if __name__ == '__main__':
    unittest.main()
