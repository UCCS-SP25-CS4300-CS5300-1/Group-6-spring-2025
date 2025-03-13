from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Goal, Injury, FitnessLevel

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

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

    def save(self, commit=True):
        user = super(UserRegistrationForm, self).save(commit=False)  # Create user instance without saving
        user.set_password(self.cleaned_data["password"])  # Hash the password
        if commit:
            user.save()  # Save the user instance to the database
        return user

class UserProfileUpdateForm(forms.ModelForm):
    HEIGHT_CHOICES = [(i, f"{i} inches") for i in range(24, 96)]  # Height from 2'0" (24 inches) to 8'0" (96 inches)
    WEIGHT_CHOICES = [(i, f"{i} lbs") for i in range(20, 600)]  # Weight from 20 lbs to 600 lbs
    FITNESS_LEVEL_CHOICES = UserProfile.FITNESS_LEVEL_CHOICES

    height = forms.ChoiceField(choices=HEIGHT_CHOICES, required=False)
    weight = forms.ChoiceField(choices=WEIGHT_CHOICES, required=False)
    fitness_level = forms.ChoiceField(choices=FITNESS_LEVEL_CHOICES, required=False)
    #fitness_level = forms.ModelChoiceField(queryset=FitnessLevel.objects.all(), required=False)

    class Meta:
        model = UserProfile
        fields = ['height', 'weight', 'fitness_level', 'goals', 'injury_history']
        widgets = {
            'goals': forms.CheckboxSelectMultiple(),  # Use checkboxes for goals
            'injury_history': forms.CheckboxSelectMultiple(),  # Use checkboxes for injuries
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['goals'].queryset = Goal.objects.all()  # Populate goals
        self.fields['injury_history'].queryset = Injury.objects.all()  # Populate injuries