from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json
from django.core.serializers.json import DjangoJSONEncoder


from .models import (
    FuelType, FuelSale, Expense, ExpenseCategory,
    Employee, FuelDelivery, UserProfile
)
from django.contrib.auth.models import User


def index(request):
    """Render the main FuelOps Admin dashboard with real data"""
    
    # Get current date for filtering
    today = timezone.now().date()
    
    # === DASHBOARD STATISTICS ===
    # Today's revenue from fuel sales
    today_sales = FuelSale.objects.filter(
        created_at__date=today, 
        status='Paid'
    )
    today_revenue = sum(sale.total_amount for sale in today_sales)
    
    # Total expenses for current month
    month_expenses = Expense.objects.filter(
        expense_date__month=today.month,
        expense_date__year=today.year,
        status='Approved'
    )
    total_expenses = sum(exp.amount for exp in month_expenses)
    
    # Net profit (today's revenue - daily average expenses)
    daily_avg_expenses = total_expenses / Decimal(today.day) if today.day > 0 else Decimal(0)
    net_profit = today_revenue - daily_avg_expenses
    
    # Total transactions today
    total_transactions = today_sales.count()
    
    # === FUEL STOCK DATA ===
    fuel_types = FuelType.objects.all().order_by('name')
    
    # Low stock alerts
    low_stock_items = [ft for ft in fuel_types if ft.is_low_stock]
    
    # === RECENT TRANSACTIONS ===
    recent_sales = FuelSale.objects.select_related('fuel_type').order_by('-created_at')[:5]
    
    # === EXPENSES ===
    recent_expenses = Expense.objects.select_related('category').order_by('-expense_date', '-created_at')[:10]
    
    # Expense categories for dropdown
    expense_categories = ExpenseCategory.objects.all()
    
    # Expense by category for current month
    expense_by_category = {}
    for cat in expense_categories:
        cat_total = Expense.objects.filter(
            category=cat,
            expense_date__month=today.month,
            expense_date__year=today.year,
            status='Approved'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        if cat_total > 0:
            expense_by_category[cat.name] = float(cat_total)
    
    # === PAYROLL ===
    employees = Employee.objects.all().order_by('last_name', 'first_name')
    total_payroll = sum(emp.net_pay for emp in employees if emp.status == 'Active')
    paid_employees = employees.filter(payroll_status='Paid').count()
    pending_employees = employees.filter(payroll_status='Pending').count()
    total_paid = sum(emp.net_pay for emp in employees if emp.payroll_status == 'Paid')
    total_pending = sum(emp.net_pay for emp in employees if emp.payroll_status == 'Pending')
    
    # === DELIVERIES ===
    deliveries = FuelDelivery.objects.select_related('fuel_type').order_by('-delivery_date', '-created_at')[:10]
    
    # === USERS ===
    user_profiles = UserProfile.objects.select_related('user').all().order_by('user__username')
    
    # === CHART DATA ===
    # Monthly sales data (last 12 months)
    monthly_sales_data = []
    for i in range(11, -1, -1):
        month_date = today - timedelta(days=i*30)
        month_sales = FuelSale.objects.filter(
            created_at__month=month_date.month,
            created_at__year=month_date.year,
            status='Paid'
        ).aggregate(total=models.Sum('total_amount'))['total'] or 0
        monthly_expenses = Expense.objects.filter(
            expense_date__month=month_date.month,
            expense_date__year=month_date.year,
            status='Approved'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        monthly_sales_data.append({
            'month': month_date.strftime('%b'),
            'revenue': float(month_sales),
            'expenses': float(monthly_expenses),
            'profit': float(month_sales - monthly_expenses)
        })
    
    # Format expense breakdown for chart
    expense_breakdown = list(expense_by_category.values())
    expense_labels = list(expense_by_category.keys())
    
    context = {
        # Dashboard stats
        'today_revenue': today_revenue,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'total_transactions': total_transactions,
        
        # Fuel stock
        'fuel_types': fuel_types,
        'low_stock_items': low_stock_items,
        
        # Recent data
        'recent_sales': recent_sales,
        'recent_expenses': recent_expenses,
        'deliveries': deliveries,
        
        # Payroll
        'employees': employees,
        'total_payroll': total_payroll,
        'paid_employees': paid_employees,
        'pending_employees': pending_employees,
        'total_paid': total_paid,
        'total_pending': total_pending,
        
        # Users
        'user_profiles': user_profiles,
        
        # Chart data - JSON serialized for JavaScript
        'monthly_sales_data_json': json.dumps(monthly_sales_data, cls=DjangoJSONEncoder),
        'expense_labels_json': json.dumps(expense_labels, cls=DjangoJSONEncoder),
        'expense_breakdown_json': json.dumps(expense_breakdown, cls=DjangoJSONEncoder),
        
        # Expense categories for dropdown
        'expense_categories': expense_categories,
        
        # Current date
        'today': today,
        'current_time': timezone.now().strftime('%H:%M:%S'),
    }
    
    return render(request, 'index.html', context)


# === API ENDPOINTS FOR AJAX OPERATIONS ===

@require_http_methods(["GET"])
def get_sales_data(request):
    """API endpoint to get sales data for tables and charts"""
    sales = FuelSale.objects.select_related('fuel_type').order_by('-created_at')
    data = []
    for sale in sales:
        data.append({
            'id': sale.transaction_id,
            'dt': sale.created_at.strftime('%Y-%m-%d %H:%M'),
            'fuel': sale.fuel_type.name,
            'liters': float(sale.liters),
            'price': float(sale.price_per_liter),
            'total': float(sale.total_amount),
            'cashier': sale.cashier_name,
            'status': sale.status,
        })
    return JsonResponse({'sales': data})


@require_http_methods(["GET"])
def get_expense_data(request):
    """API endpoint to get expense data"""
    expenses = Expense.objects.select_related('category').order_by('-expense_date')
    data = []
    for exp in expenses:
        data.append({
            'id': exp.expense_id,
            'date': exp.expense_date.strftime('%Y-%m-%d'),
            'cat': exp.category.name,
            'desc': exp.description,
            'amount': float(exp.amount),
            'by': exp.approved_by_name,
            'status': exp.status,
        })
    return JsonResponse({'expenses': data})


@require_http_methods(["GET"])
def get_stock_data(request):
    """API endpoint to get fuel stock data"""
    fuel_types = FuelType.objects.all()
    data = []
    for ft in fuel_types:
        data.append({
            'type': ft.name,
            'tank': f'Tank {ft.id}',
            'vol': float(ft.current_stock),
            'cap': ft.tank_capacity,
            'color': ft.color,
            'pct': ft.stock_percentage,
            'is_low': ft.is_low_stock,
        })
    return JsonResponse({'stock': data})


@require_http_methods(["GET"])
def get_payroll_data(request):
    """API endpoint to get payroll data"""
    employees = Employee.objects.all().order_by('last_name')
    data = []
    for emp in employees:
        data.append({
            'id': emp.employee_id,
            'name': emp.full_name,
            'role': emp.role,
            'basic': float(emp.basic_pay),
            'allow': float(emp.allowance),
            'ded': float(emp.deductions),
            'net': float(emp.net_pay),
            'status': emp.payroll_status,
        })
    return JsonResponse({'employees': data})


@require_http_methods(["GET"])
def get_delivery_data(request):
    """API endpoint to get delivery data"""
    deliveries = FuelDelivery.objects.select_related('fuel_type').order_by('-delivery_date')
    data = []
    for del_obj in deliveries:
        data.append({
            'id': del_obj.delivery_id,
            'date': del_obj.delivery_date.strftime('%Y-%m-%d'),
            'fuel': del_obj.fuel_type.name,
            'vol': del_obj.volume,
            'supplier': del_obj.supplier,
            'cost': float(del_obj.cost),
            'status': del_obj.status,
        })
    return JsonResponse({'deliveries': data})


@require_http_methods(["GET"])
def get_user_data(request):
    """API endpoint to get user data"""
    profiles = UserProfile.objects.select_related('user').all()
    data = []
    for profile in profiles:
        last_login = profile.user.last_login
        data.append({
            'id': f'USR-{profile.user.id:03d}',
            'name': profile.user.get_full_name() or profile.user.username,
            'user': profile.user.username,
            'role': profile.role,
            'branch': profile.branch,
            'login': last_login.strftime('%Y-%m-%d %H:%M') if last_login else 'Never',
            'status': 'Active' if profile.is_active else 'Inactive',
        })
    return JsonResponse({'users': data})


@require_http_methods(["GET"])
def get_dashboard_stats(request):
    """API endpoint for dashboard statistics"""
    today = timezone.now().date()
    
    today_sales = FuelSale.objects.filter(
        created_at__date=today, 
        status='Paid'
    )
    today_revenue = sum(sale.total_amount for sale in today_sales)
    
    month_expenses = Expense.objects.filter(
        expense_date__month=today.month,
        expense_date__year=today.year,
        status='Approved'
    )
    total_expenses = sum(exp.amount for exp in month_expenses)
    
    daily_avg_expenses = total_expenses / Decimal(today.day) if today.day > 0 else Decimal(0)
    net_profit = today_revenue - daily_avg_expenses
    
    return JsonResponse({
        'today_revenue': float(today_revenue),
        'total_expenses': float(total_expenses),
        'net_profit': float(net_profit),
        'total_transactions': today_sales.count(),
    })


# === CRUD OPERATIONS ===

@require_http_methods(["POST"])
@csrf_exempt
def add_sale(request):
    """Add a new fuel sale - starts as Pending by default"""
    try:
        data = json.loads(request.body)
        fuel_type = FuelType.objects.get(name=data['fuel'])
        
        sale = FuelSale(
            fuel_type=fuel_type,
            liters=Decimal(str(data['liters'])),
            price_per_liter=Decimal(str(data.get('price', fuel_type.price_per_liter))),
            cashier_name=data.get('cashier', 'Unknown'),
            payment_method=data.get('payment_method', 'Cash'),
            status='Pending',  # Default to Pending - admin can edit to Paid/Unsuccessful
            notes=data.get('notes', ''),
        )
        sale.save()
        
        return JsonResponse({'success': True, 'transaction_id': sale.transaction_id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
@csrf_exempt
def add_expense(request):
    """Add a new expense"""
    try:
        data = json.loads(request.body)
        category = ExpenseCategory.objects.get(name=data['category'])
        
        # Parse date - handle both 'date' and 'expense_date' keys
        expense_date = timezone.now().date()
        if data.get('date'):
            expense_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        elif data.get('expense_date'):
            expense_date = datetime.strptime(data['expense_date'], '%Y-%m-%d').date()
        
        expense = Expense(
            category=category,
            description=data['description'],
            amount=Decimal(str(data['amount'])),
            expense_date=expense_date,
            approved_by_name=data.get('approved_by', 'Admin'),
            status=data.get('status', 'Pending'),  # Default to Pending - requires approval
        )
        expense.save()
        
        return JsonResponse({'success': True, 'expense_id': expense.expense_id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
@csrf_exempt
def add_employee(request):
    """Add a new employee"""
    try:
        data = json.loads(request.body)
        
        employee = Employee(
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data['role'],
            basic_pay=Decimal(str(data['basic_pay'])),
            allowance=Decimal(str(data.get('allowance', 0))),
            deductions=Decimal(str(data.get('deductions', 0))),
        )
        employee.save()
        
        return JsonResponse({'success': True, 'employee_id': employee.employee_id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
@csrf_exempt
def add_delivery(request):
    """Add a new fuel delivery and create expense if delivered"""
    try:
        data = json.loads(request.body)
        fuel_type = FuelType.objects.get(name=data['fuel'])
        
        delivery_date = datetime.strptime(data['date'], '%Y-%m-%d').date() if data.get('date') else timezone.now().date()
        
        delivery = FuelDelivery(
            fuel_type=fuel_type,
            volume=int(data['volume']),
            supplier=data['supplier'],
            cost=Decimal(str(data['cost'])),
            delivery_date=delivery_date,
            status=data.get('status', 'Scheduled'),
        )
        delivery.save()
        
        # Update fuel stock if delivered
        if delivery.status == 'Delivered':
            fuel_type.current_stock += delivery.volume
            fuel_type.save()
            
            # Create an expense record for this delivery (Fuel Restock expense)
            restock_category, _ = ExpenseCategory.objects.get_or_create(
                name='Fuel Restock',
                defaults={'description': 'Expenses for fuel inventory replenishment'}
            )
            
            expense = Expense.objects.create(
                category=restock_category,
                description=f"Fuel delivery: {data['volume']}L of {data['fuel']} from {data['supplier']}",
                amount=Decimal(str(data['cost'])),
                expense_date=delivery_date,
                approved_by_name='System (Fuel Delivery)',
                status='Approved'  # Auto-approve since it's a confirmed delivery
            )
        
        return JsonResponse({'success': True, 'delivery_id': delivery.delivery_id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
@csrf_exempt
def add_user(request):
    """Add a new user"""
    try:
        data = json.loads(request.body)
        
        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
        )
        
        profile = UserProfile.objects.create(
            user=user,
            role=data.get('role', 'Viewer'),
            branch=data.get('branch', 'Main - Cebu City'),
            can_view_sales=data.get('can_view_sales', True),
            can_edit_sales=data.get('can_edit_sales', False),
            can_delete_records=data.get('can_delete_records', False),
            can_view_reports=data.get('can_view_reports', True),
            can_export_reports=data.get('can_export_reports', False),
            can_manage_users=data.get('can_manage_users', False),
        )
        
        return JsonResponse({'success': True, 'user_id': user.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
@csrf_exempt
def delete_sale(request, txn_id):
    """Delete a fuel sale"""
    try:
        sale = FuelSale.objects.get(transaction_id=txn_id)
        # Restore fuel stock
        sale.fuel_type.current_stock += sale.liters
        sale.fuel_type.save()
        sale.delete()
        return JsonResponse({'success': True})
    except FuelSale.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Sale not found'}, status=404)


@require_http_methods(["POST"])
@csrf_exempt
def delete_expense(request, exp_id):
    """Delete an expense"""
    try:
        expense = Expense.objects.get(expense_id=exp_id)
        expense.delete()
        return JsonResponse({'success': True})
    except Expense.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Expense not found'}, status=404)


@require_http_methods(["POST"])
@csrf_exempt
def delete_employee(request, emp_id):
    """Delete an employee"""
    try:
        employee = Employee.objects.get(employee_id=emp_id)
        employee.delete()
        return JsonResponse({'success': True})
    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Employee not found'}, status=404)


@require_http_methods(["POST"])
@csrf_exempt
def delete_delivery(request, del_id):
    """Delete a delivery"""
    try:
        delivery = FuelDelivery.objects.get(delivery_id=del_id)
        # If delivered, remove from stock
        if delivery.status == 'Delivered':
            delivery.fuel_type.current_stock -= delivery.volume
            delivery.fuel_type.save()
        delivery.delete()
        return JsonResponse({'success': True})
    except FuelDelivery.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Delivery not found'}, status=404)


@require_http_methods(["POST"])
@csrf_exempt
def delete_user(request, user_id):
    """Delete a user"""
    try:
        user = User.objects.get(id=user_id)
        # Prevent deleting the last admin
        admin_count = UserProfile.objects.filter(role='Admin', is_active=True).count()
        if admin_count <= 1 and hasattr(user, 'profile') and user.profile.role == 'Admin':
            return JsonResponse({'success': False, 'error': 'Cannot delete last admin'}, status=400)
        user.delete()
        return JsonResponse({'success': True})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)


@require_http_methods(["POST"])
@csrf_exempt
def approve_expense(request, exp_id):
    """Approve an expense"""
    try:
        expense = Expense.objects.get(expense_id=exp_id)
        expense.status = 'Approved'
        expense.save()
        return JsonResponse({'success': True})
    except Expense.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Expense not found'}, status=404)


@require_http_methods(["POST"])
@csrf_exempt
def reject_expense(request, exp_id):
    """Reject an expense"""
    try:
        expense = Expense.objects.get(expense_id=exp_id)
        expense.status = 'Rejected'
        expense.save()
        return JsonResponse({'success': True})
    except Expense.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Expense not found'}, status=404)


@require_http_methods(["POST"])
@csrf_exempt
def pay_employee(request, emp_id):
    """Mark an employee as paid and create an expense record for the payroll"""
    try:
        employee = Employee.objects.get(employee_id=emp_id)
        
        if employee.payroll_status == 'Paid':
            return JsonResponse({'success': False, 'error': 'Employee already paid'}, status=400)
        
        # Mark employee as paid
        employee.payroll_status = 'Paid'
        employee.save()
        
        # Get or create the Salaries expense category
        salary_category, _ = ExpenseCategory.objects.get_or_create(
            name='Salaries',
            defaults={'description': 'Employee salaries and wages'}
        )
        
        # Create an expense record for this payroll payment
        today = timezone.now().date()
        expense = Expense.objects.create(
            category=salary_category,
            description=f"Payroll payment for {employee.full_name} ({employee.role}) - {today.strftime('%B %Y')}",
            amount=employee.net_pay,
            expense_date=today,
            approved_by_name='System (Payroll)',
            status='Approved'  # Auto-approve since it's a confirmed payment
        )
        
        return JsonResponse({'success': True, 'expense_id': expense.expense_id})
    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Employee not found'}, status=404)


@require_http_methods(["POST"])
@csrf_exempt
def approve_sale(request, txn_id):
    """Approve a pending sale - mark as Paid and deduct fuel stock"""
    try:
        sale = FuelSale.objects.get(transaction_id=txn_id)
        if sale.status != 'Pending':
            return JsonResponse({'success': False, 'error': 'Only pending sales can be approved'}, status=400)
        
        sale.status = 'Paid'
        sale.save()
        
        # Deduct fuel stock
        sale.fuel_type.current_stock -= sale.liters
        sale.fuel_type.save()
        
        return JsonResponse({'success': True})
    except FuelSale.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Sale not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
@csrf_exempt
def deny_sale(request, txn_id):
    """Deny a pending sale - mark as Unsuccessful"""
    try:
        sale = FuelSale.objects.get(transaction_id=txn_id)
        if sale.status != 'Pending':
            return JsonResponse({'success': False, 'error': 'Only pending sales can be denied'}, status=400)
        
        sale.status = 'Unsuccessful'
        sale.save()
        
        return JsonResponse({'success': True})
    except FuelSale.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Sale not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


