"""
URL configuration for the home app.

Includes routes for homepage, workout generation, calendar view,
retrieving workout events, and saving AI-generated workouts.
"""

from django.urls import path
from .views import index, generate_workout, calendar_view, workout_events, save_to_calendar

urlpatterns = [
    path('', index, name='home'),  
    path('generate-workout/', generate_workout, name='generate_workout'),
    path('calendar/', calendar_view, name='calendar'),
    path('workout-events/', workout_events, name='workout_events'),
    path("save-to-calendar/", save_to_calendar, name="save_to_calendar"),
]
