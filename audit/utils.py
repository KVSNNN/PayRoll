from .models import AuditLog
from .middleware import get_current_ip, get_current_user_agent


def log_action(request, action, model_name, record_id, changes=None):
    """
    Create an audit log entry.

    Args:
        request: The HTTP request object
        action: The action type (CREATE, UPDATE, DELETE, LOCK, UNLOCK, LOGIN, LOGOUT)
        model_name: Name of the model being acted upon
        record_id: ID of the record
        changes: Dict of field changes {field: {old: x, new: y}}
    """
    if changes is None:
        changes = {}

    try:
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            username=request.user.username if request.user.is_authenticated else 'anonymous',
            action=action,
            model_name=model_name,
            record_id=record_id,
            changes=changes,
            ip_address=get_current_ip(),
            user_agent=get_current_user_agent(),
        )
    except Exception:
        # Don't let audit logging failures break the application
        pass
