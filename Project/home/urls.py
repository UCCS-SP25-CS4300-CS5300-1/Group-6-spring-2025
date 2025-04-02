from django.urls import path
from .views import index, generate_workout, calendar_view, workout_events, mark_workout_complete

urlpatterns = [
    path('', index, name='home'),  
    path('generate-workout/', generate_workout, name='generate_workout'),
    path('calendar/', calendar_view, name='calendar'),
    path('workout-events/', workout_events, name='workout_events'),
    path('mark-workout-complete/', mark_workout_complete, name='mark_workout_complete')
]