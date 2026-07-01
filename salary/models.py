from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal, ROUND_HALF_UP


class SalaryRecord(models.Model):
    """Monthly salary record for an employee with auto-calculated fields."""

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('PAID', 'Paid'),
    ]

    employee = models.ForeignKey(
        'employees.Employee', on_delete=models.CASCADE,
        related_name='salary_records'
    )
    salary_month = models.CharField(
        max_length=20, help_text='e.g., June 2026'
    )
    month_year = models.DateField(
        help_text='First day of the salary month (for filtering)'
    )
    monthly_salary = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Monthly salary snapshot at time of entry'
    )
    total_working_days = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text='Total working days in the month'
    )
    present_days = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(31)],
        help_text='Number of days present'
    )

    # Auto-calculated fields
    absent_days = models.IntegerField(default=0, editable=False)
    salary_earned = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, editable=False
    )

    # Deductions
    deduction_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Total deduction amount'
    )
    deduction_remarks = models.TextField(
        blank=True, default='',
        help_text='Reason for deduction (e.g., Late attendance, Loan EMI)'
    )

    # Net salary
    net_salary = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, editable=False
    )

    # Payment details
    paid_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Amount paid in first payment'
    )
    payment_date = models.DateField(
        null=True, blank=True,
        help_text='Date of first payment'
    )

    # Balance tracking
    balance_salary = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, editable=False
    )
    balance_paid = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text='Balance amount paid later'
    )
    balance_paid_date = models.DateField(
        null=True, blank=True,
        help_text='Date when balance was paid'
    )

    # Totals
    total_salary_paid = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, editable=False
    )
    outstanding_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, editable=False
    )

    # Status and locking
    payment_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='PENDING', editable=False
    )
    is_completed = models.BooleanField(
        default=False,
        help_text='Lock record when checked — only Super Admin can unlock'
    )
    completed_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='completed_salaries'
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    remarks = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True,
        related_name='created_salary_records'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-month_year', 'employee__employee_id']
        unique_together = ['employee', 'month_year']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.salary_month}"

    def save(self, *args, **kwargs):
        """Auto-calculate all derived fields before saving."""
        self.calculate_fields()
        super().save(*args, **kwargs)

    def calculate_fields(self):
        """Calculate all auto-derived salary fields."""
        # Absent days
        self.absent_days = max(0, self.total_working_days - self.present_days)

        # Salary earned (proportional)
        if self.total_working_days > 0:
            daily_rate = self.monthly_salary / Decimal(self.total_working_days)
            self.salary_earned = (daily_rate * Decimal(self.present_days)).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        else:
            self.salary_earned = Decimal('0.00')

        # Net salary after deductions
        self.net_salary = max(Decimal('0.00'), self.salary_earned - self.deduction_amount)

        # Balance salary (after first payment)
        self.balance_salary = max(Decimal('0.00'), self.net_salary - self.paid_amount)

        # Total salary paid
        self.total_salary_paid = self.paid_amount + self.balance_paid

        # Outstanding balance
        self.outstanding_balance = max(
            Decimal('0.00'), self.net_salary - self.total_salary_paid
        )

        # Auto-determine payment status
        if self.outstanding_balance <= Decimal('0.00') and self.total_salary_paid > Decimal('0.00'):
            self.payment_status = 'PAID'
        elif self.total_salary_paid > Decimal('0.00'):
            self.payment_status = 'PARTIALLY_PAID'
        else:
            self.payment_status = 'PENDING'

    @property
    def status_color(self):
        """Return Bootstrap color class for payment status."""
        colors = {
            'PENDING': 'danger',
            'PARTIALLY_PAID': 'warning',
            'PAID': 'success',
        }
        return colors.get(self.payment_status, 'secondary')

    @property
    def status_icon(self):
        """Return icon for payment status."""
        icons = {
            'PENDING': 'bi-exclamation-circle-fill',
            'PARTIALLY_PAID': 'bi-clock-fill',
            'PAID': 'bi-check-circle-fill',
        }
        return icons.get(self.payment_status, 'bi-question-circle')

    def formatted_currency(self, amount):
        """Format amount in Indian Rupees."""
        return f'₹{amount:,.2f}'


class SalaryPayment(models.Model):
    """Individual payment transaction against a salary record."""

    PAYMENT_TYPE_CHOICES = [
        ('INITIAL', 'Initial Payment'),
        ('BALANCE', 'Balance Payment'),
    ]

    salary_record = models.ForeignKey(
        SalaryRecord, on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES)
    recorded_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True,
        related_name='recorded_payments'
    )
    remarks = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"₹{self.amount:,.2f} ({self.get_payment_type_display()}) - {self.payment_date}"
