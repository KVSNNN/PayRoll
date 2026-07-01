from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponse
from decimal import Decimal

from .models import SalaryRecord
from employees.models import Employee
from accounts.decorators import cashier_or_admin_required


@login_required
@cashier_or_admin_required
def report_monthly(request):
    """Monthly Salary Report — all salaries for a given month."""
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')
    records = SalaryRecord.objects.all()

    if month:
        records = records.filter(salary_month__icontains=month)
    if year:
        records = records.filter(month_year__year=int(year))

    totals = records.aggregate(
        total_net=Sum('net_salary'),
        total_paid=Sum('total_salary_paid'),
        total_balance=Sum('outstanding_balance'),
        total_deductions=Sum('deduction_amount'),
    )

    return render(request, 'salary/reports/monthly_report.html', {
        'records': records,
        'totals': totals,
        'selected_month': month,
        'selected_year': year,
        'report_title': 'Monthly Salary Report',
    })


@login_required
@cashier_or_admin_required
def report_pending(request):
    """Pending Salary Report."""
    records = SalaryRecord.objects.filter(payment_status='PENDING')
    totals = records.aggregate(
        total_net=Sum('net_salary'),
        total_balance=Sum('outstanding_balance'),
    )
    return render(request, 'salary/reports/status_report.html', {
        'records': records,
        'totals': totals,
        'report_title': 'Pending Salary Report',
        'status_filter': 'PENDING',
    })


@login_required
@cashier_or_admin_required
def report_paid(request):
    """Paid Salary Report."""
    records = SalaryRecord.objects.filter(payment_status='PAID')
    totals = records.aggregate(
        total_net=Sum('net_salary'),
        total_paid=Sum('total_salary_paid'),
    )
    return render(request, 'salary/reports/status_report.html', {
        'records': records,
        'totals': totals,
        'report_title': 'Paid Salary Report',
        'status_filter': 'PAID',
    })


@login_required
@cashier_or_admin_required
def report_balance(request):
    """Balance Salary Report — records with outstanding balance."""
    records = SalaryRecord.objects.filter(outstanding_balance__gt=0)
    totals = records.aggregate(
        total_net=Sum('net_salary'),
        total_paid=Sum('total_salary_paid'),
        total_balance=Sum('outstanding_balance'),
    )
    return render(request, 'salary/reports/status_report.html', {
        'records': records,
        'totals': totals,
        'report_title': 'Balance Salary Report',
        'status_filter': 'BALANCE',
    })


@login_required
@cashier_or_admin_required
def report_employee_history(request):
    """Employee Salary History — all records for one employee."""
    employee_id = request.GET.get('employee_id', '')
    records = SalaryRecord.objects.none()
    employee = None

    if employee_id:
        try:
            employee = Employee.objects.get(pk=employee_id)
            records = SalaryRecord.objects.filter(employee=employee).order_by('-month_year')
        except Employee.DoesNotExist:
            pass

    employees = Employee.objects.filter(status='ACTIVE')
    totals = records.aggregate(
        total_net=Sum('net_salary'),
        total_paid=Sum('total_salary_paid'),
        total_balance=Sum('outstanding_balance'),
    )

    return render(request, 'salary/reports/employee_history.html', {
        'records': records,
        'employee': employee,
        'employees': employees,
        'totals': totals,
        'report_title': 'Employee Salary History',
    })


@login_required
@cashier_or_admin_required
def report_deductions(request):
    """Deduction Report — all records with deductions."""
    records = SalaryRecord.objects.filter(deduction_amount__gt=0).order_by('-month_year')
    totals = records.aggregate(
        total_deductions=Sum('deduction_amount'),
    )
    return render(request, 'salary/reports/deduction_report.html', {
        'records': records,
        'totals': totals,
        'report_title': 'Deduction Report',
    })


@login_required
@cashier_or_admin_required
def report_attendance(request):
    """Attendance-wise Salary Report — sorted by present days."""
    month = request.GET.get('month', '')
    year = request.GET.get('year', '')
    records = SalaryRecord.objects.all()

    if month:
        records = records.filter(salary_month__icontains=month)
    if year:
        records = records.filter(month_year__year=int(year))

    records = records.order_by('present_days')
    totals = records.aggregate(
        total_net=Sum('net_salary'),
    )

    return render(request, 'salary/reports/attendance_report.html', {
        'records': records,
        'totals': totals,
        'selected_month': month,
        'selected_year': year,
        'report_title': 'Attendance-wise Salary Report',
    })
