# pylint: disable=E0401, E0611
"""
URL configuration for user-related views, including authentication and friendship management.

This module defines the URL patterns for user registration, login, profile management,
friendship actions, and log data. The views corresponding to these URLs handle tasks such as
user registration, login/logout, updating user profiles, sending and accepting friend requests,
viewing and removing friends, and managing friend searches.

The following routes are included:
- Register, login, and logout functionality.
- User data management, including profile updates and viewing.
- Friend request handling (send, accept, reject).
- Friendship list and data management.
- Searching for friends.
- Logging data for user activities.

Each route corresponds to a specific view function that implements the logic for the corresponding
action.
"""

from django.urls import path
from .views import (
    register,
    user_login,
    user_data,
    update_profile,
    custom_logout,
    send_friend_request,
    accept_friend_request,
    reject_friend_request,
    remove_friend,
    friend_list,
    friend_search,
    friend_data,
    log_data,
)

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", user_login, name="login"),
    path("user_data/", user_data, name="user_data"),
    path("update_profile/", update_profile, name="update_profile"),
    path("logout/", custom_logout, name="logout"),
    path(
        "friend-request/send/<int:user_id>/",
        send_friend_request,
        name="send_friend_request",
    ),
    path(
        "friend-request/accept/<int:request_id>/",
        accept_friend_request,
        name="accept_friend_request",
    ),
    path(
        "friend-request/reject/<int:request_id>/",
        reject_friend_request,
        name="reject_friend_request",
    ),
    path("friend/remove/<int:user_id>/", remove_friend, name="remove_friend"),
    path("friends/", friend_list, name="friend_list"),
    path("friend-search/", friend_search, name="friend_search"),
    path("user_data/<int:user_id>/", friend_data, name="friend_data"),
    path("log_data/", log_data, name="log_data"),
]
