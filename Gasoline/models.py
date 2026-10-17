from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta


# Fuel types available at the station
class FuelType(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., "Unleaded 91", "Diesel"
    price_per_liter = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    color = models.CharField(max_length=7, default='#f5a623')  # Hex color for UI
    tank_capacity = models.IntegerField(default=15000)  # Total tank capacity in liters
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Current volume in tank
    low_stock_threshold = models.IntegerField(default=3000)  # Alert when below this

    class Meta:
        verbose_name_plural = "Fuel Types"

    def __str__(self):
        return self.name

    @property
    def stock_percentage(self):
        if self.tank_capacity == 0:
            return 0
        return round((self.current_stock / self.tank_capacity) * 100)

    @property
    def is_low_stock(self):
        # Alert if stock is below absolute threshold OR below 25% capacity (visual red threshold)
        return self.current_stock < self.low_stock_threshold or self.stock_percentage < 25


# Fuel sales transactions
class FuelSale(models.Model):
    STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
        ('Unsuccessful', 'Unsuccessful'),
        ('Cancelled', 'Cancelled'),
    ]

    PAYMENT_METHODS = [
        ('Cash', 'Cash'),
        ('GCash', 'GCash'),
        ('Card', 'Card'),
    ]

    transaction_id = models.CharField(max_length=20, unique=True, editable=False)
    fuel_type = models.ForeignKey(FuelType, on_delete=models.CASCADE, related_name='sales')
    liters = models.DecimalField(max_digits=8, decimal_places=2)
    price_per_liter = models.DecimalField(max_digits=8, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sales')
    cashier_name = models.CharField(max_length=100)  # Store name for historical records
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='Cash')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Paid')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_id} - {self.fuel_type.name} ({self.liters}L)"

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            # Generate transaction ID: TXN-YYYYMMDD-XXXX
            today = datetime.now().strftime('%Y%m%d')
            last_txn = FuelSale.objects.filter(transaction_id__startswith=f'TXN-{today}').order_by('-transaction_id').first()
            if last_txn:
                last_num = int(last_txn.transaction_id.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.transaction_id = f'TXN-{today}-{new_num:04d}'
        
        if self.fuel_type and self.liters and self.price_per_liter:
            self.total_amount = self.liters * self.price_per_liter
        
        super().save(*args, **kwargs)


# Expense categories
class ExpenseCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., "Fuel Restock", "Utilities"
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Expense Categories"

    def __str__(self):
        return self.name


# Expenses
class Expense(models.Model):
    STATUS_CHOICES = [
        ('Approved', 'Approved'),
        ('Pending', 'Pending'),
        ('Rejected', 'Rejected'),
    ]

    expense_id = models.CharField(max_length=20, unique=True, editable=False)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, related_name='expenses')
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='approved_expenses')
    approved_by_name = models.CharField(max_length=100)  # Store name for historical records
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-expense_date', '-created_at']

    def __str__(self):
        return f"{self.expense_id} - {self.category.name} ({self.amount})"

    def save(self, *args, **kwargs):
        if not self.expense_id:
            # Generate expense ID
            today = datetime.now().strftime('%Y%m%d')
            last_exp = Expense.objects.filter(expense_id__startswith=f'EXP-{today}').order_by('-expense_id').first()
            if last_exp:
                last_num = int(last_exp.expense_id.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.expense_id = f'EXP-{today}-{new_num:04d}'
        
        super().save(*args, **kwargs)


# Employee/Payroll
class Employee(models.Model):
    ROLE_CHOICES = [
        ('Pump Attendant', 'Pump Attendant'),
        ('Cashier', 'Cashier'),
        ('Supervisor', 'Supervisor'),
        ('Manager', 'Manager'),
    ]

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('On Leave', 'On Leave'),
    ]

    PAYROLL_STATUS = [
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
    ]

    employee_id = models.CharField(max_length=20, unique=True, editable=False)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    basic_pay = models.DecimalField(max_digits=10, decimal_places=2)
    allowance = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    payroll_status = models.CharField(max_length=20, choices=PAYROLL_STATUS, default='Pending')
    hire_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def net_pay(self):
        return self.basic_pay + self.allowance - self.deductions

    def save(self, *args, **kwargs):
        if not self.employee_id:
            last_emp = Employee.objects.order_by('-employee_id').first()
            if last_emp:
                last_num = int(last_emp.employee_id.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.employee_id = f'EMP-{new_num:03d}'
        
        super().save(*args, **kwargs)


# Fuel delivery log
class FuelDelivery(models.Model):
    STATUS_CHOICES = [
        ('Delivered', 'Delivered'),
        ('Scheduled', 'Scheduled'),
        ('Cancelled', 'Cancelled'),
    ]

    SUPPLIER_CHOICES = [
        ('Petron Corp.', 'Petron Corp.'),
        ('Shell Philippines', 'Shell Philippines'),
        ('Phoenix Petroleum', 'Phoenix Petroleum'),
        ('Caltex', 'Caltex'),
    ]

    delivery_id = models.CharField(max_length=20, unique=True, editable=False)
    fuel_type = models.ForeignKey(FuelType, on_delete=models.CASCADE, related_name='deliveries')
    volume = models.IntegerField()  # Volume in liters
    supplier = models.CharField(max_length=50, choices=SUPPLIER_CHOICES)
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-delivery_date', '-created_at']

    def __str__(self):
        return f"{self.delivery_id} - {self.fuel_type.name} ({self.volume}L)"

    def save(self, *args, **kwargs):
        if not self.delivery_id:
            today = datetime.now().strftime('%Y%m%d')
            last_del = FuelDelivery.objects.filter(delivery_id__startswith=f'DEL-{today}').order_by('-delivery_id').first()
            if last_del:
                last_num = int(last_del.delivery_id.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.delivery_id = f'DEL-{today}-{new_num:04d}'
        
        super().save(*args, **kwargs)


# User profiles for extended user management
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Manager', 'Manager'),
        ('Cashier', 'Cashier'),
        ('Viewer', 'Viewer'),
    ]

    BRANCH_CHOICES = [
        ('Main - Cebu City', 'Main - Cebu City'),
        ('Branch 2 - Mandaue', 'Branch 2 - Mandaue'),
        ('Branch 3 - Lapu-Lapu', 'Branch 3 - Lapu-Lapu'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Viewer')
    branch = models.CharField(max_length=50, choices=BRANCH_CHOICES, default='Main - Cebu City')
    phone = models.CharField(max_length=20, blank=True)
    last_login_display = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Permissions
    can_view_sales = models.BooleanField(default=True)
    can_edit_sales = models.BooleanField(default=False)
    can_delete_records = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=True)
    can_export_reports = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.role}"