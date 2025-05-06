"""Models for the goals app."""
# pylint: disable=E1101, R0903

import datetime
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now

RECURRENCE_CHOICES = [
    (0, 'Monday'),
    (1, 'Tuesday'),
    (2, 'Wednesday'),
    (3, 'Thursday'),
    (4, 'Friday'),
    (5, 'Saturday'),
    (6, 'Sunday'),
]


class Goal(models.Model):
    """A fitness goal belonging to a user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')


class Exercise(models.Model):
    """A single type of exercise with metadata."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    body_part = models.CharField(max_length=100)
    target = models.CharField(max_length=100)
    equipment = models.CharField(max_length=100)
    gif_url = models.URLField(blank=True)
    secondary_muscles = models.JSONField(blank=True, default=list)
    instructions = models.JSONField(blank=True, default=list)

    def __str__(self):
        return str(self.name)


# Define choices from 0% to 100% in 5% increments.
PERCENT_CHOICES = [(i, f'{i}%') for i in range(0, 101, 5)]


class UserExercise(models.Model):
    """An exercise entry for a user, including planned recurrence."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    current_weight = models.DecimalField(max_digits=6, decimal_places=2)
    reps = models.PositiveIntegerField()
    percent_increase = models.IntegerField(choices=PERCENT_CHOICES, default=0)

    # Recurring workout fields
    start_date = models.DateField(default=now)
    end_date = models.DateField(null=True, blank=True)
    recurring_day = models.IntegerField(
        choices=RECURRENCE_CHOICES,
        default=0,
    )

    @property
    def goal_weight(self):
        """Return the target weight after applying the percentage increase."""
        return (
            self.current_weight
            * (
                Decimal('1')
                + Decimal(self.percent_increase) / Decimal('100')
            )
        )

    def __str__(self):
        return (
            f"{self.user.username} - {self.exercise.name} (Every "
            f"{self.get_recurring_day_display()} from {self.start_date} "
            f"to {self.end_date})"
        )


class WorkoutLog(models.Model):
    """Log of a user’s completed workout on a given date."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(UserExercise, on_delete=models.CASCADE)
    date_completed = models.DateField(default=datetime.date.today)
    completed = models.BooleanField(default=True)

    class Meta:
        """Prevent duplicate completions on the same day"""
        unique_together = ("user", "exercise", "date_completed")
