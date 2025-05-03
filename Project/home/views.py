# pylint: disable=no-member,invalid-name

"""
Workout AI and Calendar Views

This module handles the generation of AI-powered workout plans, saving them to the
calendar, and rendering user-specific exercise and workout event data in views.

Features:
- AI workout generation using prompt templates
- Parsing and saving workout plans to user's calendar
- Viewing and toggling completed workouts on a calendar
- Providing warm-up suggestions via external API
"""

import json
import os
import re
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils.crypto import get_random_string
from django.utils.text import slugify

from accounts.models import UserProfile
from goals.models import UserExercise, WorkoutLog, Exercise
from .ai import ai_model

# Handles AI generated workout to the calendar
@login_required
def save_to_calendar(request):
    """
    Parses an AI-generated workout plan and saves it to the user's calendar.

    Expected POST payload:
    {
        "ai_plan": "Workout text...",
        "week_start": "YYYY-MM-DD"
    }

    - Extracts exercise names and reps per day from AI plan
    - Maps workout days to actual dates based on the week's start
    - Saves each exercise to the UserExercise model

    Returns:
        JsonResponse indicating success or failure
    """
    # Ensures this response only happens with a request
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body)
        # Grabs the AI plan workout text
        raw_plan = data.get("ai_plan", "").strip()
        # Gets start date from the user's input to go into calendar
        week_start_str = data.get("week_start")

        # Check to see if anything is missing for plan or dates
        if not raw_plan or not week_start_str:
            return JsonResponse({"error": "Missing data"}, status=400)

        # Convert start string to date object
        week_start = datetime.strptime(week_start_str, "%Y-%m-%d").date()

        # Parse AI Plan
        plan_lines = raw_plan.split("\n")
        current_day = None
        day_workouts = {}

        # Cleaning data to process it
        for line in plan_lines:
            line = line.strip()
            if not line:
                continue
            # Looks for colon (e.g "Friday:"), removes it, adds day to list
            if line.endswith(":"):
                current_day = line[:-1]
                day_workouts[current_day] = []

            # Extract exercise name and reps using regex (eg "2. Bench Press: 4 sets of 6 reps;")
            elif current_day:
                match = re.match(
                    r"\d+\.\s*(.+?):\s*(\d+)\s*sets\s*of\s*(\d+)\s*reps",
                    line,
                    re.IGNORECASE,
                )

                # Get's name of workout and reps, stores as pair
                if match:
                    name = match.group(1).strip()
                    reps = int(match.group(3))
                    day_workouts[current_day].append((name, reps))

                # Handles if AI output doesnt follow expected
                else:
                    fallback_match = re.match(r"\d+\.\s*(.+)", line)
                    name = (
                        fallback_match.group(1).strip()
                        if fallback_match
                        else line.strip()
                    )
                    day_workouts[current_day].append((name, 0))

        # Map weekdays to actual dates (eg. "Friday" -> 2025-04-25)
        day_to_date = {}
        for i in range(7):
            d = week_start + timedelta(days=i)
            day_to_date[d.strftime("%A")] = d

        # Create exercises and attach to user
        for day, exercises in day_workouts.items():
            # Converts date to format needed
            date = day_to_date.get(day)
            if not date:
                print(f" Error unknown day: {day}")
                continue

            # If the exercise name exists, reuse, otherwise create unique slug
            for name, reps in exercises:
                slug = slugify(f"{name}-{get_random_string(4)}")

                try:
                    base_exercise = Exercise.objects.get(name=name)

                except Exercise.DoesNotExist:
                    base_exercise = Exercise.objects.create(
                        name=name,
                        slug=slug,
                        description=f"AI-generated workout for {day}",
                    )
                # Create user's scheduled instance
                UserExercise.objects.create(
                    user=request.user,
                    exercise=base_exercise,
                    start_date=date,
                    end_date=date,
                    recurring_day=date.weekday(),
                    current_weight=0,
                    reps=reps,
                    percent_increase=0,
                )

        return JsonResponse(
            {"status": "success", "saved_days": list(day_workouts.keys())}
        )

    # Print errors for debugging
    except Exception as e:
        print(" Error saving workout:", str(e))
        return JsonResponse({"error": str(e)}, status=500)


# Handles generation of AI workouts
@login_required
def generate_workout(request):
    """
    Generates a workout using AI based on user input and profile context.

    - Loads template prompt from file
    - Replaces placeholders with user data (goals, injuries, etc.)
    - Sends the prompt to the AI model for a response
    - Returns plain text response or renders the template with context

    Returns:
        HttpResponse (text/plain for AJAX, or HTML for normal GET/POST)
    """
    # Initializes context diary for basic template
    context = {}

    # Attempting to pull user information if possible to add to workout
    if request.user.is_authenticated:
        try:
            profile = request.user.userprofile
            context["fitness_level"] = profile.fitness_level or ""
            context["goals"] = ", ".join(goal.name for goal in profile.goals.all())
            context["injuries"] = ", ".join(
                injury.name for injury in profile.injury_history.all()
            )
        except UserProfile.DoesNotExist:
            context["fitness_level"] = ""
            context["goals"] = ""
            context["injuries"] = ""

    if request.method == "POST":
        # Grabs user input from the frontend
        user_info_text = request.POST.get("user_input", "").strip()

        # Opening up the text file that is used to prompt the AI (workout_template.txt)
        template_path = os.path.join(settings.BASE_DIR, "home", "workout_template.txt")
        try:
            with open(template_path, "r", encoding="utf-8") as file:
                prompt_template = file.read()
        except Exception as e:
            return HttpResponse(f"Error reading prompt template: {e}", status=500)

        # Adds in the actual user information to the prompt
        prompt = prompt_template.format(user_info=user_info_text)

        # Attempt to send the prompt to the AI model
        try:
            ai_response = ai_model.get_response(prompt)
        except Exception as e:
            ai_response = f"Error generating response: {e}"

        # Ensures the raw plain text of the AI response is sent, NOT the full HTML file
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return HttpResponse(ai_response, content_type="text/plain")

        # AI response passed to template to be rendered
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
    return render(request, "index.html", {"goals": goals})


@login_required
def calendar_view(request):
    """
    View for displaying and interacting with the workout calendar.

    - On POST: toggles workout completion status for a specific date
    - On GET: renders the calendar with scheduled workouts and warm-ups

    Returns:
        JsonResponse (POST) or rendered HTML (GET)
    """
    # POST: toggle a workout occurrence
    if request.method == "POST":
        workout_id = request.POST.get("workout_id")
        date_str = request.POST.get("date_completed")  # "YYYY-MM-DD"
        completed = request.POST.get("completed") == "true"

        exercise = get_object_or_404(UserExercise, id=workout_id, user=request.user)

        if completed:
            # mark done (create if missing)
            WorkoutLog.objects.get_or_create(
                user=request.user, exercise=exercise, date_completed=date_str
            )
        else:
            # unmark (delete the log for that date)
            WorkoutLog.objects.filter(
                user=request.user, exercise=exercise, date_completed=date_str
            ).delete()

        return JsonResponse(
            {
                "status": "success",
                "workout_id": workout_id,
                "date": date_str,
                "completed": completed,
            }
        )

    warm_ups = []  # create empty list to store warm ups
    try:  # use a try except for requests from the API
        # call the API to get a JSON response listing the exercises
        response = requests.get(
            "https://api.api-ninjas.com/v1/exercises?type=stretching",
            headers={
                # input the API key for the project
                "X-API-Key": "BB+Yg/m06BKgSpFZ+FCbdw==W7rniUupiho7pyGz"
            },
        )
        if response.status_code == 200:  # if the response worked
            warm_ups = response.json()[
                :3
            ]  # update the list (holds three exercises for now)
    except Exception as e:  # if the try did not work
        print(
            f"Error fetching warm-up excercises: {e}"
        )  # print an error message on the webpage

    # GET: render calendar
    exercises = UserExercise.objects.filter(user=request.user)
    return render(request, "calendar.html", {"events": exercises, "warm_ups": warm_ups})


@login_required
def workout_events(request):
    """
    Provides JSON list of scheduled and completed workout events for the user.

    Returns:
        JsonResponse containing a list of events grouped by date.
    """
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)

    # Retrieve all exercises associated with the logged-in user
    exercises = UserExercise.objects.filter(user=request.user)

    # Retrieve completed workouts from the WorkoutLog model
    completed_workouts = WorkoutLog.objects.filter(user=request.user).values_list(
        "exercise_id", "date_completed"
    )
    completed_dict = {
        (ex_id, date_completed) for ex_id, date_completed in completed_workouts
    }

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
                "start": current_date.strftime("%Y-%m-%d"),
                "color": "#28A745"
                if completed
                else "#007BFF",  # Green if completed, blue otherwise
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
    """
    Returns a JSON response containing a list of completed workouts for the authenticated user.

    Each workout entry in the response includes the exercise name and the date it was completed.
    The workouts are ordered by completion date in descending order (most recent first).

    Returns:
        JsonResponse: A list of dictionaries, each containing:
            - 'title' (str): The name of the exercise.
            - 'date_completed' (str): The date the workout was completed in 'YYYY-MM-DD' format.
        If the user is not authenticated, an empty list is returned.
    """
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
