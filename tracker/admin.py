from django.contrib import admin
from .models import Category, Income, Expense

# Register your models here.

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'user']
    list_filter = ['type', 'user']
    search_fields = ['name']

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ['amount', 'date', 'category', 'description', 'user']
    list_filter = ['date', 'category', 'user']
    search_fields = ['description', 'amount']
    ordering = ['-date']
    readonly_fields = ['user']

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['amount', 'date', 'category', 'description', 'user']
    list_filter = ['date', 'category', 'user']
    search_fields = ['description', 'amount']
    ordering = ['-date']
    readonly_fields = ['user']