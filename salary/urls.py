from django.urls import path
from . import views, reports, export

app_name = 'salary'

urlpatterns = [
    # Salary CRUD
    path('', views.salary_list, name='salary_list'),
    path('create/', views.salary_create, name='salary_create'),
    path('<int:pk>/', views.salary_detail, name='salary_detail'),
    path('<int:pk>/edit/', views.salary_edit, name='salary_edit'),
    path('<int:pk>/balance-payment/', views.balance_payment, name='balance_payment'),
    path('<int:pk>/toggle-lock/', views.salary_toggle_lock, name='salary_toggle_lock'),
    path('get-employee-salary/', views.get_employee_salary, name='get_employee_salary'),

    # Reports
    path('reports/monthly/', reports.report_monthly, name='report_monthly'),
    path('reports/pending/', reports.report_pending, name='report_pending'),
    path('reports/paid/', reports.report_paid, name='report_paid'),
    path('reports/balance/', reports.report_balance, name='report_balance'),
    path('reports/employee-history/', reports.report_employee_history, name='report_employee_history'),
    path('reports/deductions/', reports.report_deductions, name='report_deductions'),
    path('reports/attendance/', reports.report_attendance, name='report_attendance'),

    # Export
    path('export/excel/', export.export_excel, name='export_excel'),
    path('export/salary-slip/<int:pk>/', export.export_salary_slip_pdf, name='export_salary_slip'),
]
