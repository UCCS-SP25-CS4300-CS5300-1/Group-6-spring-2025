from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile

class UserRegistrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Enter Username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter Email Address'}),
            'password': forms.PasswordInput(attrs={'placeholder': 'Enter Password'}),
        }

    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = ""  # Remove help text
        self.fields['username'].error_messages = {
            'required': 'Please enter a username.',
            'max_length': 'Your username must be 150 characters or fewer.',
            'invalid': 'This value may contain only letters, numbers, and @/./+/-/_ characters.',
        }
        self.fields['email'].error_messages = {
            'required': 'Please enter your email address.',
            'invalid': 'Enter a valid email address.',
        }
        self.fields['password'].error_messages = {
            'required': 'Please enter a password.',
        }

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bmi', 'fitness_level', 'goals', 'injury_history']
        widgets = {
            'goals': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your fitness goals here...'}),
            'injury_history': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter any injury history here...'}),
        }