"""
App configuration for the 'accounts' app, which manages user accounts and profiles.
"""
from django.apps import AppConfig

class AccountsConfig(AppConfig):
    """
    Configuration class for the 'accounts' app.
    Sets the default primary key type and app name.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
