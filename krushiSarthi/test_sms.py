#!/usr/bin/env python
"""
Quick test to check SMS configuration and registered farmers
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'krushiSarthi.settings')
sys.path.insert(0, r'c:\Users\Ajay\FarmerPortal\krushiSarthi')
django.setup()

from django.conf import settings
from krushiApp.models import Farmer
from krushiApp.utils import send_sms

print("=" * 60)
print("SMS CONFIGURATION & FARMER CHECK")
print("=" * 60)

# Check 1: SMS Settings
print("\n✓ SMS Settings:")
print(f"  SMS_API_URL: {settings.SMS_API_URL}")
print(f"  SMS_API_KEY: {settings.SMS_API_KEY[:10]}***" if settings.SMS_API_KEY else "  SMS_API_KEY: EMPTY ❌")

# Check 2: Registered Farmers
print("\n✓ Registered Farmers:")
farmers = Farmer.objects.filter(
    mobile_number__isnull=False
).exclude(mobile_number__exact='')

if farmers.exists():
    for farmer in farmers:
        print(f"  - {farmer.name}: {farmer.mobile_number}")
    print(f"\nTotal: {farmers.count()} farmers found ✓")
else:
    print("  NO FARMERS REGISTERED ❌")

# Check 3: Test SMS sending
print("\n✓ Sending Test SMS:")
if settings.SMS_API_KEY and farmers.exists():
    test_numbers = list(farmers.values_list('mobile_number', flat=True))
    print(f"  To: {test_numbers}")
    result = send_sms(test_numbers, "Test message from Farmer Portal")
    if result:
        print("  Result: SMS sent successfully ✓")
    else:
        print("  Result: SMS failed ❌")
else:
    print("  Skipped: SMS_API_KEY not set or no farmers registered ❌")

print("\n" + "=" * 60)
