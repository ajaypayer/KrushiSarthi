from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Scheme, MSP, Loan, User
from .utils import send_sms

# 🔹 When new Scheme added
@receiver(post_save, sender=Scheme)
def send_scheme_sms(sender, instance, created, **kwargs):
    if created:
        users = User.objects.all()
        for user in users:
            send_sms(user.phone, f"New Scheme: {instance.name}")

# 🔹 When new MSP added
@receiver(post_save, sender=MSP)
def send_msp_sms(sender, instance, created, **kwargs):
    if created:
        users = User.objects.all()
        for user in users:
            send_sms(user.phone, f"New MSP Rate: {instance.crop} - ₹{instance.price}")

# 🔹 When new Loan added
@receiver(post_save, sender=Loan)
def send_loan_sms(sender, instance, created, **kwargs):
    if created:
        users = User.objects.all()
        for user in users:
            send_sms(user.phone, f"New Loan Scheme: {instance.name}")