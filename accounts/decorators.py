from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden


def role_required(*roles):
    """Decorator that restricts view access to specific user roles."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.role not in roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('dashboard:home')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def super_admin_required(view_func):
    """Restrict access to Super Admin only."""
    return role_required('SUPER_ADMIN')(view_func)


def cashier_or_admin_required(view_func):
    """Allow access to Cashier and Super Admin."""
    return role_required('SUPER_ADMIN', 'CASHIER')(view_func)


def staff_only(view_func):
    """Restrict access to Staff only (for viewing own data)."""
    return role_required('STAFF')(view_func)
