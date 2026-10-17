from django.core.management.base import BaseCommand
from Gasoline.models import ExpenseCategory


class Command(BaseCommand):
    help = 'Seed default expense categories for the Expense module'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding expense categories...')

        categories_data = [
            {'name': 'Fuel Restock', 'desc': 'Expenses for fuel inventory replenishment'},
            {'name': 'Utilities', 'desc': 'Electricity, water, and other utilities'},
            {'name': 'Maintenance', 'desc': 'Equipment and facility maintenance'},
            {'name': 'Salaries', 'desc': 'Employee salaries and wages'},
            {'name': 'Miscellaneous', 'desc': 'Other operational expenses'},
            {'name': 'Insurance', 'desc': 'Business insurance premiums'},
            {'name': 'Taxes', 'desc': 'Government taxes and permits'},
            {'name': 'Marketing', 'desc': 'Advertising and promotional expenses'},
            {'name': 'Supplies', 'desc': 'Office and operational supplies'},
            {'name': 'Repairs', 'desc': 'Equipment and facility repairs'},
        ]

        created_count = 0
        skipped_count = 0

        for cat_data in categories_data:
            cat, created = ExpenseCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['desc']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {cat.name}'))
                created_count += 1
            else:
                self.stdout.write(self.style.WARNING(f'Skipped (already exists): {cat.name}'))
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nExpense categories seeding complete! Created: {created_count}, Skipped: {skipped_count}'
        ))