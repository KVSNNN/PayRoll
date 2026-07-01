import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from employees.models import Employee
from salary.models import SalaryRecord, SalaryPayment
from audit.models import AuditLog
from payroll_project.supabase_sync import serialize_instance, MODEL_TABLE_MAP

# The SQL schema required on Supabase side
SQL_DDL_SCHEMA = """
-- =========================================================================
-- RUN THIS IN THE SUPABASE SQL EDITOR BEFORE SYNCING
-- =========================================================================

-- 1. Create employees_employee table
CREATE TABLE IF NOT EXISTS public.employees_employee (
    id bigint PRIMARY KEY,
    employee_id varchar(20) NOT NULL,
    name varchar(200) NOT NULL,
    designation varchar(100) NOT NULL,
    department varchar(100) NOT NULL,
    date_of_joining date NOT NULL,
    monthly_salary numeric(12, 2) NOT NULL,
    bank_account varchar(30),
    phone varchar(15),
    email varchar(254),
    status varchar(10) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    created_by_id bigint
);
ALTER TABLE public.employees_employee DISABLE ROW LEVEL SECURITY;

-- 2. Create accounts_user table
CREATE TABLE IF NOT EXISTS public.accounts_user (
    id bigint PRIMARY KEY,
    password varchar(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username varchar(150) NOT NULL,
    first_name varchar(150) NOT NULL,
    last_name varchar(150) NOT NULL,
    email varchar(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL,
    role varchar(20) NOT NULL,
    phone varchar(15),
    failed_login_attempts integer NOT NULL,
    locked_until timestamp with time zone,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    employee_id bigint REFERENCES public.employees_employee(id) ON DELETE SET NULL
);
ALTER TABLE public.accounts_user DISABLE ROW LEVEL SECURITY;

-- 3. Create salary_salaryrecord table
CREATE TABLE IF NOT EXISTS public.salary_salaryrecord (
    id bigint PRIMARY KEY,
    salary_month varchar(20) NOT NULL,
    month_year date NOT NULL,
    monthly_salary numeric(12, 2) NOT NULL,
    total_working_days integer NOT NULL,
    present_days integer NOT NULL,
    absent_days integer NOT NULL,
    salary_earned numeric(12, 2) NOT NULL,
    deduction_amount numeric(12, 2) NOT NULL,
    deduction_remarks text,
    net_salary numeric(12, 2) NOT NULL,
    paid_amount numeric(12, 2) NOT NULL,
    payment_date date,
    balance_salary numeric(12, 2) NOT NULL,
    balance_paid numeric(12, 2) NOT NULL,
    balance_paid_date date,
    total_salary_paid numeric(12, 2) NOT NULL,
    outstanding_balance numeric(12, 2) NOT NULL,
    payment_status varchar(20) NOT NULL,
    is_completed boolean NOT NULL,
    completed_at timestamp with time zone,
    remarks text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    completed_by_id bigint REFERENCES public.accounts_user(id) ON DELETE SET NULL,
    created_by_id bigint REFERENCES public.accounts_user(id) ON DELETE SET NULL,
    employee_id bigint NOT NULL REFERENCES public.employees_employee(id) ON DELETE CASCADE
);
ALTER TABLE public.salary_salaryrecord DISABLE ROW LEVEL SECURITY;

-- 4. Create salary_salarypayment table
CREATE TABLE IF NOT EXISTS public.salary_salarypayment (
    id bigint PRIMARY KEY,
    amount numeric(12, 2) NOT NULL,
    payment_date date NOT NULL,
    payment_type varchar(10) NOT NULL,
    remarks text,
    created_at timestamp with time zone NOT NULL,
    recorded_by_id bigint REFERENCES public.accounts_user(id) ON DELETE SET NULL,
    salary_record_id bigint NOT NULL REFERENCES public.salary_salaryrecord(id) ON DELETE CASCADE
);
ALTER TABLE public.salary_salarypayment DISABLE ROW LEVEL SECURITY;

-- 5. Create audit_auditlog table
CREATE TABLE IF NOT EXISTS public.audit_auditlog (
    id bigint PRIMARY KEY,
    username varchar(150) NOT NULL,
    action varchar(10) NOT NULL,
    model_name varchar(50) NOT NULL,
    record_id integer,
    changes jsonb,
    ip_address inet,
    user_agent varchar(500),
    timestamp timestamp with time zone NOT NULL,
    user_id bigint REFERENCES public.accounts_user(id) ON DELETE SET NULL
);
ALTER TABLE public.audit_auditlog DISABLE ROW LEVEL SECURITY;
"""

class Command(BaseCommand):
    help = "Bulk syncs existing Django SQLite database records to Supabase."

    def handle(self, *args, **options):
        url = getattr(settings, "SUPABASE_URL", None)
        key = getattr(settings, "SUPABASE_ANON_KEY", None)

        if not url or not key:
            self.stdout.write(self.style.ERROR("Supabase settings not configured in settings.py!"))
            return

        User = get_user_model()
        
        # Models ordered by dependencies (FKs)
        models_to_sync = [
            (Employee, "Employee"),
            (User, "User"),
            (SalaryRecord, "SalaryRecord"),
            (SalaryPayment, "SalaryPayment"),
            (AuditLog, "AuditLog"),
        ]

        # Temporarily disconnect signals to prevent triggering individual background threads
        from django.db.models.signals import post_save, post_delete
        from payroll_project.supabase_sync import handle_save, handle_delete

        self.stdout.write(self.style.WARNING("Temporarily disabling sync signals for bulk export..."))
        for model_cls, name in models_to_sync:
            post_save.disconnect(handle_save, sender=model_cls, dispatch_uid=f"supabase_sync_save_{model_cls.__name__}")
            post_delete.disconnect(handle_delete, sender=model_cls, dispatch_uid=f"supabase_sync_delete_{model_cls.__name__}")

        self.stdout.write("Starting bulk sync to Supabase...")

        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }

        has_errors = False

        for model_cls, model_name in models_to_sync:
            table_name = MODEL_TABLE_MAP.get(model_name)
            if not table_name:
                continue

            records = model_cls.objects.all()
            count = records.count()
            self.stdout.write(f"Syncing model {model_name} ({count} records)...")

            if count == 0:
                self.stdout.write(self.style.SUCCESS(f"No records found for {model_name}. Skipped."))
                continue

            # Serialize all records
            payload = [serialize_instance(obj) for obj in records]

            # Post in bulk to Supabase
            upsert_url = f"{url.rstrip('/')}/rest/v1/{table_name}?on_conflict=id"
            try:
                r = requests.post(upsert_url, headers=headers, json=payload)
                if r.status_code in (200, 201, 204):
                    self.stdout.write(self.style.SUCCESS(f"  Successfully synced {count} records of {model_name} to table {table_name}."))
                elif r.status_code == 404:
                    self.stdout.write(self.style.ERROR(f"  Table '{table_name}' does not exist on Supabase!"))
                    has_errors = True
                else:
                    self.stdout.write(self.style.ERROR(f"  Failed to sync {model_name}: {r.status_code} - {r.text}"))
                    has_errors = True
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Exception occurred during sync of {model_name}: {e}"))
                has_errors = True

        if has_errors:
            self.stdout.write("\n" + "="*80)
            self.stdout.write(self.style.ERROR("SYNC FAILED OR COMPLETED WITH ERRORS."))
            self.stdout.write("It is likely that you need to create the required tables in your Supabase SQL editor.")
            self.stdout.write("Please log into your Supabase Dashboard, open the SQL Editor, and execute the SQL schema script below:")
            self.stdout.write("="*80)
            self.stdout.write(SQL_DDL_SCHEMA)
            self.stdout.write("="*80 + "\n")
        else:
            self.stdout.write(self.style.SUCCESS("\nAll models synced to Supabase successfully!"))
