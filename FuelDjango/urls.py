"""
URL configuration for FuelDjango project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from Gasoline.views import (
    index,
    get_sales_data, get_expense_data, get_stock_data,
    get_payroll_data, get_delivery_data, get_user_data,
    get_dashboard_stats,
    add_sale, add_expense, add_employee, add_delivery, add_user,
    delete_sale, delete_expense, delete_employee, delete_delivery, delete_user,
    approve_expense, reject_expense, pay_employee,
    approve_sale, deny_sale,
)
from Gasoline.export_views import (
    export_sales_pdf, export_sales_excel,
    export_expenses_pdf, export_expenses_excel,
    export_profit_pdf, export_profit_excel,
    export_payroll_pdf, export_payroll_excel,
)
    
urlpatterns = [
    # Main dashboard
    path('', index, name='index'),
    path('admin/', admin.site.urls),
    
    # API endpoints - GET data
    path('api/sales/', get_sales_data, name='api-sales'),
    path('api/expenses/', get_expense_data, name='api-expenses'),
    path('api/stock/', get_stock_data, name='api-stock'),
    path('api/payroll/', get_payroll_data, name='api-payroll'),
    path('api/deliveries/', get_delivery_data, name='api-deliveries'),
    path('api/users/', get_user_data, name='api-users'),
    path('api/dashboard-stats/', get_dashboard_stats, name='api-dashboard-stats'),
    
    # API endpoints - POST (CRUD operations)
    path('api/sales/add/', add_sale, name='api-add-sale'),
    path('api/expenses/add/', add_expense, name='api-add-expense'),
    path('api/employees/add/', add_employee, name='api-add-employee'),
    path('api/deliveries/add/', add_delivery, name='api-add-delivery'),
    path('api/users/add/', add_user, name='api-add-user'),
    
    # API endpoints - DELETE
    path('api/sales/delete/<str:txn_id>/', delete_sale, name='api-delete-sale'),
    path('api/expenses/delete/<str:exp_id>/', delete_expense, name='api-delete-expense'),
    path('api/employees/delete/<str:emp_id>/', delete_employee, name='api-delete-employee'),
    path('api/deliveries/delete/<str:del_id>/', delete_delivery, name='api-delete-delivery'),
    path('api/users/delete/<int:user_id>/', delete_user, name='api-delete-user'),
    
    # API endpoints - UPDATE (Status changes)
    path('api/expenses/approve/<str:exp_id>/', approve_expense, name='api-approve-expense'),
    path('api/expenses/reject/<str:exp_id>/', reject_expense, name='api-reject-expense'),
    path('api/employees/pay/<str:emp_id>/', pay_employee, name='api-pay-employee'),
    
    # API endpoints - Fuel Sale status changes
    path('api/sales/approve/<str:txn_id>/', approve_sale, name='api-approve-sale'),
    path('api/sales/deny/<str:txn_id>/', deny_sale, name='api-deny-sale'),
    
    # REPORT EXPORT ENDPOINTS
    path('export/sales/pdf/', export_sales_pdf, name='export-sales-pdf'),
    path('export/sales/excel/', export_sales_excel, name='export-sales-excel'),
    path('export/expenses/pdf/', export_expenses_pdf, name='export-expenses-pdf'),
    path('export/expenses/excel/', export_expenses_excel, name='export-expenses-excel'),
    path('export/profit/pdf/', export_profit_pdf, name='export-profit-pdf'),
    path('export/profit/excel/', export_profit_excel, name='export-profit-excel'),
    path('export/payroll/pdf/', export_payroll_pdf, name='export-payroll-pdf'),
    path('export/payroll/excel/', export_payroll_excel, name='export-payroll-excel'),
]
