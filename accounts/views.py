from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserSignupForm

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
