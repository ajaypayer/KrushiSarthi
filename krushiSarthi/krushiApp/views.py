from django.shortcuts import render
from django.utils import timezone


def _common_context():
    return {'year': timezone.now().year}


def home(request):

    return render(request, 'home.html', _common_context())


def government_schemes(request):

    return render(request, 'government_scheme.html', _common_context())

def msp(request):
    return render(request, 'msp.html', _common_context())

def agriloans(request):
    return render(request, 'agriloans.html', _common_context())

def chatbot(request):
    return render(request, 'chatbot.html', _common_context())