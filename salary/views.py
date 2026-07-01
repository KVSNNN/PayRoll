from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from django.http import JsonResponse

from .models import SalaryRecord, SalaryPayment
from .forms import SalaryRecordForm, BalancePaymentForm, SalarySearchForm
from employees.models import Employee
from accounts.decorators import super_admin_required, cashier_or_admin_required
from audit.utils import log_action


@login_required
def salary_list(request):
    """List salary records with search and filters."""
    # Staff can only see their own records
    if request.user.is_staff_role:
        if request.user.employee:
            records = SalaryRecord.objects.filter(employee=request.user.employee)
        else:
            records = SalaryRecord.objects.none()
    else:
        records = SalaryRecord.objects.all()

    form = SalarySearchForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search', '')
        month = form.cleaned_data.get('month', '')
        year = form.cleaned_data.get('year', '')
        status = form.cleaned_data.get('status', '')

        if search:
            records = records.filter(
                Q(employee__employee_id__icontains=search) |
                Q(employee__name__icontains=search)
            )
        if month:
            records = records.filter(salary_month__icontains=month)
        if year:
            records = records.filter(month_year__year=int(year))
        if status:
            records = records.filter(payment_status=status)

    # Summary totals
    totals = records.aggregate(
        total_net=Sum('net_salary'),
        total_paid=Sum('total_salary_paid'),
        total_balance=Sum('outstanding_balance'),
    )

    return render(request, 'salary/salary_list.html', {
        'records': records,
        'form': form,
        'totals': totals,
    })


@login_required
@cashier_or_admin_required
def salary_create(request):
    """Create a new salary entry."""
    if request.method == 'POST':
        form = SalaryRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.created_by = request.user
            record.save()

            # Create payment transaction if paid_amount > 0 and record.payment_date:
            if record.paid_amount > 0 and record.payment_date:
                SalaryPayment.objects.create(
                    salary_record=record,
                    amount=record.paid_amount,
                    payment_date=record.payment_date,
                    payment_type='INITIAL',
                    recorded_by=request.user,
                )

            log_action(request, 'CREATE', 'SalaryRecord', record.pk, {
                'employee': record.employee.employee_id,
                'month': record.salary_month,
                'net_salary': str(record.net_salary),
            })
            messages.success(request, f'Salary entry for {record.employee.name} ({record.salary_month}) created.')
            return redirect('salary:salary_list')
    else:
        form = SalaryRecordForm()
    return render(request, 'salary/salary_form.html', {
        'form': form, 'title': 'New Salary Entry'
    })


@login_required
@cashier_or_admin_required
def salary_edit(request, pk):
    """Edit a salary record (blocked if completed for Cashier)."""
    record = get_object_or_404(SalaryRecord, pk=pk)

    # Block editing completed records for Cashier
    if record.is_completed and request.user.is_cashier:
        messages.error(request, 'This record is locked. Contact Super Admin to unlock.')
        return redirect('salary:salary_list')

    old_data = {
        'paid_amount': str(record.paid_amount),
        'deduction_amount': str(record.deduction_amount),
    }

    if request.method == 'POST':
        form = SalaryRecordForm(request.POST, instance=record)
        if form.is_valid():
            updated = form.save()
            changes = {}
            if old_data['paid_amount'] != str(updated.paid_amount):
                changes['paid_amount'] = {
                    'old': old_data['paid_amount'],
                    'new': str(updated.paid_amount)
                }
            log_action(request, 'UPDATE', 'SalaryRecord', updated.pk, changes)
            messages.success(request, f'Salary record updated for {updated.employee.name}.')
            return redirect('salary:salary_list')
    else:
        form = SalaryRecordForm(instance=record)
    return render(request, 'salary/salary_form.html', {
        'form': form, 'title': 'Edit Salary Entry', 'record': record
    })


@login_required
@cashier_or_admin_required
def balance_payment(request, pk):
    """Record a balance payment for a salary record."""
    record = get_object_or_404(SalaryRecord, pk=pk)

    if record.is_completed and request.user.is_cashier:
        messages.error(request, 'This record is locked.')
        return redirect('salary:salary_list')

    if record.outstanding_balance <= 0:
        messages.info(request, 'No outstanding balance for this record.')
        return redirect('salary:salary_list')

    if request.method == 'POST':
        form = BalancePaymentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['balance_paid']
            date = form.cleaned_data['balance_paid_date']

            if amount > record.outstanding_balance:
                messages.error(request, f'Payment amount cannot exceed outstanding balance of ₹{record.outstanding_balance:,.2f}')
            else:
                record.balance_paid = record.balance_paid + amount
                record.balance_paid_date = date
                record.save()

                SalaryPayment.objects.create(
                    salary_record=record,
                    amount=amount,
                    payment_date=date,
                    payment_type='BALANCE',
                    recorded_by=request.user,
                    remarks=form.cleaned_data.get('remarks', ''),
                )

                log_action(request, 'UPDATE', 'SalaryRecord', record.pk, {
                    'balance_paid': str(amount),
                    'balance_paid_date': str(date),
                })
                messages.success(request, f'Balance payment of ₹{amount:,.2f} recorded.')
                return redirect('salary:salary_list')
    else:
        form = BalancePaymentForm()

    return render(request, 'salary/balance_payment.html', {
        'form': form, 'record': record,
    })


@login_required
@super_admin_required
def salary_toggle_lock(request, pk):
    """Lock/Unlock a salary record (Super Admin only)."""
    record = get_object_or_404(SalaryRecord, pk=pk)

    if request.method == 'POST':
        record.is_completed = not record.is_completed
        if record.is_completed:
            record.completed_by = request.user
            record.completed_at = timezone.now()
            action = 'LOCK'
            msg = 'Record locked successfully.'
        else:
            record.completed_by = None
            record.completed_at = None
            action = 'UNLOCK'
            msg = 'Record unlocked successfully.'
        record.save()

        log_action(request, action, 'SalaryRecord', record.pk, {
            'is_completed': record.is_completed
        })
        messages.success(request, msg)
    return redirect('salary:salary_list')


@login_required
def salary_detail(request, pk):
    """View salary record details."""
    record = get_object_or_404(SalaryRecord, pk=pk)

    # Staff can only view their own records
    if request.user.is_staff_role:
        if not request.user.employee or request.user.employee != record.employee:
            messages.error(request, 'You can only view your own salary records.')
            return redirect('salary:salary_list')

    payments = record.payments.all().order_by('payment_date')
    return render(request, 'salary/salary_detail.html', {
        'record': record,
        'payments': payments,
    })


@login_required
@cashier_or_admin_required
def get_employee_salary(request):
    """AJAX endpoint to fetch employee's monthly salary."""
    employee_id = request.GET.get('employee_id')
    try:
        employee = Employee.objects.get(pk=employee_id)
        return JsonResponse({
            'success': True,
            'monthly_salary': str(employee.monthly_salary),
            'name': employee.name,
            'employee_id': employee.employee_id,
        })
    except Employee.DoesNotExist:
        return JsonResponse({'success': False})
