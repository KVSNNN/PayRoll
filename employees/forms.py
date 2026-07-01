from django import forms
from .models import Employee


class EmployeeForm(forms.ModelForm):
    """Form for creating and editing employee records."""

    class Meta:
        model = Employee
        fields = [
            'name', 'designation', 'department', 'date_of_joining',
            'monthly_salary', 'bank_account', 'phone', 'email', 'status'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'emp-name', 'placeholder': 'Full Name'
            }),
            'designation': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'emp-designation', 'placeholder': 'e.g., Software Engineer'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'emp-department', 'placeholder': 'e.g., IT, HR, Finance'
            }),
            'date_of_joining': forms.DateInput(attrs={
                'class': 'form-control', 'id': 'emp-doj', 'type': 'date'
            }),
            'monthly_salary': forms.NumberInput(attrs={
                'class': 'form-control', 'id': 'emp-salary', 'placeholder': '₹25,000',
                'step': '0.01', 'min': '0'
            }),
            'bank_account': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'emp-bank', 'placeholder': 'Bank Account Number'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 'id': 'emp-phone', 'placeholder': '+91 9876543210'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 'id': 'emp-email', 'placeholder': 'employee@company.com'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select', 'id': 'emp-status'
            }),
        }


class EmployeeSearchForm(forms.Form):
    """Search form for filtering employees."""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Search by ID, Name, Department...',
            'id': 'emp-search'
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Status'), ('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'emp-status-filter'})
    )
    department = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 'placeholder': 'Filter by Department',
            'id': 'emp-dept-filter'
        })
    )
