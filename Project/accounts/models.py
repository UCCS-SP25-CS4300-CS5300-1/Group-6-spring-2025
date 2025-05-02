"""
This module defines models related to user profiles, fitness tracking,
goal management, injury history, social connections (friends and friend requests),
exercise logging, and food intake logging within a Django application.
"""

from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Stores additional user information beyond the default Django User model.

    Includes physical metrics (height, weight, BMI), fitness level,
    goals, injury history, friend connections, and weight history.
    """

    FITNESS_LEVEL_CHOICES = [
        (
            "beginner",
            "Beginner – New to exercise or returning after a long break. \
                Low endurance, strength, and flexibility.",
        ),
        (
            "intermediate",
            "Intermediate – Engages in regular physical activity (e.g., 1-3 times per week), \
                has moderate endurance and strength.",
        ),
        (
            "advanced",
            "Advanced – High fitness level with consistent training (e.g., 3+ times per week), \
                strong endurance, strength, and flexibility.",
        ),
        (
            "athlete",
            "Athlete – Trains for specific performance goals (e.g., competitive sports, \
                weightlifting, endurance events).",
        ),
        (
            "rehab",
            "Rehabilitation/Recovery – Focused on regaining fitness after an injury, \
                surgery, or medical condition.",
        ),
        (
            "senior",
            "Senior/Low Impact – Prioritizes joint-friendly and lower-intensity movements, \
                often for older adults or those with physical limitations.",
        ),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    height = models.FloatField(null=True, blank=True, help_text="Height in inches")
    weight = models.FloatField(null=True, blank=True, help_text="Weight in pounds")
    bmi = models.FloatField(null=True, blank=True)
    fitness_level = models.CharField(
        max_length=20, choices=FITNESS_LEVEL_CHOICES, null=True, blank=True
    )
    goals = models.ManyToManyField("Goal", blank=True)
    injury_history = models.ManyToManyField("Injury", blank=True)
    friends = models.ManyToManyField("self", blank=True, symmetrical=True)
    # is_working_out = models.BooleanField(default=False, help_text="Indicates if the
    # user is working out today.")
    weight_history = models.CharField(
        max_length=200, choices=FITNESS_LEVEL_CHOICES, null=True, blank=True
    )

    def __str__(self):
        return str(self.user.username) # pylint: disable=no-member


class FitnessLevel(models.Model):
    """
    Represents a user-defined or system-defined fitness level category.
    """
    name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.name)


class Goal(models.Model):
    """
    Represents a fitness-related goal the user is aiming to achieve.
    """
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return str(self.name)


class Injury(models.Model):
    """
    Represents a past or current injury associated with a user's profile.
    """
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return str(self.name)


class FriendRequest(models.Model):
    """
    Represents a friend request sent from one user to another.
    """
    from_user = models.ForeignKey(
        User, related_name="sent_requests", on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        User, related_name="received_requests", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username}" # pylint: disable=no-member


class UserAccExercise(models.Model):
    """
    Logs individual exercise details for a user, including sets, reps, and weight.
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    sets = models.IntegerField(default=0)
    reps = models.IntegerField(default=0)
    weight = models.IntegerField(default=0)


class FoodDatabase(models.Model):
    """
    Logs nutritional information for a specific food item consumed by a user.
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    datelog = models.DateField(default=date.today)
    barcode = models.IntegerField(default=0)
    name = models.CharField(max_length=100)
    carbs = models.FloatField(default=0)
    protein = models.FloatField(default=0)
    fat = models.FloatField(default=0)
    servings = models.FloatField(default=0)


@receiver(post_save, sender=User)
def create_or_save_userprofile(_sender, instance, created, **_kwargs):
    """
    Signal to automatically create or save a UserProfile whenever a User is created or updated.
    """
    if created:
        UserProfile.objects.create(user=instance) # pylint: disable=no-member
    else:
        instance.userprofile.save()
