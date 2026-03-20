from django.contrib import admin
from .models import Scheme, MSP, AgriLoan


@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "crop", "created_at")
    search_fields = ("title", "category", "crop")


@admin.register(MSP)
class MSPAdmin(admin.ModelAdmin):
    list_display = ("crop_name", "season", "msp_rate", "year", "change_percent")
    search_fields = ("crop_name", "season", "year")


@admin.register(AgriLoan)
class AgriLoanAdmin(admin.ModelAdmin):
    list_display = ("name", "rate", "duration", "created_at")
    search_fields = ("name", "rate")

# Register your models here.
