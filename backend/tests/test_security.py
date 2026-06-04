import unittest

from app.core.security import normalize_role, role_has_permission


class SecurityPolicyTests(unittest.TestCase):
    def test_unknown_role_normalizes_to_director(self):
        self.assertEqual(normalize_role('Unknown'), 'Director')

    def test_host_can_import_attendance(self):
        self.assertTrue(role_has_permission('Host', 'attendance:import'))

    def test_mentor_cannot_import_attendance(self):
        self.assertFalse(role_has_permission('Mentor', 'attendance:import'))


if __name__ == '__main__':
    unittest.main()
