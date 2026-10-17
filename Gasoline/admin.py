from django.contrib import admin
from .models import FuelType, FuelSale, Expense, ExpenseCategory, Employee, FuelDelivery, UserProfile


@admin.register(FuelType)
class FuelTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_per_liter', 'current_stock', 'tank_capacity', 'stock_percentage', 'is_low_stock']
    list_filter = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(FuelSale)
class FuelSaleAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'fuel_type', 'liters', 'price_per_liter', 'total_amount', 'cashier_name', 'status', 'created_at']
    list_filter = ['fuel_type', 'status', 'payment_method', 'created_at']
    search_fields = ['transaction_id', 'cashier_name']
    readonly_fields = ['transaction_id', 'total_amount', 'created_at', 'updated_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['expense_id', 'category', 'amount', 'expense_date', 'approved_by_name', 'status']
    list_filter = ['category', 'status', 'expense_date']
    search_fields = ['expense_id', 'description', 'approved_by_name']
    readonly_fields = ['expense_id', 'created_at', 'updated_at']
    ordering = ['-expense_date', '-created_at']
    date_hierarchy = 'expense_date'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'role', 'basic_pay', 'allowance', 'deductions', 'net_pay', 'status', 'payroll_status']
    list_filter = ['role', 'status', 'payroll_status']
    search_fields = ['first_name', 'last_name', 'employee_id']
    readonly_fields = ['employee_id', 'created_at', 'updated_at']
    ordering = ['last_name', 'first_name']


@admin.register(FuelDelivery)
class FuelDeliveryAdmin(admin.ModelAdmin):
    list_display = ['delivery_id', 'fuel_type', 'volume', 'supplier', 'cost', 'delivery_date', 'status']
    list_filter = ['fuel_type', 'supplier', 'status', 'delivery_date']
    search_fields = ['delivery_id', 'supplier']
    readonly_fields = ['delivery_id', 'created_at', 'updated_at']
    ordering = ['-delivery_date', '-created_at']
    date_hierarchy = 'delivery_date'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'branch', 'is_active', 'created_at']
    list_filter = ['role', 'branch', 'is_active']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    ordering = ['user__username']
    filter_horizontal = []  # No many-to-many fields