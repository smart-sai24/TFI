import unittest
from unittest.mock import Mock, patch

from app.services.notifications import send_email, send_whatsapp


class NotificationServiceTests(unittest.TestCase):
    def test_send_email_includes_configured_sender(self):
        response = Mock()
        response.json.return_value = {'id': 'email-1'}
        response.raise_for_status.return_value = None

        with patch('app.services.notifications.httpx.post', return_value=response) as post:
            result = send_email(
                'student@example.com',
                'Attendance update',
                '<p>Hello</p>',
                'resend-key',
                from_email='ops@tfi.example',
            )

        self.assertEqual(result, {'id': 'email-1'})
        payload = post.call_args.kwargs['json']
        self.assertEqual(payload['from'], 'ops@tfi.example')
        self.assertEqual(payload['to'], ['student@example.com'])
        response.raise_for_status.assert_called_once()

    def test_send_whatsapp_uses_configured_phone_number_id(self):
        response = Mock()
        response.json.return_value = {'messages': [{'id': 'message-1'}]}
        response.raise_for_status.return_value = None

        with patch('app.services.notifications.httpx.post', return_value=response) as post:
            result = send_whatsapp('Session starts now', '+919999999999', 'wa-token', phone_number_id='phone-123')

        self.assertEqual(result, {'messages': [{'id': 'message-1'}]})
        self.assertEqual(post.call_args.args[0], 'https://graph.facebook.com/v17.0/phone-123/messages')
        self.assertEqual(post.call_args.kwargs['json']['text']['body'], 'Session starts now')
        response.raise_for_status.assert_called_once()


if __name__ == '__main__':
    unittest.main()
