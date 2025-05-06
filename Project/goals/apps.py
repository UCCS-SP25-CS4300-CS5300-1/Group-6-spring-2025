"""App configuration for the goals Django application."""

from django.apps import AppConfig


class GoalsConfig(AppConfig):
    """Configuration class for the goals app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'goals'
