import os
import json
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from accounts.models import UserProfile
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
