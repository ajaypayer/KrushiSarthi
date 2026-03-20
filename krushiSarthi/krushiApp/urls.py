from . import views
from django.urls import path

urlpatterns = [
    path("", views.home, name="home"),
    path("schemes/", views.government_schemes, name="government_schemes"),
    path("msp/", views.msp, name="msp"),
    path("agriloans/", views.agriloans, name="agriloans"),
    path("chatbot/", views.chatbot, name="chatbot"),

    # Hidden admin link endpoint for data management (login required)
    path("secret-admin/", views.secret_admin, name="secret_admin"),
    path("secret-admin/login/", views.admin_login, name="admin_login"),
    path("secret-admin/logout/", views.admin_logout, name="admin_logout"),
    path("secret-admin/delete/<str:model_name>/<int:pk>/", views.admin_delete, name="admin_delete"),
]

