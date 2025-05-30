# pylint: disable=E1101, W0611, E0611, E0401, R0903, R1725
"""
Forms for handling user registration, profile updates, and data logging in a
fitness tracking application.

Includes:
- User account registration with password hashing
- User profile updates (height, weight, fitness level, goals, injuries)
- Weight logging
- Exercise logging
- Food data and barcode logging

Each form is tied to a model and provides customized validation, choices, and UI widgets.
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.db import models
from .models import (
    UserProfile,
    Goal,
    Injury,
    FitnessLevel,
    UserAccExercise,
    FoodDatabase,
)


class UserRegistrationForm(forms.ModelForm):
    """
    Form for registering a new user account.

    Hashes the password before saving and sets up error messages and placeholders
    for better form UX.
    """

    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        """
        Meta class for user registration
        """

        model = User
        fields = ["username", "email", "password"]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Enter Username"}),
            "email": forms.EmailInput(attrs={"placeholder": "Enter Email Address"}),
            "password": forms.PasswordInput(attrs={"placeholder": "Enter Password"}),
        }

    def __init__(self, *args, **kwargs):
        """
        Customize field error messages and remove Django's default username help text.
        """
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        self.fields["username"].help_text = ""  # Remove help text
        self.fields["username"].error_messages = {
            "required": "Please enter a username.",
            "max_length": "Your username must be 150 characters or fewer.",
            "invalid": "This value may contain only letters, numbers, and @/./+/-/_ characters.",
        }
        self.fields["email"].error_messages = {
            "required": "Please enter your email address.",
            "invalid": "Enter a valid email address.",
        }
        self.fields["password"].error_messages = {
            "required": "Please enter a password.",
        }

    def save(self, commit=True):
        """
        Hash the password before saving the User instance.
        """
        user = super(UserRegistrationForm, self).save(
            commit=False
        )  # Create user instance without saving
        user.set_password(self.cleaned_data["password"])  # Hash the password
        if commit:
            user.save()  # Save the user instance to the database
        return user


class UserProfileUpdateForm(forms.ModelForm):
    """
    Form for updating the user's profile data including height, weight, fitness level,
    goals, and injury history.
    """

    HEIGHT_CHOICES = [
        (i, f"{i} inches") for i in range(24, 96)
    ]  # Height from 2'0" (24 inches) to 8'0" (96 inches)
    WEIGHT_CHOICES = [
        (i, f"{i} lbs") for i in range(20, 600)
    ]  # Weight from 20 lbs to 600 lbs
    FITNESS_LEVEL_CHOICES = UserProfile.FITNESS_LEVEL_CHOICES

    height = forms.ChoiceField(choices=HEIGHT_CHOICES, required=False)
    weight = forms.ChoiceField(choices=WEIGHT_CHOICES, required=False)
    fitness_level = forms.ChoiceField(choices=FITNESS_LEVEL_CHOICES, required=False)
    # fitness_level = forms.ModelChoiceField(queryset=FitnessLevel.objects.all(), required=False)

    class Meta:
        """
        Meta class for updating user profile
        """

        model = UserProfile
        fields = ["height", "weight", "fitness_level", "goals", "injury_history"]
        widgets = {
            "goals": forms.CheckboxSelectMultiple(),  # Use checkboxes for goals
            "injury_history": forms.CheckboxSelectMultiple(),  # Use checkboxes for injuries
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize dynamic queryset values for goals and injury history.
        """
        super().__init__(*args, **kwargs)
        self.fields["goals"].queryset = Goal.objects.all()  # Populate goals
        self.fields[
            "injury_history"
        ].queryset = Injury.objects.all()  # Populate injuries


class UserLogDataFormWeight(forms.ModelForm):
    """
    Form for logging or updating user's weight.
    """

    WEIGHT_CHOICES = [
        (i, f"{i} lbs") for i in range(20, 600)
    ]  # Weight from 20 lbs to 600 lbs
    weight = forms.ChoiceField(choices=WEIGHT_CHOICES, required=False)

    class Meta:
        """
        Meta class for user weight
        """

        model = UserProfile
        fields = ["weight"]


class UserLogDataFormExercise(forms.ModelForm):
    """
    Form for logging an exercise performed by the user.
    Includes fields for exercise name, weight, sets, and reps.
    """

    class Meta:
        """
        Meta class for user logging exercise
        """

        model = UserAccExercise
        name = forms.TextInput(attrs={"placeholder": "Enter Username"})
        weight = models.IntegerField(default=0)
        sets = models.IntegerField(default=0)
        reps = models.IntegerField(default=0)
        fields = ["name", "weight", "sets", "reps"]


class UserLogDataFormFood(forms.ModelForm):
    """
    Form for logging food using its barcode.
    """

    class Meta:
        """
        Meta class for user logging food via barcode
        """

        model = FoodDatabase
        barcode = models.IntegerField(default=0)
        fields = ["barcode"]


class UserLogDataFormFoodData(forms.ModelForm):
    """
    Form for adding or updating detailed food nutrition data.
    Includes barcode, name, carbs, protein, fat, and servings.
    """

    class Meta:
        """
        Meta class for logging food
        """

        model = FoodDatabase
        barcode = models.IntegerField(default=0)
        name = models.IntegerField(default=0)
        carbs = models.IntegerField(default=0)
        protein = models.IntegerField(default=0)
        fat = models.IntegerField(default=0)
        servings = models.IntegerField(default=0)
        fields = ["barcode", "name", "carbs", "protein", "fat", "servings"]
