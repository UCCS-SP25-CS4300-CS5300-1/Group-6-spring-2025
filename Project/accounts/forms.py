"""
forms.py

This module defines Django form classes used in the user account system.
It includes forms for user registration, profile updates, and logging 
user data such as weight, exercises, and food intake.

Forms:
- UserRegistrationForm: Handles new user sign-up with password hashing.
- UserProfileUpdateForm: Allows users to update profile details like height,
  weight, fitness level, goals, and injury history.
- UserLogDataFormWeight: Used for logging user weight.
- UserLogDataFormExercise: Used for logging exercise details including weight, sets, and reps.
- UserLogDataFormFood: Logs food entries by barcode.
- UserLogDataFormFoodData: Logs detailed nutritional info for food items.

These forms are tightly integrated with
"""

from django import forms
from django.contrib.auth.models import User
from django.db import models
from .models import UserProfile, Goal, Injury, UserAccExercise, FoodDatabase


class UserRegistrationForm(forms.ModelForm):
    """Form for registering a new user."""
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta: # pylint: disable=too-few-public-methods
        """Form variables"""
        model = User
        fields = ["username", "email", "password"]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Enter Username"}),
            "email": forms.EmailInput(attrs={"placeholder": "Enter Email Address"}),
            "password": forms.PasswordInput(attrs={"placeholder": "Enter Password"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        """Create a new user with a hashed password."""
        # Create user instance without saving
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()  # Save the user instance to the database
        return user


class UserProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile information."""
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

    class Meta: # pylint: disable=too-few-public-methods
        """Form variables for their account info"""
        model = UserProfile
        fields = ["height", "weight", "fitness_level", "goals", "injury_history"]
        widgets = {
            "goals": forms.CheckboxSelectMultiple(),  # Use checkboxes for goals
            "injury_history": forms.CheckboxSelectMultiple(),  # Use checkboxes for injuries
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["goals"].queryset = Goal.objects.all()  # pylint: disable=no-member
        self.fields[
            "injury_history"
        ].queryset = Injury.objects.all()  # pylint: disable=no-member


class UserLogDataFormWeight(forms.ModelForm):
    """Form for logging user weight entries."""
    WEIGHT_CHOICES = [
        (i, f"{i} lbs") for i in range(20, 600)
    ]  # Weight from 20 lbs to 600 lbs
    weight = forms.ChoiceField(choices=WEIGHT_CHOICES, required=False)

    class Meta: # pylint: disable=too-few-public-methods
        """Form variables"""
        model = UserProfile
        fields = ["weight"]


class UserLogDataFormExercise(forms.ModelForm):
    """Form for logging user exercise entries."""
    class Meta: # pylint: disable=too-few-public-methods
        """Form variables"""
        model = UserAccExercise
        name = forms.TextInput(attrs={"placeholder": "Enter Username"})
        weight = models.IntegerField(default=0)
        sets = models.IntegerField(default=0)
        reps = models.IntegerField(default=0)
        fields = ["name", "weight", "sets", "reps"]


class UserLogDataFormFood(forms.ModelForm):
    """Form for logging a food item barcode."""
    class Meta: # pylint: disable=too-few-public-methods
        """Form variables"""
        model = FoodDatabase
        barcode = models.IntegerField(default=0)
        fields = ["barcode"]


class UserLogDataFormFoodData(forms.ModelForm):
    """Form for logging detailed food data entry."""
    class Meta: # pylint: disable=too-few-public-methods
        """Form variables and their default values."""
        model = FoodDatabase
        barcode = models.IntegerField(default=0)
        name = models.IntegerField(default=0)
        carbs = models.IntegerField(default=0)
        protein = models.IntegerField(default=0)
        fat = models.IntegerField(default=0)
        servings = models.IntegerField(default=0)
        fields = ["barcode", "name", "carbs", "protein", "fat", "servings"]
