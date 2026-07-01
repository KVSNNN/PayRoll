from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse

from .models import Employee
from .forms import EmployeeForm, EmployeeSearchForm
from accounts.decorators import super_admin_required, cashier_or_admin_required
from audit.utils import log_action


@login_required
@cashier_or_admin_required
def employee_list(request):
    """List all employees with search and filter."""
    employees = Employee.objects.all()
    form = EmployeeSearchForm(request.GET)

    if form.is_valid():
        search = form.cleaned_data.get('search', '')
        status = form.cleaned_data.get('status', '')
        department = form.cleaned_data.get('department', '')

        if search:
            employees = employees.filter(
                Q(employee_id__icontains=search) |
                Q(name__icontains=search) |
                Q(designation__icontains=search)
            )
        if status:
            employees = employees.filter(status=status)
        if department:
            employees = employees.filter(department__icontains=department)

    return render(request, 'employees/employee_list.html', {
        'employees': employees,
        'form': form,
        'total_count': Employee.objects.count(),
        'active_count': Employee.objects.filter(status='ACTIVE').count(),
    })


@login_required
@super_admin_required
def employee_create(request):
    """Create a new employee (Super Admin only)."""
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.created_by = request.user
            employee.save()
            log_action(request, 'CREATE', 'Employee', employee.pk, {
                'employee_id': employee.employee_id,
                'name': employee.name,
            })
            messages.success(request, f'Employee {employee.employee_id} - {employee.name} created successfully.')
            return redirect('employees:employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'employees/employee_form.html', {
        'form': form, 'title': 'Add New Employee'
    })


@login_required
@super_admin_required
def employee_edit(request, pk):
    """Edit an employee (Super Admin only)."""
    employee = get_object_or_404(Employee, pk=pk)
    old_salary = employee.monthly_salary

    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            updated = form.save()
            changes = {}
            if old_salary != updated.monthly_salary:
                changes['monthly_salary'] = {
                    'old': str(old_salary), 'new': str(updated.monthly_salary)
                }
            log_action(request, 'UPDATE', 'Employee', updated.pk, changes)
            messages.success(request, f'Employee {updated.employee_id} updated successfully.')
            return redirect('employees:employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'employees/employee_form.html', {
        'form': form, 'title': 'Edit Employee', 'employee': employee
    })


@login_required
@super_admin_required
def employee_delete(request, pk):
    """Soft-delete an employee (set to Inactive) — Super Admin only."""
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.status = 'INACTIVE'
        employee.save(update_fields=['status'])
        log_action(request, 'DELETE', 'Employee', employee.pk, {
            'action': 'soft_delete', 'name': employee.name
        })
        messages.success(request, f'Employee {employee.employee_id} has been deactivated.')
        return redirect('employees:employee_list')
    return render(request, 'employees/employee_confirm_delete.html', {'employee': employee})


@login_required
@cashier_or_admin_required
def employee_detail(request, pk):
    """View employee details."""
    employee = get_object_or_404(Employee, pk=pk)
    salary_records = employee.salary_records.all().order_by('-month_year')
    return render(request, 'employees/employee_detail.html', {
        'employee': employee,
        'salary_records': salary_records,
    })


@login_required
@cashier_or_admin_required
def employee_search_ajax(request):
    """AJAX endpoint for employee search autocomplete."""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})

    employees = Employee.objects.filter(
        Q(employee_id__icontains=query) |
        Q(name__icontains=query),
        status='ACTIVE'
    )[:10]

    results = [{
        'id': emp.pk,
        'employee_id': emp.employee_id,
        'name': emp.name,
        'designation': emp.designation,
        'department': emp.department,
        'monthly_salary': str(emp.monthly_salary),
    } for emp in employees]

    return JsonResponse({'results': results})
