from django.urls import path
from .views import register, user_login, user_data, update_profile, custom_logout, friend_data
from . import views

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('user_data/', user_data, name='user_data'),
    path('update_profile/', update_profile, name='update_profile'),
    path('logout/', custom_logout, name='logout'),

    path('profile/<int:user_id>/', views.profile_view, name='profile'),
    path('friend-request/send/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('friend-request/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friend-request/reject/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('friend/remove/<int:user_id>/', views.remove_friend, name='remove_friend'),
    path('friends/', views.friend_list, name='friend_list'),
    # New URL for friend search
    path('friend-search/', views.friend_search, name='friend_search'),
    path('user_data/<int:user_id>/', friend_data, name='friend_data'),

]