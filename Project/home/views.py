from django.shortcuts import render
from accounts.models import UserProfile
from .ai import ai_model  # Import the AI model instance
from goals.models import UserExercise

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
    exercises = UserExercise.objects.all()
    events = []

    weekday_map = {
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
        6: "Saturday",
        7: "Sunday",
    }

    for exercise in exercises:
        events.append({
            "title": exercise.exercise.name,
            "start": exercise.start_date.strftime('%Y-%m-%d'),  # Format date for JS
            "end": exercise.end_date.strftime('%Y-%m-%d'),
            "dow": [exercise.recurring_day - 1] if exercise.recurring_day else [],  # Adjust for FullCalendar (0 = Sunday)
            "color": "#007BFF"  # Optional: Set color
        })

    return JsonResponse(events, safe=False)