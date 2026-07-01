from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model with role-based access control."""

    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('CASHIER', 'Cashier'),
        ('STAFF', 'Staff'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STAFF')
    phone = models.CharField(max_length=15, blank=True, null=True)
    employee = models.OneToOneField(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_account',
        help_text='Link to Employee record (for Staff users)'
    )
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_super_admin(self):
        return self.role == 'SUPER_ADMIN'

    @property
    def is_cashier(self):
        return self.role == 'CASHIER'

    @property
    def is_staff_role(self):
        return self.role == 'STAFF'

    def reset_login_attempts(self):
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['failed_login_attempts', 'locked_until'])

    def increment_login_attempts(self):
        from django.utils import timezone
        from django.conf import settings
        import datetime

        self.failed_login_attempts += 1
        if self.failed_login_attempts >= getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5):
            lockout_seconds = getattr(settings, 'LOGIN_LOCKOUT_DURATION', 900)
            self.locked_until = timezone.now() + datetime.timedelta(seconds=lockout_seconds)
        self.save(update_fields=['failed_login_attempts', 'locked_until'])

    @property
    def is_locked(self):
        from django.utils import timezone
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False
