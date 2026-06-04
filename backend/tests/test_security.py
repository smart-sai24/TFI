import unittest

from app.core.security import create_access_token, decode_access_token, normalize_role, role_has_permission


class SecurityPolicyTests(unittest.TestCase):
    def test_unknown_role_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_role('Unknown')

    def test_role_normalization_is_case_insensitive(self):
        self.assertEqual(normalize_role('admin'), 'Admin')

    def test_host_can_import_attendance(self):
        self.assertTrue(role_has_permission('Host', 'attendance:import'))

    def test_mentor_cannot_import_attendance(self):
        self.assertFalse(role_has_permission('Mentor', 'attendance:import'))

    def test_unknown_role_has_no_permissions(self):
        self.assertFalse(role_has_permission('Unknown', 'reports:generate'))

    def test_access_token_contains_normalized_role(self):
        token, expires_in = create_access_token('uid-1', 'admin@example.com', 'admin')
        payload = decode_access_token(token)

        self.assertEqual(expires_in, 3600)
        self.assertIsNotNone(payload)
        self.assertEqual(payload['role'], 'Admin')


if __name__ == '__main__':
    unittest.main()
