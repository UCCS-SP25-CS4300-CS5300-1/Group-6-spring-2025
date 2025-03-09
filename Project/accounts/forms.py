from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bmi', 'fitness_level', 'goals', 'injury_history']
        widgets = {
            'goals': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your fitness goals here...'}),
            'injury_history': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter any injury history here...'}),
        }