from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.decorators import super_admin_required
from .models import AuditLog


@login_required
@super_admin_required
def audit_log_list(request):
    """View audit logs (Super Admin only)."""
    logs = AuditLog.objects.all()[:200]

    # Filters
    action = request.GET.get('action', '')
    model = request.GET.get('model', '')
    user = request.GET.get('user', '')

    all_logs = AuditLog.objects.all()
    if action:
        all_logs = all_logs.filter(action=action)
    if model:
        all_logs = all_logs.filter(model_name__icontains=model)
    if user:
        all_logs = all_logs.filter(username__icontains=user)

    logs = all_logs[:200]

    return render(request, 'audit/audit_log.html', {
        'logs': logs,
        'selected_action': action,
        'selected_model': model,
        'selected_user': user,
    })
