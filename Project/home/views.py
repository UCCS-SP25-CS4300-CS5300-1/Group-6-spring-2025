from django.shortcuts import render
from accounts.models import UserProfile
from .ai import ai_model  # Import the AI model instance

def index(request):
    return render(request, 'index.html')


def generate_workout(request):
    context = {}

    if request.method == 'POST':
        user_input = request.POST.get('user_input', '')

        if user_input:
            try:
                response = ai_model.get_response(user_input)
            except Exception as e:
                response = f"Error generating response: {str(e)}"
            context['output'] = response
            context['user_input'] = user_input

    # ✅ Pull user data regardless of POST (outside if block)
    if request.user.is_authenticated:
        try:
            profile = request.user.userprofile  # or .user_profile based on your model
            context['fitness_level'] = profile.fitness_level
            context['goals'] = ", ".join([goal.name for goal in profile.goals.all()])

            # ✅ Convert injuries to comma-separated string
            injuries = profile.injury_history.all()  # change to match your model field
            injury_list = [i.name for i in injuries]
            context['injuries'] = ", ".join(injury_list)
        except UserProfile.DoesNotExist:
            context['fitness_level'] = ''
            context['goal'] = ''
            context['workout_days'] = ''
            context['injuries'] = ''

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
