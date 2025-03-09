from django.urls import path
from .views import register, user_login, user_data, update_profile

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('user_data/', user_data, name='user_data'),
    path('update_profile/', update_profile, name='update_profile'),
    
]