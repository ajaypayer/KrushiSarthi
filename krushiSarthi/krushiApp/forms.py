from django import forms
from .models import GovernmentScheme, MspRate, AgriLoan, Farmer

class GovernmentSchemeForm(forms.ModelForm):
    class Meta:
        model = GovernmentScheme
        fields = ['name', 'scheme_type', 'status', 'description', 'benefits', 'eligibility', 'apply_url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., PM-KISAN'}),
            'scheme_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief overview...'}),
            'benefits': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'List benefits here...'}),
            'eligibility': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Who can apply?'}),
            'apply_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://official-portal.gov.in'}),
        }

class MspRateForm(forms.ModelForm):
    class Meta:
        model = MspRate
        fields = ['crop_name', 'season', 'rate', 'year', 'percentage_increase']
        widgets = {
            'crop_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Paddy'}),
            'season': forms.Select(attrs={'class': 'form-control'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2183'}),
            'year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2024-25'}),
            'percentage_increase': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 7%'}),
        }

class AgriLoanForm(forms.ModelForm):
    class Meta:
        model = AgriLoan
        fields = ['bank_name', 'loan_name', 'category', 'interest_rate', 'duration', 'details', 'apply_url']
        widgets = {
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., SBI'}),
            'loan_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., KCC'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 4.00'}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 12 months'}),
            'details': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Terms and documents...'}),
            'apply_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://bank-portal.com/apply'}),
        }

class FarmerForm(forms.ModelForm):
    class Meta:
        model = Farmer
        fields = ['name', 'mobile_number', 'email', 'location']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
            'mobile_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter mobile number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email (optional)'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your state/location'}),
        }
