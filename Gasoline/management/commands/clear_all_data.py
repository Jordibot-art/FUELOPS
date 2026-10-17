from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import connection
from Gasoline.models import FuelSale, Expense, Employee, UserProfile, FuelDelivery


class Command(BaseCommand):
    help = 'Clear all Fuel Sales Records, Expense Records, Employee Payroll, and User Management data while maintaining functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        if not options['noinput']:
            self.stdout.write(self.style.WARNING(
                'This will permanently delete the following data:'
            ))
            self.stdout.write('  - All Fuel Sales Records')
            self.stdout.write('  - All Expense Records')
            self.stdout.write('  - All Employee Payroll Records')
            self.stdout.write('  - All User accounts (except superusers) and User Profiles')
            self.stdout.write('')
            confirm = input('Are you sure you want to continue? (yes/no): ')
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write(self.style.NOTICE('Operation cancelled.'))
                return

        # Count records before deletion for reporting
        fuel_sales_count = FuelSale.objects.count()
        expenses_count = Expense.objects.count()
        employees_count = Employee.objects.count()
        user_profiles_count = UserProfile.objects.count()
        # Count non-superuser users
        users_to_delete_count = User.objects.filter(is_superuser=False).count()
        superusers_count = User.objects.filter(is_superuser=True).count()

        # 1. Clear Fuel Sales Records
        FuelSale.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(
            f'✓ Deleted {fuel_sales_count} Fuel Sales Records'
        ))

        # 2. Clear Expense Records (keep categories for functionality)
        Expense.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(
            f'✓ Deleted {expenses_count} Expense Records'
        ))

        # 3. Clear Employee Payroll Records
        Employee.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(
            f'✓ Deleted {employees_count} Employee Payroll Records'
        ))

        # 4. Clear User Profiles first (they have OneToOne relationship with User)
        UserProfile.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(
            f'✓ Deleted {user_profiles_count} User Profiles'
        ))

        # 5. Clear non-superuser User accounts (keep superusers for admin access)
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.SUCCESS(
            f'✓ Deleted {users_to_delete_count} User accounts (kept {superusers_count} superuser accounts)'
        ))

        # Reset auto-increment counters (SQLite specific)
        self.stdout.write('')
        self.stdout.write('Resetting database sequences...')

        # Get all tables that might have auto-increment that we want to reset
        tables_to_reset = [
            ('Gasoline_fuelsale', 'id'),
            ('Gasoline_expense', 'id'),
            ('Gasoline_employee', 'id'),
            ('Gasoline_fueldelivery', 'id'),
            ('auth_user', 'id'),
            ('Gasoline_userprofile', 'id'),
        ]

        with connection.cursor() as cursor:
            for table, column in tables_to_reset:
                # Check if table exists
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=%s",
                    [table]
                )
                if cursor.fetchone():
                    # Reset the sqlite_sequence
                    cursor.execute(
                        f"DELETE FROM sqlite_sequence WHERE name=%s",
                        [table]
                    )

        self.stdout.write(self.style.SUCCESS('✓ Database sequences reset'))

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('All specified data has been cleared successfully!'))
        self.stdout.write('')
        self.stdout.write('The following data was preserved:')
        self.stdout.write('  - Fuel Types (for sales functionality)')
        self.stdout.write('  - Expense Categories (for expense functionality)')
        self.stdout.write('  - Superuser accounts (for admin access)')
        self.stdout.write('')
        self.stdout.write('The application functionality remains intact.')