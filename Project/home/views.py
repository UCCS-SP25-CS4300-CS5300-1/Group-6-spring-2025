from django.shortcuts import render
from accounts.models import UserProfile
from .ai import ai_model  # Import the AI model instance
from goals.models import UserExercise
from django.http import JsonResponse
import datetime
from django.utils import timezone


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
    if request.user.is_authenticated:
        exercises = UserExercise.objects.filter(user=request.user)
    else:
        exercises = []

    events = []

    for exercise in exercises:
        start_date = exercise.start_date
        end_date = exercise.end_date if exercise.end_date else start_date  # If no end_date, use start_date
        recurring_day = exercise.recurring_day  # This represents the day of the week (0=Monday, 6=Sunday)

        # Start with the first date that matches the recurring day
        current_date = start_date

        # Find the first date that matches the recurring day
        # This will ensure that we start on the correct weekday
        days_ahead = recurring_day - current_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7  # If the day is earlier in the week, find the next occurrence
        first_occurrence = current_date + datetime.timedelta(days=days_ahead)

        # Now, iterate over the range from the first occurrence to the end_date
        current_date = first_occurrence
        while current_date <= end_date:
            # Create event for this specific date
            events.append({
                "title": exercise.exercise.name,
                "start": current_date.strftime('%Y-%m-%d'),  # Set to the recurring day
                "color": "#007BFF",
            })
            # Move to the next occurrence of the recurring day
            current_date += datetime.timedelta(weeks=1)  # Move one week ahead

    return JsonResponse(events, safe=False)