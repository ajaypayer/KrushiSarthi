from django.db import models

class GovernmentScheme(models.Model):
    SCHEME_TYPES = [('Central', 'Central'), ('State', 'State')]
    STATUS_CHOICES = [('Active', 'Active'), ('Inactive', 'Inactive')]

    name = models.CharField(max_length=200)
    scheme_type = models.CharField(max_length=100, choices=SCHEME_TYPES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    last_updated = models.DateField(auto_now=True)
    description = models.TextField(blank=True, null=True, help_text="A brief overview of the scheme.")
    benefits = models.TextField(blank=True, null=True, help_text="Detailed benefits offered to farmers.")
    eligibility = models.TextField(blank=True, null=True, help_text="Who is eligible for this scheme?")
    apply_url = models.URLField(blank=True, null=True, help_text="Link to the official government application portal.")

    def __str__(self):
        return self.name

class MspRate(models.Model):
    SEASON_CHOICES = [('Kharif', 'Kharif'), ('Rabi', 'Rabi')]

    crop_name = models.CharField(max_length=100)
    season = models.CharField(max_length=100, choices=SEASON_CHOICES)
    rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Rate in ₹ per Quintal")
    year = models.CharField(max_length=20, default="2024-25", help_text="Target financial year (e.g., 2024-25)")
    percentage_increase = models.CharField(max_length=20, blank=True, null=True, help_text="Percentage increase compared to last year (e.g., 7%)")
    last_updated = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.crop_name} - {self.season}"

class AgriLoan(models.Model):
    CATEGORY_CHOICES = [
        ('Credit Cards', 'Credit Cards'),
        ('Crop Loans', 'Crop Loans'),
        ('Equipment Loans', 'Equipment Loans'),
    ]

    bank_name = models.CharField(max_length=200)
    loan_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='Crop Loans')
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    duration = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 12 months, 5-7 years")
    details = models.TextField(blank=True, null=True, help_text="List of required documents and terms.")
    apply_url = models.URLField(blank=True, null=True, help_text="Link to the official bank application portal.")

    def __str__(self):
        return f"{self.bank_name} - {self.loan_name}"

class Farmer(models.Model):
    name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.mobile_number})"

class Scheme(models.Model):
    name = models.CharField(max_length=200)

class MSP(models.Model):
    crop = models.CharField(max_length=100)
    price = models.IntegerField()

class Loan(models.Model):
    name = models.CharField(max_length=200)

class User(models.Model):
    phone = models.CharField(max_length=15)