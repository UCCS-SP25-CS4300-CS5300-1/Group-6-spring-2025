from django.urls import path
from .views import index, generate_workout, calendar_view, workout_events, completed_workouts


# app_name = "home"

urlpatterns = [
    path('', index, name='home'),  
    path('generate-workout/', generate_workout, name='generate_workout'),
    path('calendar/', calendar_view, name='calendar'),
    path('workout-events/', workout_events, name='workout_events'),
    path("completed-workouts/", completed_workouts, name="completed_workouts"),
]