from django.shortcuts import render, redirect
from .forms import UserRegistrationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from .models import UserProfile
from django.contrib.auth.decorators import login_required
from .forms import UserProfileUpdateForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import FriendRequest
# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import UserProfile, FriendRequest
from django.contrib import messages



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

@login_required
def user_data(request):
    # Retrieve the user's profile
    user_profile = request.user.userprofile

    # Retrieve additional friend management data if viewing own profile
    friend_requests = FriendRequest.objects.filter(to_user=request.user)
    search_query = request.GET.get('q', '')
    search_results = []
    if search_query:
        # Exclude yourself and those already friends
        friends_ids = request.user.userprofile.friends.all().values_list('user__id', flat=True)
        search_results = User.objects.filter(username__icontains=search_query)\
            .exclude(id=request.user.id)\
            .exclude(id__in=friends_ids)
    
    # Retrieve user data entries if needed (as before)
    user_data_entries = UserProfile.objects.filter(user=request.user).prefetch_related('goals')

    context = {
        'user_profile': user_profile,
        'user_data_entries': user_data_entries,
        'friend_requests': friend_requests,
        'search_query': search_query,
        'search_results': search_results,
    }
    return render(request, 'accounts/user_data.html', context)


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

@login_required
def profile_view(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)
    friend_requests = FriendRequest.objects.filter(to_user=request.user)

    # Handle friend search functionality
    search_query = request.GET.get('q', '')
    search_results = []
    if search_query:
        # Get IDs of users that are already friends with the logged-in user.
        friends_ids = request.user.userprofile.friends.all().values_list('user__id', flat=True)
        search_results = User.objects.filter(username__icontains=search_query)\
            .exclude(id=request.user.id)\
            .exclude(id__in=friends_ids)

    context = {
        'profile_user': profile_user,
        'friend_requests': friend_requests,
        'search_query': search_query,
        'search_results': search_results,
    }
    return render(request, 'accounts/user_data.html', context)


@login_required
def send_friend_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    friend_request, created = FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
    if created:
        messages.success(request, "Friend request sent.")
    else:
        messages.info(request, "Friend request was already sent.")
    # Redirect back to your own profile so you cannot access the target user's profile
    return redirect('user_data')




@login_required
def accept_friend_request(request, request_id):
    f_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    # Using request.user.profile instead of f_request.to_user.profile for clarity
    from_profile = f_request.from_user.userprofile
    to_profile = request.user.userprofile
    # For symmetrical ManyToMany fields, adding on one side is enough.
    to_profile.friends.add(from_profile)
    # Optionally, you could use to_profile.friends.add(from_profile)
    # Either call will automatically create the relationship in both directions.
    f_request.delete()
    return redirect('user_data')

@login_required
def reject_friend_request(request, request_id):
    # Reject and delete a friend request
    f_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    f_request.delete()
    return redirect('user_data')

@login_required
def remove_friend(request, user_id):
    # Remove a friend from the current user's friend list
    friend = get_object_or_404(User, id=user_id)
    request.user.userprofile.friends.remove(friend.userprofile)
    friend.userprofile.friends.remove(request.user.userprofile)
    return redirect('user_data')

@login_required
def friend_list(request):
    # View a list of your friends
    friends = request.user.userprofile.friends.all()
    return render(request, 'accounts/user_data.html', {'friends': friends})

@login_required
def friend_search(request):
    query = request.GET.get('q', '')
    results = []
    if query:
        friends_ids = request.user.userprofile.friends.all().values_list('user__id', flat=True)
        results = User.objects.filter(username__icontains=query)\
            .exclude(id=request.user.id)\
            .exclude(id__in=friends_ids)
    return render(request, 'accounts/user_data.html', {'search_results': results, 'query': query})

from django.contrib import messages

@login_required
def friend_data(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    # Check if the friend is actually in the current user's friends list
    if not request.user.userprofile.friends.filter(pk=friend.userprofile.pk).exists():
        messages.error(request, "You are not allowed to view this profile.")
        return redirect('accounts/user_data.html', user_id=request.user.id)
    # Render the user_data.html template using the friend's profile
    return render(request, 'accounts/user_data.html', {'user_profile': friend.userprofile})


