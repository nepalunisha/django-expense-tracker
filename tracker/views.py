from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.db.models import Sum, Q
from .models import Category, Income, Expense
from .forms import CategoryForm, IncomeForm, ExpenseForm
from datetime import datetime, timedelta
import pandas as pd
from prophet import Prophet
import os
import csv
from django.http import HttpResponse
from django.conf import settings

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Registration failed. Please correct the errors.')
    else:
        form = UserCreationForm()
    return render(request, 'tracker/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'tracker/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    today = datetime.now().date()
    last_month = today - timedelta(days=30)
    total_income = Income.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Expense.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expense
    recent_incomes = Income.objects.filter(user=request.user, date__gte=last_month).order_by('-date')[:5]
    recent_expenses = Expense.objects.filter(user=request.user, date__gte=last_month).order_by('-date')[:5]
    balance_pos = max(balance, 0)
    balance_neg = abs(min(balance, 0))
    user_expenses = Expense.objects.filter(user=request.user).order_by('date')
    if user_expenses.exists() and user_expenses.count() >= 2:
        df = pd.DataFrame(list(user_expenses.values('date', 'amount')))
        df.rename(columns={'date': 'ds', 'amount': 'y'}, inplace=True)
        model = Prophet(daily_seasonality=True)
        model.fit(df)
        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)
        forecast_dates = forecast['ds'].dt.strftime('%Y-%m-%d').tolist()
        forecast_values = forecast['yhat'].round(2).tolist()
    else:
        forecast_dates = []
        forecast_values = []
    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'recent_incomes': recent_incomes,
        'recent_expenses': recent_expenses,
        'balance_pos': balance_pos,
        'balance_neg': balance_neg,
        'forecast_dates': forecast_dates,
        'forecast_values': forecast_values,
    }
    return render(request, 'tracker/dashboard.html', context)

@login_required
def reports(request):
    total_income = Income.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Expense.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expense
    chart_data = {'total_income': total_income, 'total_expense': total_expense, 'total_balance': balance}
    return render(request, 'tracker/reports.html', {'chart_data': chart_data})

@login_required
def forecast_view(request):
    file_path = os.path.join(settings.BASE_DIR, 'dataset', 'expense_data_1.csv')
    df = pd.read_csv(file_path)
    df['Start_Date'] = pd.to_datetime(df['Date'].str.split(' - ').str[0], errors='coerce')
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df_expense = df[df['Income/Expense'] == 'Expense'].dropna(subset=['Start_Date','Amount'])
    if len(df_expense) < 2:
        return render(request, 'tracker/forecast.html', {'error': 'Not enough expense data to make a forecast.'})
    daily_expense = df_expense.groupby('Start_Date')['Amount'].sum().reset_index()
    daily_expense.rename(columns={'Start_Date':'ds','Amount':'y'}, inplace=True)
    model = Prophet()
    model.fit(daily_expense)
    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)
    forecast_chart = forecast[['ds','yhat']].tail(30)
    chart_labels = forecast_chart['ds'].dt.strftime('%Y-%m-%d').tolist()
    chart_data = forecast_chart['yhat'].round(2).tolist()
    request.session['chart_labels'] = chart_labels
    request.session['chart_data'] = chart_data
    return render(request, 'tracker/forecast.html', {'chart_labels': chart_labels, 'chart_data': chart_data})

def download_forecast_csv(request):
    chart_labels = request.session.get('chart_labels', [])
    chart_data = request.session.get('chart_data', [])
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="forecast.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Predicted Expense'])
    for date, value in zip(chart_labels, chart_data):
        writer.writerow([date, value])
    return response

@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user)
    return render(request, 'tracker/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, 'Category created successfully!')
            return redirect('category_list')
        else:
            messages.error(request, 'Error creating category.')
    else:
        form = CategoryForm()
    return render(request, 'tracker/category_form.html', {'form': form, 'title': 'Create Category'})

@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('category_list')
        else:
            messages.error(request, 'Error updating category.')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'tracker/category_form.html', {'form': form, 'title': 'Update Category'})

@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully!')
        return redirect('category_list')
    return render(request, 'tracker/category_confirm_delete.html', {'category': category})

@login_required
def income_list(request):
    query = request.GET.get('q')
    incomes = Income.objects.filter(user=request.user)
    if query:
        incomes = incomes.filter(Q(description__icontains=query) | Q(category__name__icontains=query))
    return render(request, 'tracker/income_list.html', {'incomes': incomes})

@login_required
def income_create(request):
    if request.method == 'POST':
        form = IncomeForm(request.POST, user=request.user)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.save()
            messages.success(request, 'Income added successfully!')
            return redirect('income_list')
        else:
            messages.error(request, 'Error adding income.')
    else:
        form = IncomeForm(user=request.user)
    return render(request, 'tracker/income_form.html', {'form': form, 'title': 'Create Income'})

@login_required
def income_update(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)
    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=income, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Income updated successfully!')
            return redirect('income_list')
        else:
            messages.error(request, 'Error updating income.')
    else:
        form = IncomeForm(instance=income, user=request.user)
    return render(request, 'tracker/income_form.html', {'form': form, 'title': 'Update Income'})

@login_required
def income_delete(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)
    if request.method == 'POST':
        income.delete()
        messages.success(request, 'Income deleted successfully!')
        return redirect('income_list')
    return render(request, 'tracker/income_confirm_delete.html', {'income': income})

@login_required
def expense_list(request):
    query = request.GET.get('q')
    expenses = Expense.objects.filter(user=request.user)
    if query:
        expenses = expenses.filter(Q(description__icontains=query) | Q(category__name__icontains=query))
    return render(request, 'tracker/expense_list.html', {'expenses': expenses})

@login_required
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, 'Expense added successfully!')
            return redirect('expense_list')
        else:
            messages.error(request, 'Error adding expense.')
    else:
        form = ExpenseForm(user=request.user)
    return render(request, 'tracker/expense_form.html', {'form': form, 'title': 'Create Expense'})

@login_required
def expense_update(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('expense_list')
        else:
            messages.error(request, 'Error updating expense.')
    else:
        form = ExpenseForm(instance=expense, user=request.user)
    return render(request, 'tracker/expense_form.html', {'form': form, 'title': 'Update Expense'})

@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('expense_list')
    return render(request, 'tracker/expense_confirm_delete.html', {'expense': expense})
