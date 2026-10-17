from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
import random

from Gasoline.models import (
    FuelType, FuelSale, ExpenseCategory, Expense,
    Employee, FuelDelivery, UserProfile
)


class Command(BaseCommand):
    help = 'Set up sample data for the FuelOps dashboard'

    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up sample data...')

        # Check if data already exists
        if FuelType.objects.exists():
            self.stdout.write(self.style.WARNING('Sample data already exists. Skipping setup.'))
            return

        # Create admin user
        admin_user = User.objects.create_superuser(
            username='admin',
            password='admin123',
            first_name='Juan',
            last_name='Reyes',
            email='admin@fuelops.com'
        )
        UserProfile.objects.create(
            user=admin_user,
            role='Admin',
            branch='Main - Cebu City',
            is_active=True,
            can_view_sales=True,
            can_edit_sales=True,
            can_delete_records=True,
            can_view_reports=True,
            can_export_reports=True,
            can_manage_users=True
        )
        self.stdout.write('Created admin user (username: admin, password: admin123)')

        # Create fuel types
        fuel_types_data = [
            {'name': 'Unleaded 91', 'price': Decimal('58.50'), 'capacity': 15000, 'stock': 8200, 'color': '#f5a623'},
            {'name': 'Unleaded 97', 'price': Decimal('62.10'), 'capacity': 10000, 'stock': 6400, 'color': '#4a9eff'},
            {'name': 'Diesel', 'price': Decimal('54.20'), 'capacity': 15000, 'stock': 2700, 'color': '#2ec97e'},
            {'name': 'Premium Diesel', 'price': Decimal('57.00'), 'capacity': 10000, 'stock': 2200, 'color': '#9b7fe8'},
        ]

        fuel_types = {}
        for ft_data in fuel_types_data:
            ft = FuelType.objects.create(
                name=ft_data['name'],
                price_per_liter=ft_data['price'],
                tank_capacity=ft_data['capacity'],
                current_stock=ft_data['stock'],
                color=ft_data['color'],
                low_stock_threshold=3000
            )
            fuel_types[ft_data['name']] = ft
            self.stdout.write(f'Created fuel type: {ft.name}')

        # Create expense categories
        categories_data = [
            {'name': 'Fuel Restock', 'desc': 'Expenses for fuel inventory replenishment'},
            {'name': 'Utilities', 'desc': 'Electricity, water, and other utilities'},
            {'name': 'Maintenance', 'desc': 'Equipment and facility maintenance'},
            {'name': 'Salaries', 'desc': 'Employee salaries and wages'},
            {'name': 'Miscellaneous', 'desc': 'Other operational expenses'},
        ]

        categories = {}
        for cat_data in categories_data:
            cat = ExpenseCategory.objects.create(
                name=cat_data['name'],
                description=cat_data['desc']
            )
            categories[cat_data['name']] = cat

        # Create users and cashiers
        users_data = [
            {'username': 'msantos', 'fname': 'Maria', 'lname': 'Santos', 'role': 'Cashier'},
            {'username': 'jcruz', 'fname': 'Jose', 'lname': 'Cruz', 'role': 'Cashier'},
            {'username': 'areyes', 'fname': 'Ana', 'lname': 'Reyes', 'role': 'Cashier'},
            {'username': 'plopez', 'fname': 'Pedro', 'lname': 'Lopez', 'role': 'Cashier'},
            {'username': 'rtan', 'fname': 'Roberto', 'lname': 'Tan', 'role': 'Manager'},
        ]

        users = {}
        for u_data in users_data:
            user = User.objects.create_user(
                username=u_data['username'],
                password='password123',
                first_name=u_data['fname'],
                last_name=u_data['lname'],
                email=f"{u_data['username']}@fuelops.com"
            )
            profile = UserProfile.objects.create(
                user=user,
                role=u_data['role'],
                branch='Main - Cebu City',
                is_active=True,
                can_view_sales=True,
                can_edit_sales=u_data['role'] in ['Cashier', 'Manager'],
                can_view_reports=True
            )
            users[u_data['username']] = user

        # Create employees
        employees_data = [
            {'fname': 'Maria', 'lname': 'Santos', 'role': 'Cashier', 'pay': 18000, 'allow': 3000, 'ded': 2100},
            {'fname': 'Jose', 'lname': 'Cruz', 'role': 'Pump Attendant', 'pay': 15000, 'allow': 2000, 'ded': 1800},
            {'fname': 'Ana', 'lname': 'Reyes', 'role': 'Cashier', 'pay': 18000, 'allow': 3000, 'ded': 2100},
            {'fname': 'Pedro', 'lname': 'Lopez', 'role': 'Pump Attendant', 'pay': 15000, 'allow': 2000, 'ded': 1800},
            {'fname': 'Roberto', 'lname': 'Tan', 'role': 'Supervisor', 'pay': 28000, 'allow': 5000, 'ded': 3500},
            {'fname': 'Carla', 'lname': 'Mendoza', 'role': 'Pump Attendant', 'pay': 15000, 'allow': 2000, 'ded': 1800},
            {'fname': 'Miguel', 'lname': 'Bautista', 'role': 'Pump Attendant', 'pay': 15000, 'allow': 2000, 'ded': 1800},
            {'fname': 'Liza', 'lname': 'Villanueva', 'role': 'Cashier', 'pay': 18000, 'allow': 3000, 'ded': 2100},
        ]

        payroll_statuses = ['Paid', 'Pending']
        for i, emp_data in enumerate(employees_data):
            Employee.objects.create(
                first_name=emp_data['fname'],
                last_name=emp_data['lname'],
                role=emp_data['role'],
                basic_pay=Decimal(str(emp_data['pay'])),
                allowance=Decimal(str(emp_data['allow'])),
                deductions=Decimal(str(emp_data['ded'])),
                payroll_status=payroll_statuses[i % 2],
                status='Active',
                hire_date=datetime.now().date() - timedelta(days=random.randint(30, 365))
            )

        # Create fuel sales for the past 30 days
        today = timezone.now().date()
        cashiers = ['Maria Santos', 'Jose Cruz', 'Ana Reyes', 'Pedro Lopez']
        fuel_names = list(fuel_types.keys())

        for day_offset in range(30):
            sale_date = today - timedelta(days=day_offset)
            # Create 3-8 sales per day
            num_sales = random.randint(3, 8)
            for _ in range(num_sales):
                fuel_name = random.choice(fuel_names)
                ft = fuel_types[fuel_name]
                liters = Decimal(str(random.uniform(10, 100)))
                sale = FuelSale.objects.create(
                    fuel_type=ft,
                    liters=liters,
                    price_per_liter=ft.price_per_liter,
                    total_amount=liters * ft.price_per_liter,
                    cashier_name=random.choice(cashiers),
                    status='Paid',
                    payment_method=random.choice(['Cash', 'GCash', 'Card'])
                )
                sale.created_at = datetime.combine(sale_date, datetime.min.time()) + timedelta(
                    hours=random.randint(6, 22),
                    minutes=random.randint(0, 59)
                )
                sale.save()

        self.stdout.write(self.style.SUCCESS(f'Created fuel sales for past 30 days'))

        # Create expenses
        expense_data = [
            {'cat': 'Fuel Restock', 'desc': 'Unleaded 91 - 10,000L from Petron', 'amount': 585000, 'days_ago': 1},
            {'cat': 'Utilities', 'desc': 'Electric bill - current month', 'amount': 18400, 'days_ago': 2},
            {'cat': 'Maintenance', 'desc': 'Pump #3 repair and calibration', 'amount': 8500, 'days_ago': 5},
            {'cat': 'Utilities', 'desc': 'Water bill - current month', 'amount': 3200, 'days_ago': 7},
            {'cat': 'Miscellaneous', 'desc': 'Office supplies and cleaning materials', 'amount': 2800, 'days_ago': 10},
            {'cat': 'Maintenance', 'desc': 'Security camera system upgrade', 'amount': 12000, 'days_ago': 15},
            {'cat': 'Fuel Restock', 'desc': 'Diesel - 12,000L from Phoenix', 'amount': 650400, 'days_ago': 20},
            {'cat': 'Salaries', 'desc': 'Monthly payroll - first half', 'amount': 72900, 'days_ago': 15},
        ]

        for exp_data in expense_data:
            Expense.objects.create(
                category=categories[exp_data['cat']],
                description=exp_data['desc'],
                amount=Decimal(str(exp_data['amount'])),
                expense_date=today - timedelta(days=exp_data['days_ago']),
                approved_by=admin_user,
                approved_by_name='Juan Reyes',
                status='Approved'
            )

        self.stdout.write(self.style.SUCCESS('Created expense records'))

        # Create fuel deliveries
        delivery_data = [
            {'fuel': 'Unleaded 91', 'vol': 10000, 'supplier': 'Petron Corp.', 'cost': 585000, 'days_ago': 1, 'status': 'Delivered'},
            {'fuel': 'Unleaded 97', 'vol': 8000, 'supplier': 'Shell Philippines', 'cost': 496800, 'days_ago': 5, 'status': 'Delivered'},
            {'fuel': 'Diesel', 'vol': 12000, 'supplier': 'Phoenix Petroleum', 'cost': 650400, 'days_ago': 10, 'status': 'Delivered'},
            {'fuel': 'Premium Diesel', 'vol': 6000, 'supplier': 'Petron Corp.', 'cost': 342000, 'days_ago': 15, 'status': 'Delivered'},
            {'fuel': 'Diesel', 'vol': 15000, 'supplier': 'Phoenix Petroleum', 'cost': 813000, 'days_ago': -2, 'status': 'Scheduled'},
        ]

        for del_data in delivery_data:
            FuelDelivery.objects.create(
                fuel_type=fuel_types[del_data['fuel']],
                volume=del_data['vol'],
                supplier=del_data['supplier'],
                cost=Decimal(str(del_data['cost'])),
                delivery_date=today - timedelta(days=del_data['days_ago']),
                status=del_data['status']
            )

        self.stdout.write(self.style.SUCCESS('Created fuel delivery records'))

        self.stdout.write(self.style.SUCCESS('Sample data setup complete!'))
        self.stdout.write(self.style.WARNING('Login credentials: username=admin, password=admin123'))