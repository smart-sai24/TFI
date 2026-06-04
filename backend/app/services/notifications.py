import httpx


def send_email(recipient: str, subject: str, html_body: str, api_key: str) -> dict:
    resp = httpx.post(
        'https://api.resend.com/emails',
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        json={
            'to': [recipient],
            'subject': subject,
            'html': html_body,
        },
        timeout=15,
    )
    return resp.json()


def send_whatsapp(message: str, to_number: str, token: str) -> dict:
    resp = httpx.post(
        'https://graph.facebook.com/v17.0/YOUR_PHONE_NUMBER_ID/messages',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json={
            'messaging_product': 'whatsapp',
            'to': to_number,
            'type': 'template',
            'template': {'name': 'tfi_notification', 'language': {'code': 'en_US'}},
        },
        timeout=15,
    )
    return resp.json()
