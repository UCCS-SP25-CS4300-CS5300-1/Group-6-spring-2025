from django.shortcuts import render, get_object_or_404
from accounts.models import UserProfile
from .ai import ai_model  # Import the AI model instance
from goals.models import UserExercise, WorkoutLog, Exercise, Goal
from django.http import JsonResponse
import datetime
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import timedelta
import requests


def index(request):
    return render(request, 'index.html')

#Recieves a request object from django
def generate_workout(request):

    #Creating dictionary to pass HTML to
    context = {}
    
    #Check if user clicked a button
    if request.method == 'POST':

        #Obtain the user input that was submitted.
        user_input = request.POST.get('user_input', '')

        #Check is user input is empty
        if user_input:
            try:
                #if not empty- get a response from the ai model with user input as prompt
                response = ai_model.get_response(user_input)
            except Exception as e:
                response = f"Error generating response: {str(e)}"

            #Adding both output and response to context diary
            context['output'] = response
            context['user_input'] = user_input

    #Rendering the html while passing the context diary
    return render(request, 'generate_workout.html', context)

def index(request):
    if request.user.is_authenticated:
        try:
            user_profile = request.user.userprofile
            goals = user_profile.goals.all()
            print("Goals found:", goals.count())
        except UserProfile.DoesNotExist:
            print("UserProfile does not exist for:", request.user)
            goals = []
    else:
        goals = []
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
    
    warm_ups = [] # create empty list to store warm ups 
    try: #use a try except for requests from the API
        # call the API to get a JSON response listing the exercises
        response = requests.get("https://exercises-by-api-ninjas.p.rapidapi.com/v1/exercises?type=cardio",
            headers={ 
                #input the API key for the project
                "X-RapidAPI-Key": "BB+Yg/m06BKgSpFZ+FCbdw==W7rniUupiho7pyGz",
                # call the correct API through the API ninjas offerings 
                "X-RapidAPI-Host": "exercises-by-api-ninjas.p.rapidapi.com"
            }
        )
        if responses.status_code == 200: # if the response worked 
            warm_ups = response.json()[:3] # update the list (holds three exercises for now)
    except Exception as e: # if the try did not work 
        print(f"Error fetching warm-up excercises: {e}") #print an error message on the webpage

    # GET: render calendar
    exercises = UserExercise.objects.filter(user=request.user)
    return render(request, 'calendar.html', {'events': exercises})
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

