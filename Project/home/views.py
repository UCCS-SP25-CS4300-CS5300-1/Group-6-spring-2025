from django.shortcuts import render
from accounts.models import UserProfile
from .ai import ai_model  # Import the AI model instance
from goals.models import UserExercise, WorkoutLog
from django.http import JsonResponse
import datetime
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import timedelta


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

def calendar_view(request):
    # Check if the user is authenticated
    if request.user.is_authenticated:
        # Filter exercises based on the logged-in user
        exercises = UserExercise.objects.filter(user=request.user)  # Assuming a user field in UserExercise
    else:
        # If the user is not authenticated, you might want to handle that case (e.g., redirect to login)
        exercises = []

    print(f"Fetched {exercises.count()} exercises for user {request.user.username}")
    return render(request, 'calendar.html', {'events': exercises})

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

@csrf_exempt 
def mark_workout_complete(request):
    if request.method == "POST" and request.user.is_authenticated:
        data = json.loads(request.body)
        exercise_id = data.get("exercise_id")
        date_completed = data.get("date_completed")  # Expected format: "YYYY-MM-DD"

        if not exercise_id or not date_completed:
            return JsonResponse({"error": "Invalid data"}, status=400)

        # Get the UserExercise instance
        try:
            exercise = UserExercise.objects.get(id=exercise_id, user=request.user)
        except UserExercise.DoesNotExist:
            return JsonResponse({"error": "Exercise not found"}, status=404)

        # Check if the workout has already been logged
        workout, created = WorkoutLog.objects.get_or_create(
            user=request.user,
            exercise=exercise,
            date_completed=date_completed,
            defaults={"completed": True}
        )

        return JsonResponse({"message": "Workout marked as complete" if created else "Workout already marked complete"})

    return JsonResponse({"error": "Unauthorized"}, status=403)