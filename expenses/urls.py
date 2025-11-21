from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "expenses"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("add/", views.add_expense, name="add"),
    path("edit/<int:pk>/", views.edit_expense, name="edit"),
    path("delete/<int:pk>/", views.delete_expense, name="delete"),
    path("export/csv/", views.export_csv, name="export_csv"),
    path("export/pdf/", views.export_pdf, name="export_pdf"),
    path("monthly/", views.monthly_summary, name="monthly_summary"),
    path("budgets/", views.budgets_list, name="budgets"),
    path("budgets/add/", views.create_budget, name="add_budget"),
    path("budgets/edit/<int:pk>/", views.edit_budget, name="edit_budget"),
    path("signup/", views.signup_view, name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name="expenses/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
