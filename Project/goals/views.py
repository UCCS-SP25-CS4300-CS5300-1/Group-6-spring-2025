from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Exercise, UserExercise, Goal
from .forms import UserExerciseForm
from accounts.forms import UserProfileUpdateForm
from accounts.models import UserProfile


@login_required
def goals(request):
    """
    Display the goals page with the current user's goals and exercises.
    """
    if request.user.is_authenticated:
        try:
            user_profile = request.user.userprofile
            user_goals = user_profile.goals.all()
            print("Goals found:", user_goals.count())
        except UserProfile.DoesNotExist:
            print("UserProfile does not exist for:", request.user)
            user_goals = []
    else:
        user_goals = []

    user_exercises = UserExercise.objects.filter(user=request.user)
    
    context = {
        'user_goals': user_goals,
        'exercises': user_exercises,
    }
    return render(request, 'goals/goals.html', context)


@login_required
def delete_exercise(request, pk):
    """
    Confirm and delete a user exercise.
    """
    exercise_entry = get_object_or_404(UserExercise, pk=pk, user=request.user)
    
    if request.method == 'POST':
        exercise_entry.delete()
        return redirect('goals:my_exercises')
    
    return render(request, 'goals/confirm_delete.html', {'exercise': exercise_entry})


@login_required
def set_exercises(request):
    """
    Display and process a formset for setting user exercises.
    """
    ExerciseFormSet = modelformset_factory(UserExercise, form=UserExerciseForm, extra=0)
    
    if request.method == 'POST':
        formset = ExerciseFormSet(request.POST, queryset=UserExercise.objects.none())
        if formset.is_valid():
            for form in formset:
                # Skip forms that haven't changed (i.e. blank forms)
                if not form.has_changed():
                    continue
                user_exercise = form.save(commit=False)
                user_exercise.user = request.user
                user_exercise.save()
            return redirect('/goals/my-exercises/')
        else:
            print("Formset errors:", formset.errors)
    else:
        formset = ExerciseFormSet(queryset=UserExercise.objects.none())
        
    return render(request, 'goals/set_exercises.html', {'formset': formset})


@login_required
def my_exercises(request):
    """
    Display the list of exercises for the current user.
    """
    user_exercises = UserExercise.objects.filter(user=request.user)
    return render(request, 'goals/my_exercises.html', {'exercises': user_exercises})


