from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'employees'
    verbose_name = 'Employee Management'

    def ready(self):
        from payroll_project.supabase_sync import register_signals
        register_signals()
