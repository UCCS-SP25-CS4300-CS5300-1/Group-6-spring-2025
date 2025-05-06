"""
This module contains the configuration for the 'home' app in the Django project.

It defines the `HomeConfig` class, which inherits from `AppConfig` and is used to configure
the 'home' app. This includes specifying the default auto field type for models and setting the
app name.

Classes:
    HomeConfig: Configuration class for the 'home' app, inheriting from `AppConfig`.
               It provides necessary setup for the 'home' app in a Django project.

Usage:
    - This class is automatically discovered by Django and used to configure the 'home' app.
    - It specifies the app's name and sets up the default model field type for the app.
"""

from django.apps import AppConfig


class HomeConfig(AppConfig):
    """
    Configuration class for the 'home' app in a Django project.

    This class is used by Django to configure settings for the 'home' app. The `name` attribute
    specifies the app's name, and the `default_auto_field` attribute determines the default field
    type for primary keys in the app's models.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "home"
