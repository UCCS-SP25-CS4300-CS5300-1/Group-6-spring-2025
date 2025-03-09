from django.shortcuts import render, redirect
from .forms import UserRegistrationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from .models import UserData
from django.contrib.auth.decorators import login_required
from .forms import UserProfileUpdateForm

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in after registration
            return redirect('home')  # Redirect to home or another page after saving
    else:
        form = UserRegistrationForm()  # Create a new form instance for GET requests
    return render(request, 'accounts/register.html', {'form': form})  # Always return the form

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def user_data(request):
    if request.POST.get('bmi'):
        bmi = request.POST.get('bmi')
        fitness_level = request.POST.get('goals')
        UserData.objects.create(user=request.user, bmi=bmi, fitness_level=fitness_level, goals=goals)
        return redirect('user_data')
    user_data = UserData.objects.filter(user=request.user)
    return render(request, 'accounts/user_data.html', {'user_data': user_data})

@login_required  # Ensure the user is logged in
def update_profile(request):
    profile = request.user.userprofile  # Get the user's profile
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()  # Save the updated profile
            return redirect('home')  # Redirect to home or another page after saving
    else:
        form = UserProfileUpdateForm(instance=profile)  # Pre-fill the form with existing data
    return render(request, 'users/update_profile.html', {'form': form})