#!/usr/bin/env python
"""
Manual SMS test - send to a specific number
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'krushiSarthi.settings')
sys.path.insert(0, r'c:\Users\Ajay\FarmerPortal\krushiSarthi')
django.setup()

from krushiApp.utils import send_sms

print("Manual SMS Test")
print("=" * 30)

# Test with a single number
test_number = input("Enter phone number to test (without +91): ")
if test_number:
    test_message = "Test SMS from Farmer Portal - SMS Feature Working!"
    print(f"Sending to: {test_number}")
    print(f"Message: {test_message}")

    result = send_sms(test_number, test_message)
    if result:
        print("✅ SMS sent successfully!")
    else:
        print("❌ SMS failed!")
else:
    print("No number entered. Test cancelled.")