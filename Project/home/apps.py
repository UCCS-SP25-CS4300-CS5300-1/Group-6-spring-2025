"""
This module contains the configuration for the 'home' app in the Django project.
It defines the HomeConfig class, which configures settings for the 'home' app.
"""

from django.apps import AppConfig


class HomeConfig(AppConfig):
    """
    Configuration class for the 'home' app. It defines the default auto field
    type and the name of the app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "home"
