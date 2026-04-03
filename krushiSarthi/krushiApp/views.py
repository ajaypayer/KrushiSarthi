from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.admin.views.decorators import staff_member_required
from .models import GovernmentScheme, MspRate, AgriLoan, Farmer
from .forms import GovernmentSchemeForm, MspRateForm, AgriLoanForm, FarmerForm

def _common_context():
    return {'year': timezone.now().year}

# Frontend Views
def home(request):
    return render(request, 'home.html', _common_context())

def government_schemes(request):
    schemes = GovernmentScheme.objects.all().order_by('-last_updated')
    context = _common_context()
    context['schemes'] = schemes
    return render(request, 'government_scheme.html', context)

def msp(request):
    msps = MspRate.objects.all().order_by('crop_name')
    context = _common_context()
    context['msps'] = msps
    return render(request, 'msp.html', context)

def agriloans(request):
    loans = AgriLoan.objects.all()
    context = _common_context()
    context['loans'] = loans
    return render(request, 'agriloans.html', context)

def chatbot(request):
    return render(request, 'chatbot.html', _common_context())

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
    """
    Simulated SMS/Alert notification logic.
    Logs the alert to the console for every registered farmer.
    """
    farmers = Farmer.objects.all()
    print("\n" + "="*50)
    print(f"BROADCAST ALERT: {title}")
    print(f"MESSAGE: {message}")
    print(f"SENDING TO {farmers.count()} REGISTERED FARMERS...")
    for farmer in farmers:
        # Placeholder for real SMS API (Twilio, etc.)
        print(f"  [SMS SIMULATED] -> {farmer.mobile_number} ({farmer.name})")
    print("="*50 + "\n")

@staff_member_required(login_url='custom_admin_login')
def manage_schemes(request):
    schemes = GovernmentScheme.objects.all().order_by('-last_updated')
    return render(request, 'custom_admin/custom_admin_schemes.html', {'schemes': schemes})

@staff_member_required(login_url='custom_admin_login')
def add_scheme(request):
    if request.method == 'POST':
        form = GovernmentSchemeForm(request.POST)
        if form.is_valid():
            scheme = form.save()
            notify_registered_farmers("New Scheme Added", f"Scheme {scheme.name} is now available!")
            return redirect('custom_admin_schemes')
    else:
        form = GovernmentSchemeForm()
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
@staff_member_required(login_url='custom_admin_login')
def manage_msps(request):
    msps = MspRate.objects.all()
    return render(request, 'custom_admin/custom_admin_msp.html', {'msps': msps})

@staff_member_required(login_url='custom_admin_login')
def add_msp(request):
    if request.method == 'POST':
        form = MspRateForm(request.POST)
        if form.is_valid():
            msp_obj = form.save()
            notify_registered_farmers("MSP Updated", f"MSP for {msp_obj.crop_name} is now {msp_obj.rate}.")
            return redirect('custom_admin_msps')
    else:
        form = MspRateForm()
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
        if form.is_valid():
            loan = form.save()
            notify_registered_farmers("New Loan Available", f"A new loan {loan.loan_name} from {loan.bank_name} is open.")
            return redirect('custom_admin_loans')
    else:
        form = AgriLoanForm()
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