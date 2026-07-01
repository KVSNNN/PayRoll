from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
import datetime

from employees.models import Employee
from salary.models import SalaryRecord
from audit.models import AuditLog


@login_required
def home(request):
    """Role-based dashboard home page."""
    if request.user.is_staff_role:
        return staff_dashboard(request)
    else:
        return admin_dashboard(request)


def admin_dashboard(request):
    """Dashboard for Super Admin and Cashier."""
    now = timezone.now()
    current_month = now.replace(day=1).date()

    # Employee stats
    total_employees = Employee.objects.filter(status='ACTIVE').count()
    total_inactive = Employee.objects.filter(status='INACTIVE').count()

    # Current month salary stats
    current_records = SalaryRecord.objects.filter(month_year=current_month)
    salary_stats = current_records.aggregate(
        total_net=Sum('net_salary'),
        total_paid=Sum('total_salary_paid'),
        total_balance=Sum('outstanding_balance'),
    )

    # Payment status counts
    pending_count = current_records.filter(payment_status='PENDING').count()
    partial_count = current_records.filter(payment_status='PARTIALLY_PAID').count()
    paid_count = current_records.filter(payment_status='PAID').count()
    completed_count = current_records.filter(is_completed=True).count()

    # All-time stats
    all_records = SalaryRecord.objects.all()
    all_stats = all_records.aggregate(
        all_time_paid=Sum('total_salary_paid'),
        all_time_balance=Sum('outstanding_balance'),
    )

    # Recent activity
    recent_logs = AuditLog.objects.all()[:10]

    # Recent pending records
    pending_records = SalaryRecord.objects.filter(
        payment_status__in=['PENDING', 'PARTIALLY_PAID']
    ).select_related('employee').order_by('-month_year')[:5]

    context = {
        'total_employees': total_employees,
        'total_inactive': total_inactive,
        'total_net_salary': salary_stats['total_net'] or 0,
        'total_paid': salary_stats['total_paid'] or 0,
        'total_balance': salary_stats['total_balance'] or 0,
        'pending_count': pending_count,
        'partial_count': partial_count,
        'paid_count': paid_count,
        'completed_count': completed_count,
        'all_time_paid': all_stats['all_time_paid'] or 0,
        'all_time_balance': all_stats['all_time_balance'] or 0,
        'recent_logs': recent_logs,
        'pending_records': pending_records,
        'current_month': now.strftime('%B %Y'),
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


def staff_dashboard(request):
    """Dashboard for Staff — shows only their own salary info."""
    employee = request.user.employee
    records = SalaryRecord.objects.none()
    totals = {}

    if employee:
        records = SalaryRecord.objects.filter(
            employee=employee
        ).order_by('-month_year')[:12]

        totals = SalaryRecord.objects.filter(employee=employee).aggregate(
            total_earned=Sum('net_salary'),
            total_received=Sum('total_salary_paid'),
            total_pending=Sum('outstanding_balance'),
        )

    return render(request, 'dashboard/staff_dashboard.html', {
        'employee': employee,
        'records': records,
        'totals': totals,
    })
