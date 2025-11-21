from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Expense, Budget, UserCategory
from .forms import ExpenseForm, SignUpForm
from .utils import predict_category
from django.contrib.auth import login
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from datetime import date, timedelta
from django.core.paginator import Paginator
from django.db.models.functions import TruncMonth

# PDF support (weasy or xhtml2pdf)
try:
    from weasyprint import HTML
    WEASY = True
except Exception:
    WEASY = False

def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("expenses:dashboard")
    else:
        form = SignUpForm()
    return render(request, "expenses/signup.html", {"form": form})

@login_required
def dashboard(request):
    user = request.user
    qs = Expense.objects.filter(user=user)

    # search
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(description__icontains=q) | Q(notes__icontains=q) | Q(category__icontains=q))

    # date range filter
    date_from = request.GET.get("from", "")
    date_to = request.GET.get("to", "")
    try:
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
    except Exception:
        pass

    # quick filters
    filter_by = request.GET.get("filter", "all")
    if filter_by == "today":
        qs = qs.filter(date=date.today())
    elif filter_by == "week":
        start = date.today() - timedelta(days=date.today().weekday())
        qs = qs.filter(date__gte=start)
    elif filter_by == "month":
        qs = qs.filter(date__year=date.today().year, date__month=date.today().month)

    # pagination
    page = request.GET.get("page", 1)
    paginator = Paginator(qs, 6)
    page_obj = paginator.get_page(page)

    # totals & chart data
    total = qs.aggregate(total=Sum("amount"))["total"] or 0
    category_totals = qs.values("category").annotate(sum=Sum("amount"))
    labels = [c["category"] for c in category_totals]
    data = [float(c["sum"]) for c in category_totals]

    # Budget: check for current month budget and spent
    month_start = date.today().replace(day=1)
    try:
        current_budget = Budget.objects.get(user=user, month_start=month_start)
        spent_this_month = Expense.objects.filter(user=user, date__year=month_start.year, date__month=month_start.month).aggregate(total=Sum("amount"))["total"] or 0
        budget_pct = (float(spent_this_month) / float(current_budget.amount)) * 100 if current_budget.amount else 0
    except Budget.DoesNotExist:
        current_budget = None
        spent_this_month = 0
        budget_pct = 0

    # Insights (simple rules):
    insights = []
    month_qs = Expense.objects.filter(user=user, date__year=month_start.year, date__month=month_start.month)
    top = month_qs.values("category").annotate(sum=Sum("amount")).order_by("-sum").first()
    if top:
        insights.append(f"Top spending category this month: {top['category']} (₹{float(top['sum']):.2f}).")

    prev_month = (month_start - timedelta(days=1)).replace(day=1)
    this_total = float(month_qs.aggregate(total=Sum("amount"))["total"] or 0)
    prev_total = float(Expense.objects.filter(user=user, date__year=prev_month.year, date__month=prev_month.month).aggregate(total=Sum("amount"))["total"] or 0)
    if prev_total > 0:
        change_pct = ((this_total - prev_total) / prev_total) * 100
        if change_pct > 10:
            insights.append(f"Spending increased {change_pct:.0f}% vs last month.")
        elif change_pct < -10:
            insights.append(f"Spending decreased {abs(change_pct):.0f}% vs last month.")
    elif this_total > 0 and prev_total == 0:
        insights.append("New spending this month (no expenses recorded last month).")

    if current_budget:
        if budget_pct >= 100:
            insights.append("Alert: You have exceeded your budget for this month.")
        elif budget_pct >= 90:
            insights.append("Warning: You have used 90%+ of your budget this month.")

    context = {
        "expenses": page_obj,
        "page_obj": page_obj,
        "total": total,
        "labels": labels,
        "data": data,
        "filter_by": filter_by,
        "q": q,
        "current_budget": current_budget,
        "spent_this_month": spent_this_month,
        "budget_pct": int(budget_pct),
        "insights": insights,
    }
    return render(request, "expenses/dashboard.html", context)

@login_required
def add_expense(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            exp = form.save(commit=False)
            if exp.category == "Other" or not exp.category:
                exp.category = predict_category(exp.description)
            exp.user = request.user
            exp.save()
            return redirect("expenses:dashboard")
    else:
        form = ExpenseForm(user=request.user)
    return render(request, "expenses/expense_form.html", {"form": form, "title": "Add Expense"})

@login_required
def edit_expense(request, pk):
    exp = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=exp, user=request.user)
        if form.is_valid():
            e = form.save(commit=False)
            if e.category == "Other" or not e.category:
                e.category = predict_category(e.description)
            e.save()
            return redirect("expenses:dashboard")
    else:
        form = ExpenseForm(instance=exp, user=request.user)
    return render(request, "expenses/expense_form.html", {"form": form, "title": "Edit Expense"})

@login_required
def delete_expense(request, pk):
    exp = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == "POST":
        exp.delete()
        return redirect("expenses:dashboard")
    return render(request, "expenses/confirm_delete.html", {"expense": exp})

@login_required
def export_csv(request):
    qs = Expense.objects.filter(user=request.user).order_by("-date")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=expenses.csv"
    import csv
    writer = csv.writer(response)
    writer.writerow(["Description", "Amount", "Category", "Date", "Notes"])
    for e in qs:
        writer.writerow([e.description, e.amount, e.category, e.date, e.notes])
    return response

@login_required
def export_pdf(request):
    user = request.user
    qs = Expense.objects.filter(user=user).order_by("-date")
    context = {"expenses": qs, "user": user}
    html_string = render_to_string("expenses/report.html", context)
    if WEASY:
        pdf = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=expenses_report.pdf'
        return response
    else:
        try:
            from xhtml2pdf import pisa
        except Exception:
            return HttpResponse("PDF engine not installed. Run: pip install weasyprint or pip install xhtml2pdf", status=500)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=expenses_report.pdf'
        pisa_status = pisa.CreatePDF(html_string, dest=response)
        if pisa_status.err:
            return HttpResponse("Error generating PDF", status=500)
        return response

@login_required
def monthly_summary(request):
    user = request.user
    qs = Expense.objects.filter(user=user)
    monthly = qs.annotate(month=TruncMonth('date')).values('month').annotate(total=Sum('amount')).order_by('month')
    labels = [m['month'].strftime('%b %Y') for m in monthly]
    data = [float(m['total']) for m in monthly]
    return render(request, "expenses/monthly_summary.html", {"labels": labels, "data": data, "monthly": monthly})

# Budget views
from django import forms

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ("month_start", "amount")
        widgets = {"month_start": forms.DateInput(attrs={"type":"date"})}

@login_required
def budgets_list(request):
    user = request.user
    qs = Budget.objects.filter(user=user).order_by("-month_start")
    return render(request, "expenses/budgets_list.html", {"budgets": qs})

@login_required
def create_budget(request):
    if request.method == "POST":
        form = BudgetForm(request.POST)
        if form.is_valid():
            b = form.save(commit=False)
            b.user = request.user
            b.save()
            return redirect("expenses:budgets")
    else:
        form = BudgetForm()
    return render(request, "expenses/budget_form.html", {"form": form, "title": "Create Budget"})

@login_required
def edit_budget(request, pk):
    b = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == "POST":
        form = BudgetForm(request.POST, instance=b)
        if form.is_valid():
            form.save()
            return redirect("expenses:budgets")
    else:
        form = BudgetForm(instance=b)
    return render(request, "expenses/budget_form.html", {"form": form, "title": "Edit Budget"})
