import httpx

from app.core.config import settings


def send_email(recipient: str, subject: str, html_body: str, api_key: str, from_email: str | None = None) -> dict:
    sender = from_email or settings.resend_from_email
    if not sender:
        raise ValueError('Resend sender email is not configured')
    resp = httpx.post(
        'https://api.resend.com/emails',
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        json={
            'from': sender,
            'to': [recipient],
            'subject': subject,
            'html': html_body,
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def send_whatsapp(message: str, to_number: str, token: str, phone_number_id: str | None = None) -> dict:
    configured_phone_number_id = phone_number_id or settings.whatsapp_phone_number_id
    if not configured_phone_number_id:
        raise ValueError('WhatsApp phone number ID is not configured')
    resp = httpx.post(
        f'https://graph.facebook.com/v17.0/{configured_phone_number_id}/messages',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json={
            'messaging_product': 'whatsapp',
            'to': to_number,
            'type': 'text',
            'text': {'preview_url': False, 'body': message},
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()
