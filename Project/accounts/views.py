from django.shortcuts import render, redirect
from .forms import UserRegistrationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .models import UserProfile, UserAccExercise
from django.contrib.auth.decorators import login_required
from .forms import UserProfileUpdateForm, UserLogDataFormWeight, UserLogDataFormExercise
import json


def register(request):
    print("Register view called")
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in after registration
            return redirect('/')  # Redirect to home or another page after saving
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
                return redirect('/')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def user_data(request):
    # Retrieve the user's profile
    user_profile = request.user.userprofile
    # Retrieve all user data entries for the logged-in user
    user_data_entries = UserProfile.objects.filter(user=request.user).prefetch_related('goals')  # Prefetch related goals for efficiency
    exercises = UserAccExercise.objects.filter(user=request.user)
    exerciseDict = {}
    for x in exercises:
        if x.name in exerciseDict:
            temp = exerciseDict.get(x.name)
            exerciseDict[x.name] = temp.append(x.weight)
        else:
            exerciseDict[x.name] = [x.weight]
    print(exerciseDict)
    return render(request, 'accounts/user_data.html', {
        'user_profile': user_profile,
        'user_data_entries': user_data_entries,
    })

def custom_logout(request):
    logout(request)  # This will terminate the user's session
    return redirect('/')  # Redirect to the home page or any other page

@login_required  # Ensure the user is logged in
def update_profile(request):
    profile = request.user.userprofile  # Get the user's profile
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=profile)
        print(request.POST)  # Print the submitted data
        if form.is_valid():
            profile = form.save(commit=False)  # Save the form but don't commit yet
            
            profile.height = float(request.POST.get('height', 0)) if request.POST.get('height') else None
            profile.weight = float(request.POST.get('weight', 0)) if request.POST.get('weight') else None
            profile.weight_history = request.POST.get('weight', 0) if request.POST.get('weight') else None
            profile.weight_history = json.dumps([int(profile.weight_history)])
            print(profile.weight_history)
            # Calculate BMI
            height_m = profile.height * 0.0254 if profile.height else 0  # Convert height from inches to meters
            weight_kg = profile.weight * 0.453592 if profile.weight else 0  # Convert weight from pounds to kg
            
            if height_m > 0:  # Prevent division by zero
                profile.bmi = weight_kg / (height_m ** 2)
            else:
                profile.bmi = None  # Handle case where height is zero
            
            # Save the updated profile
            profile.save()  
            
            # Handle goals and injuries
            goals = request.POST.getlist('goals')  # Get selected goals from the form
            injuries = request.POST.getlist('injury_history')  # Get selected injuries from the form
            
            # Update the ManyToMany fields
            profile.goals.set(goals)  # Update the user's goals
            profile.injury_history.set(injuries)  # Update the user's injury history
            
            return redirect('/accounts/user_data/')  # Redirect to home or another page after saving
        else:
            print(form.errors)  # Print any validation errors
    else:
        form = UserProfileUpdateForm(instance=profile)  # Pre-fill the form with existing data

    # Prepare a list of selected goal IDs and injury IDs
    selected_goals = profile.goals.values_list('id', flat=True)
    selected_injuries = profile.injury_history.values_list('id', flat=True)

    return render(request, 'accounts/update_profile.html', {
        'form': form,
        'selected_goals': selected_goals,
        'selected_injuries': selected_injuries,
    })

def log_data(request):

    profile = request.user.userprofile
    exercisesdone = UserAccExercise.objects.filter(user=request.user)
    print(profile)
    print(exercisesdone[0].name)
    if request.method == 'POST':
        #This will update the weight_history attribute as a json object so i can be used in the charts.
        if( len(request.POST) < 5 ): #This is a weight update
            newweight = int(request.POST.get('weight', 0))
            oldweight = json.loads(profile.weight_history)
            oldweight.append(newweight)
            toupdate = json.dumps(oldweight)
            UserProfile.objects.filter(user=request.user).update(weight_history=toupdate)
        else: #This is a exercise update
            print(len(request.POST))
            UserAccExercise.objects.create(user=request.user,name=request.POST.get('name'),sets=request.POST.get('sets', 0),reps=request.POST.get('reps', 0),weight=request.POST.get('weight', 0))
        formweight = UserLogDataFormWeight()
        formexercise = UserLogDataFormExercise()
        return render(request, 'accounts/log_data.html', {'form':formweight, 'formtwo':formexercise, 'exercises':exercisesdone})
    else:
        formweight = UserLogDataFormWeight()
        formexercise = UserLogDataFormExercise()
        return render(request, 'accounts/log_data.html', {'form':formweight, 'formtwo':formexercise, 'exercises':exercisesdone})