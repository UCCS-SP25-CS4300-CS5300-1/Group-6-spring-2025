# pylint: disable=E0401, E0611
"""
This module defines the URL routing for the workout management application.

The urlpatterns list contains the mappings of URL paths to corresponding view functions.
Each view handles a specific functionality of the application such as displaying the homepage,
generating workout plans, viewing and interacting with the calendar, and saving events to the 
calendar.

URL patterns:
- "": Home page
- "generate-workout/": Generate a workout plan based on user input
- "calendar/": Display the user's workout calendar
- "workout-events/": View workout-related events
- "save-to-calendar/": Save a workout event to the calendar

Each path is linked to a specific view function that handles the logic for that URL. These views
are imported from the `views.py` module.
"""

from django.urls import path
from .views import (
    index,
    generate_workout,
    calendar_view,
    workout_events,
    save_to_calendar,
    replace_exercise,
    exercise_info
)

urlpatterns = [
    path("", index, name="home"),
    path("generate-workout/", generate_workout, name="generate_workout"),
    path("calendar/", calendar_view, name="calendar"),
    path("workout-events/", workout_events, name="workout_events"),
    path("save-to-calendar/", save_to_calendar, name="save_to_calendar"),
    path("replace-exercise/", replace_exercise, name="replace_exercise"),
    path("exercise-info/", exercise_info, name="exercise_info"),
]