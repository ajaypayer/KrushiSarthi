import requests
from django.conf import settings


def send_sms(phone, message):
    if not phone or not message:
        return False

    api_url = getattr(settings, 'SMS_API_URL', '')
    api_key = getattr(settings, 'SMS_API_KEY', '')

    if not api_url:
        print("[SMS ERROR] SMS_API_URL not configured. Please set it in environment or settings.")
        return False

    if not api_key:
        print("[SMS ERROR] SMS_API_KEY is empty! Set the environment variable SMS_API_KEY.")
        print("[SMS ERROR] To set it: set SMS_API_KEY=your_api_key (Windows) or export SMS_API_KEY=your_api_key (Linux)")
        print("[SMS ERROR] Get your API key from: https://www.fast2sms.com/")
        print(f"[SMS SIMULATION] Would send to {phone}: {message}")
        return False  # Return False so we know SMS didn't actually send

    numbers = phone if isinstance(phone, str) else ",".join(phone)
    payload = {
        "message": message,
        "language": "english",
        "route": "q",
        "numbers": numbers
    }

    headers = {
        "authorization":"a7Cp********************",
        "Content-Type": "application/json"
    }

    try:
        print(f"[SMS API] Calling {api_url} with {len(phone) if isinstance(phone, list) else 1} number(s)")
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"[SMS SUCCESS] SMS sent to {numbers}")
        return True
    except Exception as exc:
        print(f"[SMS ERROR] Send failed for {numbers}: {exc}")
        return False


def send_bulk_sms(numbers, message):
    if not numbers:
        return False

    if isinstance(numbers, str):
        numbers = [numbers]

    return send_sms(numbers, message)

