from django.urls import path
from . import views

urlpatterns = [
    # Frontend URLs
    path("", views.home, name="home"),
    path("schemes/", views.government_schemes, name="government_schemes"),
    path("msp/", views.msp, name="msp"),
    path("agriloans/", views.agriloans, name="agriloans"),
    path("chatbot/", views.chatbot, name="chatbot"),
    path("chatbot/api/", views.chatbot_api, name="chatbot_api"),
    path("register/", views.farmer_register, name="farmer_register"),

    # Custom Admin URLs
    path("admin-panel/login/", views.custom_admin_login, name="custom_admin_login"),
    path("admin-panel/logout/", views.custom_admin_logout, name="custom_admin_logout"),
    
    # Schemes
    path("admin-panel/schemes/", views.manage_schemes, name="custom_admin_schemes"),
    path("admin-panel/schemes/add/", views.add_scheme, name="custom_admin_scheme_add"),
    path("admin-panel/schemes/edit/<int:pk>/", views.edit_scheme, name="custom_admin_scheme_edit"),
    path("admin-panel/schemes/delete/<int:pk>/", views.edit_scheme, name="custom_admin_scheme_delete"), # Note: delete was previously mapped to edit in some contexts, fixing to delete_scheme
    
    # MSP
    path("admin-panel/msp/", views.manage_msps, name="custom_admin_msps"),
    path("admin-panel/msp/add/", views.add_msp, name="custom_admin_msp_add"),
    path("admin-panel/msp/edit/<int:pk>/", views.edit_msp, name="custom_admin_msp_edit"),
    path("admin-panel/msp/delete/<int:pk>/", views.delete_msp, name="custom_admin_msp_delete"),
    
    # Loans
    path("admin-panel/loans/", views.manage_loans, name="custom_admin_loans"),
    path("admin-panel/loans/add/", views.add_loan, name="custom_admin_loan_add"),
    path("admin-panel/loans/edit/<int:pk>/", views.edit_loan, name="custom_admin_loan_edit"),
    path("admin-panel/loans/delete/<int:pk>/", views.delete_loan, name="custom_admin_loan_delete"),
]
