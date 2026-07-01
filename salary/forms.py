from django import forms
from .models import SalaryRecord
from employees.models import Employee
import datetime


MONTH_CHOICES = [
    ('', 'Select Month'),
    ('January', 'January'), ('February', 'February'), ('March', 'March'),
    ('April', 'April'), ('May', 'May'), ('June', 'June'),
    ('July', 'July'), ('August', 'August'), ('September', 'September'),
    ('October', 'October'), ('November', 'November'), ('December', 'December'),
]

YEAR_CHOICES = [(str(y), str(y)) for y in range(2020, 2035)]


class SalaryRecordForm(forms.ModelForm):
    """Form for creating and editing salary records."""

    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'salary-month'})
    )
    year = forms.ChoiceField(
        choices=[('', 'Select Year')] + YEAR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'salary-year'})
    )

    class Meta:
        model = SalaryRecord
        fields = [
            'employee', 'total_working_days', 'present_days',
            'deduction_amount', 'deduction_remarks',
            'paid_amount', 'payment_date', 'remarks'
        ]
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-select', 'id': 'salary-employee'
            }),
            'total_working_days': forms.NumberInput(attrs={
                'class': 'form-control', 'id': 'salary-working-days',
                'value': '30', 'min': '1', 'max': '31'
            }),
            'present_days': forms.NumberInput(attrs={
                'class': 'form-control', 'id': 'salary-present-days',
                'min': '0', 'max': '31'
            }),
            'deduction_amount': forms.NumberInput(attrs={
                'class': 'form-control', 'id': 'salary-deduction',
                'step': '0.01', 'min': '0', 'value': '0'
            }),
            'deduction_remarks': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'salary-deduction-remarks',
                'placeholder': 'e.g., Late attendance, Loan EMI'
            }),
            'paid_amount': forms.NumberInput(attrs={
                'class': 'form-control', 'id': 'salary-paid-amount',
                'step': '0.01', 'min': '0', 'value': '0'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control', 'id': 'salary-payment-date',
                'type': 'date'
            }),
            'remarks': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'salary-remarks',
                'placeholder': 'Additional remarks'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(status='ACTIVE')

        # Pre-fill month/year from instance
        if self.instance and self.instance.pk:
            if self.instance.month_year:
                self.fields['month'].initial = self.instance.month_year.strftime('%B')
                self.fields['year'].initial = str(self.instance.month_year.year)

    def clean(self):
        cleaned_data = super().clean()
        month = cleaned_data.get('month')
        year = cleaned_data.get('year')
        present = cleaned_data.get('present_days', 0)
        total = cleaned_data.get('total_working_days', 30)

        if not month or not year:
            raise forms.ValidationError('Please select month and year.')

        if present > total:
            raise forms.ValidationError('Present days cannot exceed total working days.')

        # Build salary_month and month_year
        month_names = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12,
        }
        month_num = month_names.get(month, 1)
        cleaned_data['salary_month'] = f'{month} {year}'
        cleaned_data['month_year'] = datetime.date(int(year), month_num, 1)

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.salary_month = self.cleaned_data['salary_month']
        instance.month_year = self.cleaned_data['month_year']

        # Snapshot the monthly salary from employee
        if not instance.monthly_salary:
            instance.monthly_salary = instance.employee.monthly_salary

        if commit:
            instance.save()
        return instance


class BalancePaymentForm(forms.Form):
    """Form for recording a balance payment."""
    balance_paid = forms.DecimalField(
        max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'id': 'balance-paid',
            'step': '0.01', 'min': '0.01'
        })
    )
    balance_paid_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'id': 'balance-paid-date',
            'type': 'date'
        })
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'id': 'balance-remarks',
            'placeholder': 'Payment remarks'
        })
    )


class SalarySearchForm(forms.Form):
    """Search form for salary records."""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Search by Employee ID or Name...',
            'id': 'salary-search'
        })
    )
    month = forms.ChoiceField(
        required=False,
        choices=[('', 'All Months')] + MONTH_CHOICES[1:],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'salary-month-filter'})
    )
    year = forms.ChoiceField(
        required=False,
        choices=[('', 'All Years')] + YEAR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'salary-year-filter'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Status'),
            ('PENDING', 'Pending'),
            ('PARTIALLY_PAID', 'Partially Paid'),
            ('PAID', 'Paid'),
        ],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'salary-status-filter'})
    )
