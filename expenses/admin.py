from django.contrib import admin
from .models import Expense

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("description", "user", "amount", "category", "date")
    list_filter = ("category", "date")
    search_fields = ("description", "notes", "user__username")
