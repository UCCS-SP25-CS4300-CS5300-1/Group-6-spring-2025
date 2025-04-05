from django import forms
from .models import UserExercise

class UserExerciseForm(forms.ModelForm):

    class Meta:
        model = UserExercise
        fields = ['exercise', 'current_weight', 'reps', 'percent_increase', 'start_date', 'end_date', 'recurring_day']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_exercise(self):
        exercise = self.cleaned_data.get('exercise')
        if not exercise:
            raise forms.ValidationError("Please select an exercise.")
        return exercise

    def clean_current_weight(self):
        current_weight = self.cleaned_data.get('current_weight')
        if current_weight is not None and current_weight < 0:
            raise forms.ValidationError("Current weight cannot be negative.")
        return current_weight

    def clean_recurring_day(self):
        recurring_day = self.cleaned_data.get('recurring_day')
        if recurring_day is None:
            raise forms.ValidationError("Please select a recurrence day.")
        return recurring_day

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date cannot be after end date.")