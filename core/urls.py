from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.conf import settings
import os

def service_worker(request):
    sw_path = os.path.join(settings.BASE_DIR, "static", "expenses", "serviceworker.js")
    try:
        with open(sw_path, "rb") as f:
            return HttpResponse(f.read(), content_type="application/javascript")
    except FileNotFoundError:
        return HttpResponse("// serviceworker not found", content_type="application/javascript")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("expenses.urls", namespace="expenses")),
    path("serviceworker.js", service_worker, name="serviceworker"),
    path("offline/", TemplateView.as_view(template_name="expenses/offline.html"), name="offline"),

]
