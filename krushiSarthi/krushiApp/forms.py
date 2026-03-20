from django import forms
from .models import Scheme, MSP, AgriLoan


class SchemeForm(forms.ModelForm):
    class Meta:
        model = Scheme
        fields = ["title", "description", "category", "crop", "benefits", "eligibility"]


class MSPForm(forms.ModelForm):
    class Meta:
        model = MSP
        fields = ["crop_name", "season", "msp_rate", "year", "change_percent"]


class AgriLoanForm(forms.ModelForm):
    class Meta:
        model = AgriLoan
        fields = ["name", "summary", "rate", "duration", "details"]
