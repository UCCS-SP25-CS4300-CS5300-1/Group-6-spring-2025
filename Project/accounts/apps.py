"""
App configuration for the 'accounts' app. Sets the default auto field and
provides the Django app registry with the app's name.
"""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    Configuration class for the 'accounts' app.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
