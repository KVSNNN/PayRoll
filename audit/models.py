from django.db import models


class AuditLog(models.Model):
    """Comprehensive audit log tracking all system actions."""

    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOCK', 'Lock Record'),
        ('UNLOCK', 'Unlock Record'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
    ]

    user = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True,
        related_name='audit_logs'
    )
    username = models.CharField(max_length=150, help_text='Cached username')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50, help_text='e.g., Employee, SalaryRecord')
    record_id = models.IntegerField(null=True, blank=True)
    changes = models.JSONField(default=dict, blank=True, help_text='JSON of field changes')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['model_name', 'record_id']),
        ]

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.username} - {self.action} {self.model_name}"

    @property
    def action_color(self):
        colors = {
            'CREATE': 'success',
            'UPDATE': 'info',
            'DELETE': 'danger',
            'LOCK': 'warning',
            'UNLOCK': 'secondary',
            'LOGIN': 'primary',
            'LOGOUT': 'dark',
        }
        return colors.get(self.action, 'secondary')

    @property
    def action_icon(self):
        icons = {
            'CREATE': 'bi-plus-circle',
            'UPDATE': 'bi-pencil-square',
            'DELETE': 'bi-trash',
            'LOCK': 'bi-lock-fill',
            'UNLOCK': 'bi-unlock-fill',
            'LOGIN': 'bi-box-arrow-in-right',
            'LOGOUT': 'bi-box-arrow-left',
        }
        return icons.get(self.action, 'bi-circle')
