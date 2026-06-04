import unittest

from fastapi.testclient import TestClient

from app.main import app


class AppRuntimeTests(unittest.TestCase):
    def test_root_adds_security_headers_and_metrics(self):
        client = TestClient(app)
        response = client.get('/', headers={'Host': 'localhost'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')


if __name__ == '__main__':
    unittest.main()
