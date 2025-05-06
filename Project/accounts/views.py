"""
Views for the accounts module.

This module contains the views for user authentication and profile management,
including registration, login, logout, and editing user profiles. It handles
the request/response cycle for these operations and interacts with the models 
to perform necessary actions like creating new users or updating user information.

Each view function is responsible for rendering the appropriate templates 
and returning the corresponding HTTP responses.
"""
from datetime import date
import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import (
    UserRegistrationForm,
    UserProfileUpdateForm,
    UserLogDataFormWeight,
    UserLogDataFormExercise,
    UserLogDataFormFood,
    UserLogDataFormFoodData,
)
from .models import UserProfile, FriendRequest, UserAccExercise, FoodDatabase

# pylint: disable=no-member
def register(request):
    """
    Handle user registration. If the request method is POST, validate and save the form 
    data, authenticate the user, and log them in. Redirect to the home page after a 
    successful registration.

    Args:
        request: The HTTP request object.

    Returns:
        Rendered registration page with the registration form.
    """
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")
    else:
        form = UserRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def user_login(request):
    """
    Handle user login. If the request method is POST, authenticate the user using the provided
    username and password. If successful, log the user in and redirect to the home page.

    Args:
        request: The HTTP request object.

    Returns:
        Rendered login page with the authentication form.
    """
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect("/")
    else:
        form = AuthenticationForm()
    return render(request, "accounts/login.html", {"form": form})


@login_required
def user_data(request):
    """
    Display user data including the user's profile, friend requests, search results for friends,
    and logs of exercises and food entries. This function handles retrieval and rendering of
    various data related to the logged-in user.

    Args:
        request: The HTTP request object.

    Returns:
        Rendered user data page with user-related information such as exercises, food logs, and
        friends.
    """
    # Retrieve the user's profile
    user_profile = request.user.userprofile

    # Friend management
    friend_requests = FriendRequest.objects.filter(to_user=request.user)
    search_query = request.GET.get("q", "")
    search_results = []
    if search_query:
        friends_ids = request.user.userprofile.friends.all().values_list(
            "user__id", flat=True
        )
        search_results = (
            User.objects.filter(username__icontains=search_query)
            .exclude(id=request.user.id)
            .exclude(id__in=friends_ids)
        )

    # Retrieve all user data entries for the logged-in user
    # Prefetch related goals for efficiency
    exercise_dict = {}

    for x in UserAccExercise.objects.filter(user=request.user):
        print(x.name, x.weight)
        if x.name in exercise_dict:
            temp = exercise_dict.get(x.name)
            print(temp)
            print(type(temp), type(temp[0]), type(x.weight))
            temp.append(x.weight)
            print(temp)
            exercise_dict[x.name] = temp
        else:
            exercise_dict[x.name] = [x.weight]
    exercise_dict = json.dumps(exercise_dict)

    # Get data for food log
    total_carb = total_pro = total_fat = 0

    for food in FoodDatabase.objects.filter(
        user=request.user, datelog=date.today(), servings__gte=1):
        total_carb += food.carbs * food.servings
        total_pro += food.protein * food.servings
        total_fat += food.fat * food.servings

    labels = [
        "Protein (" + str(total_pro) + "g)",
        "Fat (" + str(total_fat) + "g)",
        "Carbohydrates (" + str(total_carb) + "g)",
    ]
    labelvalues = [total_pro * 4, total_fat * 9, total_carb * 4]

    return render(
        request,
        "accounts/user_data.html",
        {
            "user_profile": user_profile,
            "user_data_entries": UserProfile.objects.filter(user=request.user).prefetch_related(
                                     "goals"),
            "user_exercises": exercise_dict,
            "friend_requests": friend_requests,
            "search_query": search_query,
            "search_results": search_results,
            "foodlabels": json.dumps(labels),
            "foodlabelvalues": json.dumps(labelvalues),
            "foodlist": FoodDatabase.objects.filter(
                                     user=request.user,
                                     datelog=date.today(),
                                     servings__gte=1
                                  ),
            "caltotal": labelvalues[0] + labelvalues[1] + labelvalues[2],
        },
    )


def custom_logout(request):
    """
    Log the user out and redirect to the home page.

    Args:
        request: The HTTP request object.

    Returns:
        Redirect to the home page after logging out.
    """
    logout(request)
    return redirect("/")


@login_required
def update_profile(request):
    """
    Update the user's profile information, including height, weight, BMI, goals, and injury 
    history. If the form is valid, save the updated profile data and redirect the user to
    the user data page.

    Args:
        request: The HTTP request object.

    Returns:
        Rendered profile update page with the user's current profile data and a form to
        update the profile.
    """
    profile = request.user.userprofile
    if request.method == "POST":
        form = UserProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.height = (
                float(request.POST.get("height", 0))
                if request.POST.get("height")
                else None
            )
            profile.weight = (
                float(request.POST.get("weight", 0))
                if request.POST.get("weight")
                else None
            )
            profile.weight_history = (
                request.POST.get("weight", 0) if request.POST.get("weight") else None
            )
            profile.weight_history = json.dumps([int(profile.weight_history)])

            # Calculate BMI
            # Convert height from inches to meters
            height_m = profile.height * 0.0254 if profile.height else 0
            # Convert weight from pounds to kg
            weight_kg = profile.weight * 0.453592 if profile.weight else 0

            if height_m > 0:  # Prevent division by zero
                profile.bmi = weight_kg / (height_m**2)
            else:
                profile.bmi = None  # Handle case where height is zero
            # Save the updated profile
            profile.save()
            # Handle goals and injuries
            # Get selected goals from the form
            goals = request.POST.getlist("goals")
            # Get selected injuries from the form
            injuries = request.POST.getlist("injury_history")
            # Update the ManyToMany fields
            # Update the user's goals
            profile.goals.set(goals)
            # Update the user's injury history
            profile.injury_history.set(injuries)
            # Redirect to home or another page after saving
            return redirect("/accounts/user_data/")
        print(form.errors)  # Print any validation errors
    else:
        form = UserProfileUpdateForm(instance=profile)

    selected_goals = profile.goals.values_list("id", flat=True)
    selected_injuries = profile.injury_history.values_list("id", flat=True)
    return render(
        request,
        "accounts/update_profile.html",
        {
            "form": form,
            "selected_goals": selected_goals,
            "selected_injuries": selected_injuries,
        },
    )


@login_required
def send_friend_request(request, user_id):
    """
    Send a friend request to another user. If a request already exists, inform the
    user. Redirect to the user data page after sending the request.

    Args:
        request: The HTTP request object.
        user_id: The ID of the user to whom the friend request is sent.

    Returns:
        Redirect to the user data page with a success or info message.
    """
    to_user = get_object_or_404(User, id=user_id)
    _, created = FriendRequest.objects.get_or_create(
        from_user=request.user, to_user=to_user
    )
    if created:
        messages.success(request, "Friend request sent.")
    else:
        messages.info(request, "Friend request was already sent.")
    return redirect("user_data")


@login_required
def accept_friend_request(request, request_id):
    """
    Accept a pending friend request, add the sender to the user's friend list, and 
    delete the request. Redirect to the user data page after accepting the request.

    Args:
        request: The HTTP request object.
        request_id: The ID of the friend request to accept.

    Returns:
        Redirect to the user data page after accepting the request.
    """
    f_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    request.user.userprofile.friends.add(f_request.from_user.userprofile)
    f_request.delete()
    return redirect("user_data")


@login_required
def reject_friend_request(request, request_id):
    """
    Reject a pending friend request by deleting it. Redirect to the user data page after
    rejecting the request.

    Args:
        request: The HTTP request object.
        request_id: The ID of the friend request to reject.

    Returns:
        Redirect to the user data page after rejecting the request.
    """
    f_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    f_request.delete()
    return redirect("user_data")


@login_required
def remove_friend(request, user_id):
    """
    Remove a friend from the user's friend list. This will also remove the user from the
    friend's list. Redirect to the user data page after removing the friend.

    Args:
        request: The HTTP request object.
        user_id: The ID of the user to be removed from the friend list.

    Returns:
        Redirect to the user data page after removing the friend.
    """
    friend = get_object_or_404(User, id=user_id)
    request.user.userprofile.friends.remove(friend.userprofile)
    friend.userprofile.friends.remove(request.user.userprofile)
    return redirect("user_data")


@login_required
def friend_list(request):
    """
    Display a list of the user's friends.

    Args:
        request: The HTTP request object.

    Returns:
        Rendered user data page with the user's friend list.
    """
    friends = request.user.userprofile.friends.all()
    return render(request, "accounts/user_data.html", {"friends": friends})


@login_required
def friend_search(request):
    """
    Search for users by username, excluding the current user and their existing friends. The
    search results are displayed on the user data page.

    Args:
        request: The HTTP request object.

    Returns:
        Rendered user data page with search results for friends.
    """
    query = request.GET.get("q", "")
    results = []
    if query:
        friends_ids = request.user.userprofile.friends.all().values_list(
            "user__id", flat=True
        )
        results = (
            User.objects.filter(username__icontains=query)
            .exclude(id=request.user.id)
            .exclude(id__in=friends_ids)
        )
    return render(
        request,
        "accounts/user_data.html",
        {"search_results": results, "search_query": query},
    )


@login_required
def friend_data(request, user_id):
    """
    Display detailed data for a specific friend, if they are in the user's friend list.

    Args:
        request: The HTTP request object.
        user_id: The ID of the friend whose data to display.

    Returns:
        Rendered user data page with the friend's information.
    """
    friend = get_object_or_404(User, id=user_id)
    if not request.user.userprofile.friends.filter(pk=friend.userprofile.pk).exists():
        messages.error(request, "You are not allowed to view this profile.")
        return redirect("user_data")
    return render(
        request, "accounts/user_data.html", {"user_profile": friend.userprofile}
    )


def log_data(request):
    """
    Handle logging POSTs for user weight, food, and exercise entries, and render
    the log_data page with the appropriate forms and data.

    - `servings` → add a food entry and immediately render the forms
    - `barcode`  → fetch nutrition info, prefill the food form, set flag
    - `sets`     → create an exercise entry
    - otherwise → append a new weight entry

    Finally, if `flag` is set it renders the food‐prefill form; otherwise it
    renders the default empty forms.
    """
    profile = request.user.userprofile
    #exercisesdone = UserAccExercise.objects.filter(user=request.user)
    foodinfo = None
    formfooddata = None
    flag = False
    print(profile)

    if request.method == "POST":
        # This will update the weight_history attribute as a json object so it
        # can be used in the charts.
        if "servings" in request.POST:
            FoodDatabase.objects.create(
                user=request.user,
                barcode=request.POST.get("barcode"),
                name=request.POST.get("name"),
                carbs=float(request.POST.get("carbs")),
                protein=float(request.POST.get("protein")),
                fat=float(request.POST.get("fat")),
                servings=float(request.POST.get("servings")),
            )

            formweight = UserLogDataFormWeight()
            formexercise = UserLogDataFormExercise()
            formfood = UserLogDataFormFood()
            return render(
                request,
                "accounts/log_data.html",
                {
                    "form": formweight,
                    "formtwo": formexercise,
                    "formthree": formfood,
                    "exercises": UserAccExercise.objects.filter(user=request.user),
                    "flag": flag,
                },
            )

        if "barcode" in request.POST:  # This is a foodlog update
            tosend = "https://cs4300-group2.tech/api/product/" + request.POST.get(
                "barcode"
            )
            response = requests.get(tosend, timeout=360)
            response = response.content
            response = response.decode("utf-8")
            response = json.loads(response)
            data = json.loads(response["nutrition_data"])

            foodinfo = [
                "Barcode: " + response["barcode"],
                "Name: " + response["name"],
                "Carbohydrates: " + str(data["carbohydrates"]),
                "Protein: " + str(data["proteins"]),
                "Fat: " + str(data["fat"]),
            ]

            formprefill = {
                "barcode": response["barcode"],
                "name": response["name"],
                "carbs": str(data["carbohydrates"]),
                "protein": str(data["proteins"]),
                "fat": str(data["fat"]),
            }

            formfooddata = UserLogDataFormFoodData(initial=formprefill)
            flag = True

            # need to making database and new modal to display food data and allow user
            # to update their food log
        if "sets" in request.POST:  # This is a exercise update
            print(len(request.POST))
            UserAccExercise.objects.create(
                user=request.user,
                name=request.POST.get("name"),
                sets=request.POST.get("sets", 0),
                reps=request.POST.get("reps", 0),
                weight=request.POST.get("weight", 0),
            )

        if (
            "servings" not in request.POST
            and "barcode" not in request.POST
            and "sets" not in request.POST):   # This is a weight update

            newweight = int(request.POST.get("weight", 0))
            oldweight = json.loads(profile.weight_history)
            oldweight.append(newweight)
            toupdate = json.dumps(oldweight)
            UserProfile.objects.filter(user=request.user).update(
                weight_history=toupdate
            )

        if flag:
            formweight = UserLogDataFormWeight()
            formexercise = UserLogDataFormExercise()
            formfood = UserLogDataFormFood()
            return render(
                request,
                "accounts/log_data.html",
                {
                    "form": formweight,
                    "formtwo": formexercise,
                    "formthree": formfood,
                    "exercises": UserAccExercise.objects.filter(user=request.user),
                    "flag": flag,
                    "foodinfo": foodinfo,
                    "formfour": formfooddata,
                },
            )

        formweight = UserLogDataFormWeight()
        formexercise = UserLogDataFormExercise()
        formfood = UserLogDataFormFood()
        return render(
            request,
            "accounts/log_data.html",
            {
                "form": formweight,
                "formtwo": formexercise,
                "formthree": formfood,
                "exercises": UserAccExercise.objects.filter(user=request.user),
                "flag": flag,
            },
        )

    formweight = UserLogDataFormWeight()
    formexercise = UserLogDataFormExercise()
    formfood = UserLogDataFormFood()
    return render(
        request,
        "accounts/log_data.html",
        {
            "form": formweight,
            "formtwo": formexercise,
            "formthree": formfood,
            "exercises": UserAccExercise.objects.filter(user=request.user),
            "flag": flag,
        },
    )
# pylint: enable=no-member
