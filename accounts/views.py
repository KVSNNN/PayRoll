from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q

from .models import User
from .forms import LoginForm, UserCreateForm, UserUpdateForm, ChangePasswordForm
from .decorators import super_admin_required
from audit.utils import log_action


def login_view(request):
    """Handle user login with brute-force protection."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        username = request.POST.get('username', '')

        # Check if user is locked
        try:
            user = User.objects.get(username=username)
            if user.is_locked:
                remaining = (user.locked_until - timezone.now()).seconds // 60
                messages.error(
                    request,
                    f'Account is locked. Try again in {remaining + 1} minutes.'
                )
                return render(request, 'accounts/login.html', {'form': form})
        except User.DoesNotExist:
            pass

        if form.is_valid():
            user = form.get_user()
            user.reset_login_attempts()
            login(request, user)
            log_action(request, 'LOGIN', 'User', user.pk, {})
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('dashboard:home')
        else:
            # Increment failed attempts
            try:
                user = User.objects.get(username=username)
                user.increment_login_attempts()
                if user.is_locked:
                    messages.error(request, 'Too many failed attempts. Account locked for 15 minutes.')
                else:
                    remaining = 5 - user.failed_login_attempts
                    messages.error(request, f'Invalid credentials. {remaining} attempts remaining.')
            except User.DoesNotExist:
                messages.error(request, 'Invalid credentials.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Handle user logout."""
    log_action(request, 'LOGOUT', 'User', request.user.pk, {})
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
@super_admin_required
def user_list(request):
    """List all user accounts (Super Admin only)."""
    users = User.objects.all().order_by('-created_at')
    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            models.Q(username__icontains=search) |
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search) |
            models.Q(email__icontains=search)
        )
    return render(request, 'accounts/user_list.html', {'users': users, 'search': search})


@login_required
@super_admin_required
def user_create(request):
    """Create a new user account (Super Admin only)."""
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_action(request, 'CREATE', 'User', user.pk, {
                'username': user.username,
                'role': user.role,
            })
            messages.success(request, f'User "{user.username}" created successfully.')
            return redirect('accounts:user_list')
    else:
        form = UserCreateForm()
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Create User'})


@login_required
@super_admin_required
def user_edit(request, pk):
    """Edit a user account (Super Admin only)."""
    user = get_object_or_404(User, pk=pk)
    old_data = {'role': user.role, 'is_active': user.is_active}

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            updated_user = form.save()
            changes = {}
            if old_data['role'] != updated_user.role:
                changes['role'] = {'old': old_data['role'], 'new': updated_user.role}
            if old_data['is_active'] != updated_user.is_active:
                changes['is_active'] = {'old': old_data['is_active'], 'new': updated_user.is_active}
            log_action(request, 'UPDATE', 'User', updated_user.pk, changes)
            messages.success(request, f'User "{updated_user.username}" updated successfully.')
            return redirect('accounts:user_list')
    else:
        form = UserUpdateForm(instance=user)
    return render(request, 'accounts/user_form.html', {
        'form': form, 'title': 'Edit User', 'edit_user': user
    })


@login_required
@super_admin_required
def user_toggle_active(request, pk):
    """Activate/Deactivate a user (Super Admin only)."""
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('accounts:user_list')

    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    status = 'activated' if user.is_active else 'deactivated'
    log_action(request, 'UPDATE', 'User', user.pk, {
        'is_active': {'old': not user.is_active, 'new': user.is_active}
    })
    messages.success(request, f'User "{user.username}" has been {status}.')
    return redirect('accounts:user_list')


@login_required
def change_password(request):
    """Allow any user to change their own password."""
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            if not request.user.check_password(form.cleaned_data['current_password']):
                messages.error(request, 'Current password is incorrect.')
            else:
                request.user.set_password(form.cleaned_data['new_password'])
                request.user.save()
                update_session_auth_hash(request, request.user)
                log_action(request, 'UPDATE', 'User', request.user.pk, {'password': 'changed'})
                messages.success(request, 'Password changed successfully.')
                return redirect('dashboard:home')
    else:
        form = ChangePasswordForm()
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
@super_admin_required
def user_unlock(request, pk):
    """Unlock a locked user account (Super Admin only)."""
    user = get_object_or_404(User, pk=pk)
    user.reset_login_attempts()
    log_action(request, 'UNLOCK', 'User', user.pk, {})
    messages.success(request, f'User "{user.username}" has been unlocked.')
    return redirect('accounts:user_list')
