from django.shortcuts import render, get_object_or_404
from accounts.models import UserProfile
from .ai import ai_model  # Import the AI model instance
from goals.models import UserExercise, WorkoutLog, Exercise, Goal
from django.http import JsonResponse, HttpResponse
import datetime
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import timedelta
import requests
import os
from django.conf import settings
from .ai import ai_model


def generate_workout(request):
    context = {}

    if request.user.is_authenticated:
        try:
            profile = request.user.userprofile
            context['fitness_level'] = profile.fitness_level or ""
            context['goals'] = ", ".join(goal.name for goal in profile.goals.all())
            context['injuries'] = ", ".join(injury.name for injury in profile.injury_history.all())
        except UserProfile.DoesNotExist:
            context['fitness_level'] = ""
            context['goals'] = ""
            context['injuries'] = ""

    if request.method == "POST":
        user_info_text = request.POST.get("user_input", "").strip()
        print("User Info Text submitted:", user_info_text)
        template_path = os.path.join(settings.BASE_DIR, 'home', 'workout_template.txt')
        try:
            with open(template_path, "r", encoding="utf-8") as file:
                prompt_template = file.read()
        except Exception as e:
            return HttpResponse(f"Error reading prompt template: {e}", status=500)

        prompt = prompt_template.format(user_info=user_info_text)

        try:
            ai_response = ai_model.get_response(prompt)
        except Exception as e:
            ai_response = f"Error generating response: {e}"
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return HttpResponse(ai_response, content_type="text/plain")
        context["output"] = ai_response

    return render(request, "generate_workout.html", context)

def index(request):
    """
    Simple view to render the index page.
    Also logs the number of goals found in the user's profile for debugging.
    """
    goals = []
    if request.user.is_authenticated:
        try:
            user_profile = request.user.userprofile
            goals = user_profile.goals.all()
            print("Goals found:", goals.count())
        except UserProfile.DoesNotExist:
            print("UserProfile does not exist for:", request.user)
    return render(request, 'index.html', {'goals': goals})

@login_required
def calendar_view(request):
    # POST: toggle a workout occurrence
    if request.method == 'POST':
        workout_id    = request.POST.get('workout_id')
        date_str      = request.POST.get('date_completed')  # "YYYY-MM-DD"
        completed     = request.POST.get('completed') == 'true'

        exercise = get_object_or_404(UserExercise, id=workout_id, user=request.user)

        if completed:
            # mark done (create if missing)
            WorkoutLog.objects.get_or_create(
                user=request.user,
                exercise=exercise,
                date_completed=date_str
            )
        else:
            # unmark (delete the log for that date)
            WorkoutLog.objects.filter(
                user=request.user,
                exercise=exercise,
                date_completed=date_str
            ).delete()

        return JsonResponse({'status': 'success', 'workout_id': workout_id, 'date': date_str, 'completed': completed})

    warm_ups = []# create empty list to store warm ups
    try: #use a try except for requests from the API
        # call the API to get a JSON response listing the exercises
        today = timezone.now().date()
        has_workout_today = UserExercise.objects.filter(user = request.user, start_date_lte = today).filter(end_date_gte = today).filter(recurring_day = today.weekday()).exists()
        if has_workout_today:     
            response = requests.get("https://api.api-ninjas.com/v1/exercises?type=stretching",
                headers={
                    #input the API key for the project
                    "X-API-Key": "BB+Yg/m06BKgSpFZ+FCbdw==W7rniUupiho7pyGz"
                }
            )
            if response.status_code == 200:# if the response worked
                warm_ups = response.json()[:3] # update the list (holds three exercises for now)
    except Exception as e: # if the try did not work
        print(f"Error fetching warm-up excercises: {e}")#print an error message on the webpage

    # GET: render calendar
    exercises = UserExercise.objects.filter(user=request.user)
    return render(request, 'calendar.html', {'events': exercises, 'warm_ups': warm_ups})

@login_required
def workout_events(request):
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)

    # Retrieve all exercises associated with the logged-in user
    exercises = UserExercise.objects.filter(user=request.user)

    # Retrieve completed workouts from the WorkoutLog model
    completed_workouts = WorkoutLog.objects.filter(user=request.user).values_list("exercise_id", "date_completed")
    completed_dict = {(ex_id, date_completed) for ex_id, date_completed in completed_workouts}

    # Prepare an empty dictionary to store workouts grouped by date
    events_by_date = {}

    for exercise in exercises:
        start_date = exercise.start_date
        end_date = exercise.end_date if exercise.end_date else start_date
        recurring_day = exercise.recurring_day

        current_date = start_date
        if current_date.weekday() != recurring_day:
            days_ahead = (recurring_day - current_date.weekday()) % 7
            current_date += timedelta(days=days_ahead)

        while current_date <= end_date:
            # Check if this event is marked as completed in WorkoutLog
            completed = (exercise.id, current_date) in completed_dict

            event = {
                "id": exercise.id,  # Add id field for JS to use
                "title": exercise.exercise.name,
                "gif-url": exercise.exercise.gif_url,
                "start": current_date.strftime('%Y-%m-%d'),
                "color": "#28A745" if completed else "#007BFF",  # Green if completed, blue otherwise
                "completed": completed,
            }

            # Add event to the dictionary, grouped by date
            if current_date not in events_by_date:
                events_by_date[current_date] = []
            events_by_date[current_date].append(event)
            # Move to the next recurrence (one week later)
            current_date += timedelta(weeks=1)

    # Flatten the grouped events and return as a list sorted by date
    sorted_events = []
    for date in sorted(events_by_date.keys()):
        sorted_events.extend(events_by_date[date])

    return JsonResponse(sorted_events, safe=False)

@login_required
def completed_workouts(request):
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)

    logs = WorkoutLog.objects.filter(user=request.user).order_by("-date_completed")

    results = [
        {
            "title": log.exercise.exercise.name,
            "date_completed": log.date_completed.strftime("%Y-%m-%d"),
        }
        for log in logs
    ]

    return JsonResponse(results, safe=False)