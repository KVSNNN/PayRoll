from django.contrib import admin
from .models import SalaryRecord, SalaryPayment


@admin.register(SalaryRecord)
class SalaryRecordAdmin(admin.ModelAdmin):
    list_display = ['employee', 'salary_month', 'net_salary', 'paid_amount',
                    'outstanding_balance', 'payment_status', 'is_completed']
    list_filter = ['payment_status', 'is_completed', 'month_year']
    search_fields = ['employee__employee_id', 'employee__name']
    readonly_fields = ['absent_days', 'salary_earned', 'net_salary', 'balance_salary',
                       'total_salary_paid', 'outstanding_balance', 'payment_status']


@admin.register(SalaryPayment)
class SalaryPaymentAdmin(admin.ModelAdmin):
    list_display = ['salary_record', 'amount', 'payment_date', 'payment_type', 'recorded_by']
    list_filter = ['payment_type', 'payment_date']
