import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from employees.models import Employee
from salary.models import SalaryRecord, SalaryPayment
from accounts.models import User


class Command(BaseCommand):
    help = 'Load sample employee and salary data for demonstration'

    def handle(self, *args, **options):
        admin = User.objects.filter(role='SUPER_ADMIN').first()

        # Sample employees
        employees_data = [
            {'name': 'Rahul Kumar', 'designation': 'Software Engineer', 'department': 'IT',
             'date_of_joining': datetime.date(2024, 1, 15), 'monthly_salary': Decimal('35000'),
             'phone': '+91 9876543210', 'email': 'rahul@company.com', 'bank_account': '1234567890'},
            {'name': 'Priya Sharma', 'designation': 'HR Manager', 'department': 'Human Resources',
             'date_of_joining': datetime.date(2023, 6, 1), 'monthly_salary': Decimal('45000'),
             'phone': '+91 9876543211', 'email': 'priya@company.com', 'bank_account': '1234567891'},
            {'name': 'Amit Patel', 'designation': 'Accountant', 'department': 'Finance',
             'date_of_joining': datetime.date(2024, 3, 10), 'monthly_salary': Decimal('30000'),
             'phone': '+91 9876543212', 'email': 'amit@company.com', 'bank_account': '1234567892'},
            {'name': 'Sneha Reddy', 'designation': 'Marketing Executive', 'department': 'Marketing',
             'date_of_joining': datetime.date(2025, 1, 5), 'monthly_salary': Decimal('28000'),
             'phone': '+91 9876543213', 'email': 'sneha@company.com', 'bank_account': '1234567893'},
            {'name': 'Vikram Singh', 'designation': 'Operations Manager', 'department': 'Operations',
             'date_of_joining': datetime.date(2022, 8, 20), 'monthly_salary': Decimal('50000'),
             'phone': '+91 9876543214', 'email': 'vikram@company.com', 'bank_account': '1234567894'},
            {'name': 'Deepa Nair', 'designation': 'UI/UX Designer', 'department': 'IT',
             'date_of_joining': datetime.date(2024, 9, 1), 'monthly_salary': Decimal('32000'),
             'phone': '+91 9876543215', 'email': 'deepa@company.com', 'bank_account': '1234567895'},
        ]

        created_employees = []
        for data in employees_data:
            emp, created = Employee.objects.get_or_create(
                name=data['name'],
                defaults={**data, 'created_by': admin}
            )
            created_employees.append(emp)
            if created:
                self.stdout.write(f'  Created employee: {emp.employee_id} - {emp.name}')

        # Sample salary records for June 2026
        salary_data = [
            # Rahul: Fully paid
            {'employee': created_employees[0], 'salary_month': 'June 2026',
             'month_year': datetime.date(2026, 6, 1), 'present_days': 28,
             'deduction_amount': Decimal('500'), 'deduction_remarks': 'Late attendance',
             'paid_amount': Decimal('20000'), 'payment_date': datetime.date(2026, 6, 30),
             'balance_paid': Decimal('12167'), 'balance_paid_date': datetime.date(2026, 7, 5)},
            # Priya: Fully paid
            {'employee': created_employees[1], 'salary_month': 'June 2026',
             'month_year': datetime.date(2026, 6, 1), 'present_days': 30,
             'deduction_amount': Decimal('0'), 'deduction_remarks': '',
             'paid_amount': Decimal('45000'), 'payment_date': datetime.date(2026, 6, 30),
             'balance_paid': Decimal('0'), 'balance_paid_date': None},
            # Amit: Partially paid
            {'employee': created_employees[2], 'salary_month': 'June 2026',
             'month_year': datetime.date(2026, 6, 1), 'present_days': 26,
             'deduction_amount': Decimal('1000'), 'deduction_remarks': 'Loan EMI',
             'paid_amount': Decimal('15000'), 'payment_date': datetime.date(2026, 6, 30),
             'balance_paid': Decimal('0'), 'balance_paid_date': None},
            # Sneha: Pending
            {'employee': created_employees[3], 'salary_month': 'June 2026',
             'month_year': datetime.date(2026, 6, 1), 'present_days': 25,
             'deduction_amount': Decimal('500'), 'deduction_remarks': 'Half-day deduction',
             'paid_amount': Decimal('0'), 'payment_date': None,
             'balance_paid': Decimal('0'), 'balance_paid_date': None},
            # Vikram: Fully paid
            {'employee': created_employees[4], 'salary_month': 'June 2026',
             'month_year': datetime.date(2026, 6, 1), 'present_days': 30,
             'deduction_amount': Decimal('0'), 'deduction_remarks': '',
             'paid_amount': Decimal('50000'), 'payment_date': datetime.date(2026, 6, 30),
             'balance_paid': Decimal('0'), 'balance_paid_date': None},
            # Deepa: Partially paid
            {'employee': created_employees[5], 'salary_month': 'June 2026',
             'month_year': datetime.date(2026, 6, 1), 'present_days': 27,
             'deduction_amount': Decimal('200'), 'deduction_remarks': 'Late attendance',
             'paid_amount': Decimal('20000'), 'payment_date': datetime.date(2026, 6, 30),
             'balance_paid': Decimal('0'), 'balance_paid_date': None},
        ]

        for data in salary_data:
            emp = data['employee']
            record, created = SalaryRecord.objects.get_or_create(
                employee=emp,
                month_year=data['month_year'],
                defaults={
                    'salary_month': data['salary_month'],
                    'monthly_salary': emp.monthly_salary,
                    'total_working_days': 30,
                    'present_days': data['present_days'],
                    'deduction_amount': data['deduction_amount'],
                    'deduction_remarks': data['deduction_remarks'],
                    'paid_amount': data['paid_amount'],
                    'payment_date': data['payment_date'],
                    'balance_paid': data['balance_paid'],
                    'balance_paid_date': data['balance_paid_date'],
                    'created_by': admin,
                }
            )
            if created:
                self.stdout.write(f'  Created salary: {emp.employee_id} - {data["salary_month"]} [{record.get_payment_status_display()}]')

        # Create a Cashier account
        cashier, created = User.objects.get_or_create(
            username='cashier1',
            defaults={
                'first_name': 'Arun',
                'last_name': 'Cashier',
                'email': 'cashier@company.com',
                'role': 'CASHIER',
            }
        )
        if created:
            cashier.set_password('Cashier@123')
            cashier.save()
            self.stdout.write(f'  Created Cashier: cashier1 / Cashier@123')

        # Create a Staff account linked to Rahul
        staff, created = User.objects.get_or_create(
            username='rahul',
            defaults={
                'first_name': 'Rahul',
                'last_name': 'Kumar',
                'email': 'rahul@company.com',
                'role': 'STAFF',
                'employee': created_employees[0],
            }
        )
        if created:
            staff.set_password('Staff@123')
            staff.save()
            self.stdout.write(f'  Created Staff: rahul / Staff@123')

        self.stdout.write(self.style.SUCCESS('\n[OK] Sample data loaded successfully!'))
        self.stdout.write(self.style.SUCCESS(
            '\nLogin credentials:\n'
            '  Super Admin: admin / Admin@123\n'
            '  Cashier: cashier1 / Cashier@123\n'
            '  Staff: rahul / Staff@123'
        ))
