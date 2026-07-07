import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'krushiSarthi.settings')
django.setup()

from krushiApp.utils import send_bulk_sms
from django.conf import settings

def test_sms_sending():
    print("=== Testing SMS Dispatch ===")
    print(f"SMS API URL: {settings.SMS_API_URL}")
    print(f"SMS API KEY length: {len(settings.SMS_API_KEY) if settings.SMS_API_KEY else 0}")
    
    test_number = "8669180821"  # Ajay's registered number
    test_message = "Hello from KrushiSarthi! This is a test notification validating the SMS service."
    
    print(f"\nSending test SMS to: {test_number}")
    print(f"Message: {test_message}")
    
    result = send_bulk_sms([test_number], test_message)
    if result:
        print("\n[SUCCESS] SMS was sent successfully!")
    else:
        print("\n[FAILURE] SMS sending failed. Please check Fast2SMS balance or key validity.")

if __name__ == '__main__':
    test_sms_sending()
