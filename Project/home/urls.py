from django.urls import path
from .views import index, generate_workout, calendar_view

urlpatterns = [
    path('', index, name='home'),  
    path('generate-workout/', generate_workout, name='generate_workout'),
    path('calendar/', calendar_view, name='calendar'),
]