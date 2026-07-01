from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'username', 'action', 'model_name', 'record_id', 'ip_address']
    list_filter = ['action', 'model_name']
    search_fields = ['username', 'model_name']
    readonly_fields = ['user', 'username', 'action', 'model_name', 'record_id',
                       'changes', 'ip_address', 'user_agent', 'timestamp']
