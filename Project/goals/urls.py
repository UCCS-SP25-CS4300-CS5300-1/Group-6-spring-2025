"""URL configuration for the goals app."""
# pylint: disable=invalid-name

from django.urls import path
from .views import goals, set_exercises, my_exercises, delete_exercise

app_name = 'goals'

urlpatterns = [
    path('', goals, name='goals'),
    path('set-exercises/', set_exercises, name='set_exercises'),
    path('my-exercises/', my_exercises, name='my_exercises'),
    path('delete_exercise/<int:pk>/', delete_exercise, name='delete_exercise'),
]