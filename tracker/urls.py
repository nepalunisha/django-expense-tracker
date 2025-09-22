from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'), 
    path('reports/', views.reports, name='reports'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/update/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('incomes/', views.income_list, name='income_list'),
    path('incomes/create/', views.income_create, name='income_create'),
    path('incomes/<int:pk>/update/', views.income_update, name='income_update'),
    path('incomes/<int:pk>/delete/', views.income_delete, name='income_delete'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/<int:pk>/update/', views.expense_update, name='expense_update'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('forecast/', views.forecast_view, name='forecast'),
    path('forecast/download/', views.download_forecast_csv, name='download_forecast_csv'),
]