from django.urls import path
from .views import index, generate_workout

urlpatterns = [
    path('', index, name='home'),  
    path('generate-workout/', generate_workout, name='generate_workout')
]