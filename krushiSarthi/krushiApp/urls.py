from . import views
from django.urls import path

urlpatterns = [
    path("", views.home, name="home"),
    path("schemes/", views.government_schemes, name="government_schemes"),
    path("msp/", views.msp, name="msp"),
    path("agriloans/", views.agriloans, name="agriloans"),
    path("chatbot/", views.chatbot, name="chatbot"),
]

