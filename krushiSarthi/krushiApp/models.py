from django.db import models


class Scheme(models.Model):
    CATEGORY_CHOICES = [
        ("central", "Central"),
        ("state", "State"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="central")
    crop = models.CharField(max_length=50, default="allcrops")
    benefits = models.TextField(blank=True)
    eligibility = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class MSP(models.Model):
    SEASON_CHOICES = [
        ("kharif", "Kharif"),
        ("rabi", "Rabi"),
        ("summer", "Summer"),
    ]

    crop_name = models.CharField(max_length=100)
    season = models.CharField(max_length=20, choices=SEASON_CHOICES, default="kharif")
    msp_rate = models.DecimalField(max_digits=10, decimal_places=2)
    year = models.CharField(max_length=20)
    change_percent = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.crop_name} {self.season} {self.year}"


class AgriLoan(models.Model):
    name = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    rate = models.CharField(max_length=50)
    duration = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
