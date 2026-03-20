from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
from django.http import Http404

from .models import Scheme, MSP, AgriLoan
from .forms import SchemeForm, MSPForm, AgriLoanForm

SECRET_ADMIN_TOKEN = "krushiAdmin2026"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"


def _common_context(request):
    return {
        'year': timezone.now().year,
        'redirect_to': request.get_full_path(),
    }


def home(request):
    return render(request, 'home.html', _common_context(request))


def government_schemes(request):
    schemes = Scheme.objects.order_by('-created_at')
    return render(request, 'government_scheme.html', {
        **_common_context(request),
        'schemes': schemes,
    })


def msp(request):
    msps = MSP.objects.order_by('-created_at')
    return render(request, 'msp.html', {
        **_common_context(request),
        'msps': msps,
    })


def agriloans(request):
    loans = AgriLoan.objects.order_by('-created_at')
    return render(request, 'agriloans.html', {
        **_common_context(request),
        'loans': loans,
    })


def chatbot(request):
    return render(request, 'chatbot.html', _common_context(request))


def admin_login(request):
    if request.session.get('is_admin_authenticated'):
        return redirect('secret_admin')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            request.session['is_admin_authenticated'] = True
            messages.success(request, 'Admin login successful.')
            return redirect('secret_admin')
        else:
            error = 'Invalid username or password.'

    return render(request, 'admin_login.html', {'error': error})


def admin_logout(request):
    request.session['is_admin_authenticated'] = False
    messages.success(request, 'Logged out successfully.')
    return redirect('admin_login')


def secret_admin(request):
    if not request.session.get('is_admin_authenticated'):
        return redirect('admin_login')

    scheme_form = SchemeForm()
    msp_form = MSPForm()
    loan_form = AgriLoanForm()

    if request.method == 'POST':
        data_type = request.POST.get('data_type')

        if data_type == 'scheme':
            scheme_form = SchemeForm(request.POST)
            if scheme_form.is_valid():
                scheme_form.save()
                messages.success(request, 'Scheme saved successfully.')
                return redirect('secret_admin')

        elif data_type == 'msp':
            msp_form = MSPForm(request.POST)
            if msp_form.is_valid():
                msp_form.save()
                messages.success(request, 'MSP data saved successfully.')
                return redirect('secret_admin')

        elif data_type == 'loan':
            loan_form = AgriLoanForm(request.POST)
            if loan_form.is_valid():
                loan_form.save()
                messages.success(request, 'Loan data saved successfully.')
                return redirect('secret_admin')

    context = {
        'schemes': Scheme.objects.order_by('-created_at'),
        'msps': MSP.objects.order_by('-created_at'),
        'loans': AgriLoan.objects.order_by('-created_at'),
        'scheme_form': scheme_form,
        'msp_form': msp_form,
        'loan_form': loan_form,
    }

    return render(request, 'secret_admin.html', context)


def admin_delete(request, model_name, pk):
    if not request.session.get('is_admin_authenticated'):
        raise Http404

    model_map = {
        'scheme': Scheme,
        'msp': MSP,
        'loan': AgriLoan,
    }

    model = model_map.get(model_name)
    if not model:
        raise Http404

    obj = get_object_or_404(model, pk=pk)
    obj.delete()
    messages.success(request, f'{model_name.capitalize()} entry deleted.')
    return redirect('secret_admin')