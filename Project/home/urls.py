from django.urls import path
from .views import index, generate_workout, calendar_view, workout_events, save_to_calendar, replace_exercise, exercise_info

urlpatterns = [
    path('', index, name='home'),  
    path('generate-workout/', generate_workout, name='generate_workout'),
    path('calendar/', calendar_view, name='calendar'),
    path('workout-events/', workout_events, name='workout_events'),
    path("save-to-calendar/", save_to_calendar, name="save_to_calendar"),
    path("replace-exercise/", replace_exercise, name="replace_exercise"),
    path("exercise-info/", exercise_info, name="exercise_info"),
]