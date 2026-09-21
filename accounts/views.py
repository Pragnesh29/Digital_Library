from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import UserSignupForm
from .models import CustomUser
from library.utils import log_action

def check_username_view(request):
    username = request.GET.get('username', '').strip()
    if not username:
        return JsonResponse({'available': False, 'message': ''})
    
    if len(username) < 3:
        return JsonResponse({'available': False, 'message': 'Username must be at least 3 characters long.'})
        
    exists = CustomUser.objects.filter(username__iexact=username).exists()
    if exists:
        return JsonResponse({'available': False, 'message': 'Username already taken! Please choose another.'})
    else:
        return JsonResponse({'available': True, 'message': 'Username is available!'})

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = UserSignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_approved = False  # Explicitly set to false (handled by model save but good to be explicit)
            user.save()
            messages.success(request, "Registration successful! Your account has been sent for admin approval.")
            log_action(None, "User Registered", f"New user '{user.username}' created and pending approval")
            return redirect('pending_approval')
    else:
        form = UserSignupForm()
    return render(request, 'accounts/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    form = None
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_approved:
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                    return redirect('home')
                else:
                    messages.error(request, "Your account is pending approval by the administration. You will be able to log in once approved.")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
        
    # Apply styling classes to input elements
    for field_name, field in form.fields.items():
        field.widget.attrs['class'] = 'form-control'
        field.widget.attrs['placeholder'] = f'Enter {field.label}'
        
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login')

def pending_approval_view(request):
    return render(request, 'accounts/pending_approval.html')

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in
            messages.success(request, 'Your password was successfully updated!')
            log_action(request.user, "Password Changed", "Changed own password")
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
        
    # Style form control
    for field_name, field in form.fields.items():
        field.widget.attrs['class'] = 'form-control'
        field.widget.attrs['placeholder'] = f'Enter {field.label}'
        
    return render(request, 'accounts/change_password.html', {'form': form})
