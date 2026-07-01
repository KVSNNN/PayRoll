from django.db import models


class Employee(models.Model):
    """Employee master record with all personal and employment details."""

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    ]

    employee_id = models.CharField(
        max_length=20, unique=True, editable=False,
        help_text='Auto-generated Employee ID (e.g., EMP001)'
    )
    name = models.CharField(max_length=200, help_text='Full name of the employee')
    designation = models.CharField(max_length=100, help_text='Job title/designation')
    department = models.CharField(max_length=100, help_text='Department name')
    date_of_joining = models.DateField(help_text='Date of joining the company')
    monthly_salary = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Monthly salary in INR'
    )
    bank_account = models.CharField(
        max_length=30, blank=True, null=True,
        help_text='Bank account number'
    )
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True,
        related_name='created_employees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['employee_id']

    def __str__(self):
        return f"{self.employee_id} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.employee_id:
            self.employee_id = self.generate_employee_id()
        super().save(*args, **kwargs)

    @classmethod
    def generate_employee_id(cls):
        """Generate the next Employee ID in sequence: EMP001, EMP002, etc."""
        last_employee = cls.objects.order_by('-id').first()
        if last_employee and last_employee.employee_id.startswith('EMP'):
            try:
                last_num = int(last_employee.employee_id[3:])
                return f'EMP{last_num + 1:03d}'
            except ValueError:
                pass
        return 'EMP001'

    @property
    def formatted_salary(self):
        """Return salary formatted in Indian Rupees."""
        return f'₹{self.monthly_salary:,.2f}'
