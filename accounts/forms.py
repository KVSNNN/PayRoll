from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User


class LoginForm(AuthenticationForm):
    """Custom login form with Bootstrap styling."""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True,
            'id': 'login-username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'id': 'login-password',
        })
    )


class UserCreateForm(forms.ModelForm):
    """Form for Super Admin to create Cashier/Staff accounts."""
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'user-password1'}),
        min_length=8,
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'user-password2'}),
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'role', 'employee']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'id': 'user-username'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'user-firstname'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'id': 'user-lastname'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'id': 'user-email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'id': 'user-phone'}),
            'role': forms.Select(attrs={'class': 'form-select', 'id': 'user-role'}),
            'employee': forms.Select(attrs={'class': 'form-select', 'id': 'user-employee'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show CASHIER and STAFF roles (not SUPER_ADMIN)
        self.fields['role'].choices = [
            ('CASHIER', 'Cashier'),
            ('STAFF', 'Staff'),
        ]
        self.fields['employee'].required = False
        self.fields['employee'].queryset = self.fields['employee'].queryset.filter(status='ACTIVE')

    def clean(self):
        cleaned_data = super().clean()
        pw1 = cleaned_data.get('password1')
        pw2 = cleaned_data.get('password2')
        if pw1 and pw2 and pw1 != pw2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    """Form for Super Admin to update user accounts."""
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'role', 'employee', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].required = False
        self.fields['employee'].queryset = self.fields['employee'].queryset.filter(status='ACTIVE')


class ChangePasswordForm(forms.Form):
    """Form for users to change their own password."""
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=8,
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('new_password') != cleaned_data.get('confirm_password'):
            raise forms.ValidationError('New passwords do not match.')
        return cleaned_data
