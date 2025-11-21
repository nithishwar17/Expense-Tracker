from django import forms
from .models import Expense, UserCategory
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

CATEGORY_CHOICES = [
    ("Food", "Food"),
    ("Travel", "Travel"),
    ("Shopping", "Shopping"),
    ("Bills", "Bills"),
    ("Entertainment", "Entertainment"),
    ("Other", "Other"),
]

class ExpenseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # pop user if provided; keep compatibility if not
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # prepare category choices: global static choices + any user categories
        user_choices = []
        if user:
            try:
                user_choices = [(c.name, c.name) for c in user.categories.all()]
            except Exception:
                user_choices = []

        # combine - ensure no duplicates
        combined = CATEGORY_CHOICES + [c for c in user_choices if c not in CATEGORY_CHOICES]
        self.fields["category"].choices = combined

        # Add bootstrap classes to fields
        for name, field in self.fields.items():
            css = field.widget.attrs.get("class", "")
            # set form-control for inputs, keep existing classes
            if "form-control" not in css:
                field.widget.attrs["class"] = (css + " form-control").strip()
            # placeholder for description and amount
            if name == "description":
                field.widget.attrs.setdefault("placeholder", "e.g. Uber to office")
            if name == "amount":
                field.widget.attrs.setdefault("placeholder", "0.00")
            if name == "date":
                # ensure date input has type date (widget may already set)
                field.widget.attrs.setdefault("type", "date")

    class Meta:
        model = Expense
        fields = ["description", "amount", "category", "date", "notes"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
            # description and amount will receive form-control class from __init__
        }

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ("username","email","password1","password2")
