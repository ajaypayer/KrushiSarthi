from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.cache import cache_control
from .models import GovernmentScheme, MspRate, AgriLoan, Farmer
from .forms import GovernmentSchemeForm, MspRateForm, AgriLoanForm, FarmerForm
from .chatbot import get_answer
from .utils import send_bulk_sms
import requests

def translate_text(text, dest_lang):
    if dest_lang == 'en' or not text:
        return text
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={dest_lang}&dt=t&q={requests.utils.quote(text)}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            result = response.json()
            return result[0][0][0]
        else:
            return text
    except:
        return text

def _common_context():
    return {'year': timezone.now().year}

# Frontend Views
def home(request):
    return render(request, 'home.html', _common_context())

def government_schemes(request):
    schemes = GovernmentScheme.objects.all().order_by('-last_updated')
    lang = request.LANGUAGE_CODE
    for scheme in schemes:
        scheme.name = translate_text(scheme.name, lang)
        scheme.description = translate_text(scheme.description, lang)
        scheme.benefits = translate_text(scheme.benefits, lang)
        scheme.eligibility = translate_text(scheme.eligibility, lang)
        scheme.scheme_type = translate_text(scheme.scheme_type, lang)
    context = _common_context()
    context['schemes'] = schemes
    return render(request, 'government_scheme.html', context)

def msp(request):
    msps = MspRate.objects.all().order_by('crop_name')
    lang = request.LANGUAGE_CODE
    for msp in msps:
        msp.crop_name = translate_text(msp.crop_name, lang)
        msp.season = translate_text(msp.season, lang)
    context = _common_context()
    context['msps'] = msps
    return render(request, 'msp.html', context)

def agriloans(request):
    loans = AgriLoan.objects.all()
    lang = request.LANGUAGE_CODE
    for loan in loans:
        loan.bank_name = translate_text(loan.bank_name, lang)
        loan.loan_name = translate_text(loan.loan_name, lang)
        loan.duration = translate_text(loan.duration, lang)
    context = _common_context()
    context['loans'] = loans
    return render(request, 'agriloans.html', context)

def chatbot(request):
    return render(request, 'chatbot.html', _common_context())


def chatbot_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    user_input = request.POST.get('message', '').strip()
    reply = get_answer(user_input)
    return JsonResponse({'reply': reply})


def farmer_register(request):
    success = False
    if request.method == 'POST':
        form = FarmerForm(request.POST)
        if form.is_valid():
            form.save()
            success = True
    else:
        form = FarmerForm()
    
    context = _common_context()
    context['form'] = form
    context['success'] = success
    return render(request, 'register.html', context)

# Custom Admin Views
def custom_admin_login(request):
    error = None
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            if user.is_staff:
                login(request, user)
                return redirect('custom_admin_schemes')
            else:
                error = "You do not have admin access."
        else:
            error = "Invalid username or password."
    return render(request, 'custom_admin/custom_admin_login.html', {'error': error})

def custom_admin_logout(request):
    logout(request)
    return redirect('home')

def notify_registered_farmers(title, message):
    """Send a broadcast notification to all registered farmers."""
    try:
        numbers = list(Farmer.objects
            .filter(mobile_number__isnull=False)
            .exclude(mobile_number__exact='')
            .values_list('mobile_number', flat=True)
        )

        print(f"\n[NOTIFICATION LOG] Fetched {len(numbers)} registered farmer numbers from database.")
        
        if not numbers:
            print("[NOTIFICATION LOG] ERROR: No registered farmer mobile numbers found in the database.")
            return False

        print(f"[NOTIFICATION LOG] Mobile numbers: {numbers}")
        sms_text = f"{title}: {message}"
        print(f"[NOTIFICATION LOG] Sending message: {sms_text}")
        
        result = send_bulk_sms(numbers, sms_text)

        if result:
            print(f"[NOTIFICATION LOG] SUCCESS: Notifications sent to {len(numbers)} farmers.")
        else:
            print(f"[NOTIFICATION LOG] ERROR: Notification dispatch failed. Check SMS API configuration.")
        return result
    except Exception as e:
        print(f"[NOTIFICATION LOG] ERROR during notification: {str(e)}")
        return False

@staff_member_required(login_url='custom_admin_login')
def manage_schemes(request):
    schemes = GovernmentScheme.objects.all().order_by('-last_updated')
    return render(request, 'custom_admin/custom_admin_schemes.html', {'schemes': schemes})

@staff_member_required(login_url='custom_admin_login')
def add_scheme(request):
    if request.method == 'POST':
        form = GovernmentSchemeForm(request.POST)
        print(f"\n[SCHEME ADD] POST request received")
        print(f"[SCHEME ADD] POST data: {request.POST.dict()}")
        
        if form.is_valid():
            print(f"[SCHEME ADD] Form is valid")
            try:
                from django.db import transaction
                with transaction.atomic():
                    scheme = form.save()
                    print(f"[SCHEME SAVE SUCCESS] Scheme created with ID: {scheme.id}")
                    print(f"[SCHEME SAVE SUCCESS] Name: {scheme.name}, Type: {scheme.scheme_type}")
                    
                from django.db import connection
                connection.close()
                
                verify_scheme = GovernmentScheme.objects.get(id=scheme.id)
                print(f"[SCHEME VERIFY SUCCESS] Verified scheme in database: {verify_scheme.name}")
                
                notify_registered_farmers("New Scheme Added", f"Scheme {scheme.name} is now available!")
                return redirect('custom_admin_schemes')
            except Exception as e:
                import traceback
                print(f"[SCHEME SAVE ERROR] Exception: {str(e)}")
                print(f"[SCHEME SAVE ERROR] Traceback: {traceback.format_exc()}")
                form.add_error(None, f"Error saving scheme: {str(e)}")
        else:
            print(f"[FORM VALIDATION ERROR] Scheme form errors: {form.errors}")
    else:
        form = GovernmentSchemeForm()
        print(f"[SCHEME ADD] GET request - displaying form")
    return render(request, 'custom_admin/custom_admin_form.html', {
        'form': form,
        'page_title': 'Add New Scheme',
        'cancel_url': '/admin-panel/schemes/'
    })

@staff_member_required(login_url='custom_admin_login')
def edit_scheme(request, pk):
    scheme = get_object_or_404(GovernmentScheme, pk=pk)
    if request.method == 'POST':
        form = GovernmentSchemeForm(request.POST, instance=scheme)
        if form.is_valid():
            form.save()
            return redirect('custom_admin_schemes')
    else:
        form = GovernmentSchemeForm(instance=scheme)
    return render(request, 'custom_admin/custom_admin_form.html', {
        'form': form,
        'page_title': 'Edit Scheme',
        'cancel_url': '/admin-panel/schemes/'
    })

@staff_member_required(login_url='custom_admin_login')
def delete_scheme(request, pk):
    scheme = get_object_or_404(GovernmentScheme, pk=pk)
    scheme.delete()
    return redirect('custom_admin_schemes')

# MSP Admin Views
@cache_control(no_cache=True, no_store=True, must_revalidate=True, max_age=0)
@staff_member_required(login_url='custom_admin_login')
def manage_msps(request):
    # Ensure fresh data is fetched from database every time
    from django.core.cache import cache
    cache.clear()  # Clear any cached data
    
    msps = MspRate.objects.all().order_by('-last_updated')
    total_count = msps.count()
    
    print(f"\n[MSP VIEW LOG] Fetching MSP data...")
    print(f"[MSP VIEW LOG] Total MSP records in database: {total_count}")
    
    if total_count > 0:
        for msp in msps:
            print(f"[MSP VIEW LOG]   -> ID: {msp.id}, Crop: {msp.crop_name}, Season: {msp.season}, Rate: {msp.rate}")
    else:
        print(f"[MSP VIEW LOG] WARNING: No MSP records found in database!")
    
    response = render(request, 'custom_admin/custom_admin_msp.html', {
        'msps': msps,
        'total_count': total_count
    })
    # Add no-cache headers to the response
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@staff_member_required(login_url='custom_admin_login')
def add_msp(request):
    if request.method == 'POST':
        form = MspRateForm(request.POST)
        print(f"\n[MSP ADD] POST request received")
        print(f"[MSP ADD] POST data: {request.POST}")
        
        if form.is_valid():
            print(f"[MSP ADD] Form is valid")
            print(f"[MSP ADD] Cleaned data: {form.cleaned_data}")
            try:
                from django.db import transaction
                with transaction.atomic():
                    msp_obj = form.save()
                    print(f"[MSP SAVE SUCCESS] MSP object created with ID: {msp_obj.id}")
                    print(f"[MSP SAVE SUCCESS] Crop: {msp_obj.crop_name}, Season: {msp_obj.season}, Rate: {msp_obj.rate}")
                    
                # Verify data was actually saved
                from django.db import connection
                connection.close()  # Close connection to ensure commits are flushed
                
                # Query to verify
                verify_msp = MspRate.objects.get(id=msp_obj.id)
                print(f"[MSP VERIFY SUCCESS] Verified MSP in database: {verify_msp.crop_name}")
                
                notify_registered_farmers("MSP Updated", f"MSP for {msp_obj.crop_name} is now ₹{msp_obj.rate} per quintal.")
                return redirect('custom_admin_msps')
            except Exception as e:
                import traceback
                print(f"[MSP SAVE ERROR] Exception occurred: {str(e)}")
                print(f"[MSP SAVE ERROR] Traceback: {traceback.format_exc()}")
                form.add_error(None, f"Error saving MSP: {str(e)}")
        else:
            print(f"[FORM VALIDATION ERROR] Form is NOT valid")
            print(f"[FORM VALIDATION ERROR] Form errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"  -> {field}: {error}")
    else:
        form = MspRateForm()
        print(f"[MSP ADD] GET request - displaying form")
    
    return render(request, 'custom_admin/custom_admin_form.html', {
        'form': form,
        'page_title': 'Add MSP Data',
        'cancel_url': '/admin-panel/msp/'
    })

@staff_member_required(login_url='custom_admin_login')
def edit_msp(request, pk):
    msp_obj = get_object_or_404(MspRate, pk=pk)
    if request.method == 'POST':
        form = MspRateForm(request.POST, instance=msp_obj)
        if form.is_valid():
            form.save()
            return redirect('custom_admin_msps')
    else:
        form = MspRateForm(instance=msp_obj)
    return render(request, 'custom_admin/custom_admin_form.html', {
        'form': form,
        'page_title': 'Edit MSP Data',
        'cancel_url': '/admin-panel/msp/'
    })

@staff_member_required(login_url='custom_admin_login')
def delete_msp(request, pk):
    msp_obj = get_object_or_404(MspRate, pk=pk)
    msp_obj.delete()
    return redirect('custom_admin_msps')

# Loan Admin Views
@staff_member_required(login_url='custom_admin_login')
def manage_loans(request):
    loans = AgriLoan.objects.all()
    return render(request, 'custom_admin/custom_admin_loans.html', {'loans': loans})

@staff_member_required(login_url='custom_admin_login')
def add_loan(request):
    if request.method == 'POST':
        form = AgriLoanForm(request.POST)
        print(f"\n[LOAN ADD] POST request received")
        print(f"[LOAN ADD] POST data: {request.POST.dict()}")
        
        if form.is_valid():
            print(f"[LOAN ADD] Form is valid")
            try:
                from django.db import transaction
                with transaction.atomic():
                    loan = form.save()
                    print(f"[LOAN SAVE SUCCESS] Loan created with ID: {loan.id}")
                    print(f"[LOAN SAVE SUCCESS] Name: {loan.loan_name}, Bank: {loan.bank_name}")
                    
                from django.db import connection
                connection.close()
                
                verify_loan = AgriLoan.objects.get(id=loan.id)
                print(f"[LOAN VERIFY SUCCESS] Verified loan in database: {verify_loan.loan_name}")
                
                notify_registered_farmers("New Loan Available", f"A new loan {loan.loan_name} from {loan.bank_name} is open.")
                return redirect('custom_admin_loans')
            except Exception as e:
                import traceback
                print(f"[LOAN SAVE ERROR] Exception: {str(e)}")
                print(f"[LOAN SAVE ERROR] Traceback: {traceback.format_exc()}")
                form.add_error(None, f"Error saving loan: {str(e)}")
        else:
            print(f"[FORM VALIDATION ERROR] Loan form errors: {form.errors}")
    else:
        form = AgriLoanForm()
        print(f"[LOAN ADD] GET request - displaying form")
    return render(request, 'custom_admin/custom_admin_form.html', {
        'form': form,
        'page_title': 'Add Loan Scheme',
        'cancel_url': '/admin-panel/loans/'
    })

@staff_member_required(login_url='custom_admin_login')
def edit_loan(request, pk):
    loan = get_object_or_404(AgriLoan, pk=pk)
    if request.method == 'POST':
        form = AgriLoanForm(request.POST, instance=loan)
        if form.is_valid():
            form.save()
            return redirect('custom_admin_loans')
    else:
        form = AgriLoanForm(instance=loan)
    return render(request, 'custom_admin/custom_admin_form.html', {
        'form': form,
        'page_title': 'Edit Loan Scheme',
        'cancel_url': '/admin-panel/loans/'
    })

@staff_member_required(login_url='custom_admin_login')
def delete_loan(request, pk):
    loan = get_object_or_404(AgriLoan, pk=pk)
    loan.delete()
    return redirect('custom_admin_loans')