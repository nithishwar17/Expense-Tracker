from django.db import models
from django.contrib.auth.models import User

CATEGORY_CHOICES = [
    ("Food", "Food"),
    ("Travel", "Travel"),
    ("Shopping", "Shopping"),
    ("Bills", "Bills"),
    ("Entertainment", "Entertainment"),
    ("Other", "Other"),
]

class UserCategory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ("user", "name")
    def __str__(self):
        return self.name

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="expenses")
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="Other")
    date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.description} - {self.amount}"

class Budget(models.Model):
    """
    Budget for a given user and month.
    month_start: store the first day of the month (YYYY-MM-01) for simplicity.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="budgets")
    month_start = models.DateField(help_text="First day of month (e.g. 2025-11-01)")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "month_start")
        ordering = ("-month_start",)

    def __str__(self):
        return f"{self.user.username} - {self.month_start.strftime('%Y-%m')} : {self.amount}"
