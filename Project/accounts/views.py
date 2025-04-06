from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileUpdateForm
from .models import UserProfile, FriendRequest

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('/')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def user_data(request):
    user_profile = request.user.userprofile
    friend_requests = FriendRequest.objects.filter(to_user=request.user)
    search_query = request.GET.get('q', '')
    search_results = []
    if search_query:
        friends_ids = request.user.userprofile.friends.all().values_list('user__id', flat=True)
        search_results = User.objects.filter(username__icontains=search_query)\
            .exclude(id=request.user.id)\
            .exclude(id__in=friends_ids)
    context = {
        'user_profile': user_profile,
        'friend_requests': friend_requests,
        'search_query': search_query,
        'search_results': search_results,
    }
    return render(request, 'accounts/user_data.html', context)

def custom_logout(request):
    logout(request)
    return redirect('/')

@login_required
def update_profile(request):
    profile = request.user.userprofile
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.height = float(request.POST.get('height', 0)) if request.POST.get('height') else None
            profile.weight = float(request.POST.get('weight', 0)) if request.POST.get('weight') else None
            height_m = profile.height * 0.0254 if profile.height else 0
            weight_kg = profile.weight * 0.453592 if profile.weight else 0
            profile.bmi = weight_kg / (height_m ** 2) if height_m > 0 else None
            profile.save()
            goals = request.POST.getlist('goals')
            injuries = request.POST.getlist('injury_history')
            profile.goals.set(goals)
            profile.injury_history.set(injuries)
            return redirect('user_data')
    else:
        form = UserProfileUpdateForm(instance=profile)
    selected_goals = profile.goals.values_list('id', flat=True)
    selected_injuries = profile.injury_history.values_list('id', flat=True)
    return render(request, 'accounts/update_profile.html', {
        'form': form,
        'selected_goals': selected_goals,
        'selected_injuries': selected_injuries,
    })

@login_required
def send_friend_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    friend_request, created = FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
    if created:
        messages.success(request, "Friend request sent.")
    else:
        messages.info(request, "Friend request was already sent.")
    return redirect('user_data')

@login_required
def accept_friend_request(request, request_id):
    f_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    request.user.userprofile.friends.add(f_request.from_user.userprofile)
    f_request.delete()
    return redirect('user_data')

@login_required
def reject_friend_request(request, request_id):
    f_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    f_request.delete()
    return redirect('user_data')

@login_required
def remove_friend(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    request.user.userprofile.friends.remove(friend.userprofile)
    friend.userprofile.friends.remove(request.user.userprofile)
    return redirect('user_data')

@login_required
def friend_list(request):
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
    return render(request, 'accounts/user_data.html', {'search_results': results, 'search_query': query})

@login_required
def friend_data(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    if not request.user.userprofile.friends.filter(pk=friend.userprofile.pk).exists():
        messages.error(request, "You are not allowed to view this profile.")
        return redirect('user_data')
    return render(request, 'accounts/user_data.html', {'user_profile': friend.userprofile})
