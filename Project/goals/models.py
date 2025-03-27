from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from decimal import Decimal
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"

class Exercise(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

# Define choices from 0% to 100% in 5% increments.
PERCENT_CHOICES = [(i, f'{i}%') for i in range(0, 101, 5)]

class UserExercise(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    current_weight = models.DecimalField(max_digits=6, decimal_places=2)
    reps = models.PositiveIntegerField()
    percent_increase = models.IntegerField(choices=PERCENT_CHOICES, default=0)
    
     # Recurring workout fields
    start_date = models.DateField(default=now)  # When recurrence starts
    end_date = models.DateField(null=True, blank=True)  # Optional end date
    recurring_day = models.IntegerField(choices=RECURRENCE_CHOICES, default=0)  # Default to Monday

    @property
    def goal_weight(self):
        # Calculate goal weight using Decimal arithmetic for precision.
        return self.current_weight * (Decimal('1') + Decimal(self.percent_increase) / Decimal('100'))

    def __str__(self):
        return f"{self.user.username} - {self.exercise.name} (Every {self.get_recurring_day_display()} from {self.start_date} to {self.end_date})"
