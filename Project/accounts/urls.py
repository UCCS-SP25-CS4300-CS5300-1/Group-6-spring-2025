from django.urls import path
from .views import register, user_login, user_data, update_profile, custom_logout, log_data

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('user_data/', user_data, name='user_data'),
    path('update_profile/', update_profile, name='update_profile'),
    path('logout/', custom_logout, name='logout'),
    path('log_data/', log_data, name='log_data')
]