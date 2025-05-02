import json
import requests
from datetime import date
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


def register(request):
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
    user_data_entries = UserProfile.objects.filter(user=request.user).prefetch_related(
        "goals"
    )
    exercises = UserAccExercise.objects.filter(user=request.user)
    exerciseDict = {}

    for x in exercises:
        print(x.name, x.weight)
        if x.name in exerciseDict:
            temp = exerciseDict.get(x.name)
            print(temp)
            print(type(temp), type(temp[0]), type(x.weight))
            temp.append(x.weight)
            print(temp)
            exerciseDict[x.name] = temp
        else:
            exerciseDict[x.name] = [x.weight]
    print(exerciseDict)
    exerciseDict = json.dumps(exerciseDict)
    print(exerciseDict, type(exerciseDict))

    # Get data for food log
    totalCarb, totalPro, totalFat = 0
    foodlist = FoodDatabase.objects.filter(
        user=request.user, datelog=date.today(), servings__gte=1
    )

    for food in foodlist:
        totalCarb += food.carbs * food.servings
        totalPro += food.protein * food.servings
        totalFat += food.fat * food.servings

    labels = [
        "Protein (" + str(totalPro) + "g)",
        "Fat (" + str(totalFat) + "g)",
        "Carbohydrates (" + str(totalCarb) + "g)",
    ]
    labelvalues = [totalPro * 4, totalFat * 9, totalCarb * 4]
    caltotal = labelvalues[0] + labelvalues[1] + labelvalues[2]
    print(labels, json.dumps(labelvalues))

    return render(
        request,
        "accounts/user_data.html",
        {
            "user_profile": user_profile,
            "user_data_entries": user_data_entries,
            "user_exercises": exerciseDict,
            "friend_requests": friend_requests,
            "search_query": search_query,
            "search_results": search_results,
            "foodlabels": json.dumps(labels),
            "foodlabelvalues": json.dumps(labelvalues),
            "foodlist": foodlist,
            "caltotal": caltotal,
        },
    )


def custom_logout(request):
    logout(request)
    return redirect("/")


@login_required
def update_profile(request):
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
        else:
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
    to_user = get_object_or_404(User, id=user_id)
    friend_request, created = FriendRequest.objects.get_or_create(
        from_user=request.user, to_user=to_user
    )
    if created:
        messages.success(request, "Friend request sent.")
    else:
        messages.info(request, "Friend request was already sent.")
    return redirect("user_data")


@login_required
def accept_friend_request(request, request_id):
    f_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    request.user.userprofile.friends.add(f_request.from_user.userprofile)
    f_request.delete()
    return redirect("user_data")


@login_required
def reject_friend_request(request, request_id):
    f_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    f_request.delete()
    return redirect("user_data")


@login_required
def remove_friend(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    request.user.userprofile.friends.remove(friend.userprofile)
    friend.userprofile.friends.remove(request.user.userprofile)
    return redirect("user_data")


@login_required
def friend_list(request):
    friends = request.user.userprofile.friends.all()
    return render(request, "accounts/user_data.html", {"friends": friends})


@login_required
def friend_search(request):
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
    friend = get_object_or_404(User, id=user_id)
    if not request.user.userprofile.friends.filter(pk=friend.userprofile.pk).exists():
        messages.error(request, "You are not allowed to view this profile.")
        return redirect("user_data")
    return render(
        request, "accounts/user_data.html", {"user_profile": friend.userprofile}
    )


def log_data(request):
    profile = request.user.userprofile
    exercisesdone = UserAccExercise.objects.filter(user=request.user)
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
                    "exercises": exercisesdone,
                    "flag": flag,
                },
            )

        elif "barcode" in request.POST:  # This is a foodlog update
            tosend = "https://cs4300-group2.tech/api/product/" + request.POST.get(
                "barcode"
            )
            response = requests.get(tosend)
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
        elif "sets" in request.POST:  # This is a exercise update
            print(len(request.POST))
            UserAccExercise.objects.create(
                user=request.user,
                name=request.POST.get("name"),
                sets=request.POST.get("sets", 0),
                reps=request.POST.get("reps", 0),
                weight=request.POST.get("weight", 0),
            )

        else:  # This is a weight update
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
                    "exercises": exercisesdone,
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
                "exercises": exercisesdone,
                "flag": flag,
            },
        )

    else:
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
                "exercises": exercisesdone,
                "flag": flag,
            },
        )
