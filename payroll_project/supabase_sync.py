import logging
import threading
import requests
import json
from decimal import Decimal
from datetime import datetime, date
from django.conf import settings
from django.db.models.signals import post_save, post_delete

logger = logging.getLogger(__name__)

# Map Django model names to their Supabase table names
MODEL_TABLE_MAP = {
    'User': 'accounts_user',
    'Employee': 'employees_employee',
    'SalaryRecord': 'salary_salaryrecord',
    'SalaryPayment': 'salary_salarypayment',
    'AuditLog': 'audit_auditlog',
}


def run_in_background(target, *args, **kwargs):
    """Run a target function in a daemon thread."""
    thread = threading.Thread(target=target, args=args, kwargs=kwargs)
    thread.daemon = True
    thread.start()


def serialize_instance(instance):
    """Generically serialize a Django model instance to a JSON-serializable dictionary."""
    data = {}
    for field in instance._meta.fields:
        name = field.attname
        val = getattr(instance, name)
        
        if isinstance(val, Decimal):
            data[name] = float(val)
        elif isinstance(val, (datetime, date)):
            data[name] = val.isoformat()
        elif isinstance(val, (dict, list)):
            data[name] = val
        else:
            data[name] = val
            
    return data


def _send_sync_request(table_name, payload, is_deleted=False, record_id=None):
    """
    Perform the HTTP REST call to Supabase API.
    Executed in a background thread to prevent blocking main Django request flow.
    """
    url = getattr(settings, 'SUPABASE_URL', None)
    key = getattr(settings, 'SUPABASE_ANON_KEY', None)
    if not url or not key:
        logger.warning("Supabase URL or Key not configured. Skipping sync.")
        return

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    try:
        if is_deleted:
            delete_url = f"{url.rstrip('/')}/rest/v1/{table_name}?id=eq.{record_id}"
            r = requests.delete(delete_url, headers=headers)
            if r.status_code not in (200, 204):
                logger.error(f"Failed to delete record {record_id} in {table_name}: {r.status_code} - {r.text}")
        else:
            # PostgREST upsert: POST with Prefer: resolution=merge-duplicates
            upsert_url = f"{url.rstrip('/')}/rest/v1/{table_name}?on_conflict=id"
            headers["Prefer"] = "resolution=merge-duplicates"
            r = requests.post(upsert_url, headers=headers, json=[payload])
            if r.status_code not in (200, 201):
                logger.error(f"Failed to upsert record in {table_name}: {r.status_code} - {r.text}")
    except Exception as e:
        logger.exception(f"Exception during Supabase sync for {table_name}: {e}")


def handle_save(sender, instance, **kwargs):
    """Signal handler for post_save."""
    model_name = instance._meta.object_name
    table_name = MODEL_TABLE_MAP.get(model_name)
    if not table_name:
        return
        
    payload = serialize_instance(instance)
    run_in_background(_send_sync_request, table_name, payload, is_deleted=False)


def handle_delete(sender, instance, **kwargs):
    """Signal handler for post_delete."""
    model_name = instance._meta.object_name
    table_name = MODEL_TABLE_MAP.get(model_name)
    if not table_name:
        return
        
    run_in_background(_send_sync_request, table_name, None, is_deleted=True, record_id=instance.pk)


def register_signals():
    """Register signal handlers for configured Django models."""
    from django.conf import settings
    
    # Bypass signal registration if we are directly using PostgreSQL (e.g. Supabase)
    db_engine = settings.DATABASES.get('default', {}).get('ENGINE', '')
    if 'postgresql' in db_engine:
        logger.info("Direct PostgreSQL database detected. Skipping REST sync signal registration.")
        return

    from django.contrib.auth import get_user_model
    from employees.models import Employee
    from salary.models import SalaryRecord, SalaryPayment
    from audit.models import AuditLog

    User = get_user_model()
    models_to_sync = [User, Employee, SalaryRecord, SalaryPayment, AuditLog]


    for model in models_to_sync:
        post_save.connect(handle_save, sender=model, dispatch_uid=f"supabase_sync_save_{model.__name__}")
        post_delete.connect(handle_delete, sender=model, dispatch_uid=f"supabase_sync_delete_{model.__name__}")
        
    logger.info("Supabase sync signal handlers registered successfully.")
