from django.contrib import admin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'name', 'designation', 'department', 'monthly_salary', 'status']
    list_filter = ['status', 'department']
    search_fields = ['employee_id', 'name', 'email']
    readonly_fields = ['employee_id']
