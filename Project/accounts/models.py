# pylint: disable=C0301, E0401, E0611, W0613, E1101, E0307
"""Models for user fitness profiles, goals, injuries, exercise logs, and food tracking."""

from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extends the built-in Django User model to store fitness-related user data.

    Attributes:
        user (OneToOneField): The linked Django User account.
        height (float): Height in inches.
        weight (float): Weight in pounds.
        bmi (float): Body Mass Index, calculated separately.
        fitness_level (str): A choice field representing current fitness status.
        goals (ManyToManyField): Goals selected by the user.
        injury_history (ManyToManyField): Past or current injuries selected by the user.
        friends (ManyToManyField): List of mutual friends (users).
        weight_history (str): Placeholder for future or temporary weight tracking.
    """

    FITNESS_LEVEL_CHOICES = [
        (
            "beginner",
            "Beginner – New to exercise or returning after a long break. Low endurance, strength, and flexibility.",
        ),
        (
            "intermediate",
            "Intermediate – Engages in regular physical activity (e.g., 1-3 times per week), has moderate endurance and strength.",
        ),
        (
            "advanced",
            "Advanced – High fitness level with consistent training (e.g., 3+ times per week), strong endurance, strength, and flexibility.",
        ),
        (
            "athlete",
            "Athlete – Trains for specific performance goals (e.g., competitive sports, weightlifting, endurance events).",
        ),
        (
            "rehab",
            "Rehabilitation/Recovery – Focused on regaining fitness after an injury, surgery, or medical condition.",
        ),
        (
            "senior",
            "Senior/Low Impact – Prioritizes joint-friendly and lower-intensity movements, often for older adults or those with physical limitations.",
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
        """Return the username of the associated user."""
        return self.user.username


class FitnessLevel(models.Model):
    """
    Represents a predefined fitness level label.

    Attributes:
        name (str): The name of the fitness level.
    """

    name = models.CharField(max_length=100)

    def __str__(self):
        """Return the fitness level name."""
        return self.name


class Goal(models.Model):
    """
    Represents a fitness or health-related goal.

    Attributes:
        name (str): Goal title.
        description (str): Detailed explanation of the goal.
    """

    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        """Return the goal name."""
        return self.name


class Injury(models.Model):
    """
    Represents a record of a physical injury.

    Attributes:
        name (str): Injury name or type.
        description (str): Additional details about the injury.
    """

    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        """Return the injury name."""
        return self.name


class FriendRequest(models.Model):
    """
    Represents a pending friend request between two users.

    Attributes:
        from_user (User): User who sent the request.
        to_user (User): User who received the request.
    """

    from_user = models.ForeignKey(
        User, related_name="sent_requests", on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        User, related_name="received_requests", on_delete=models.CASCADE
    )

    def __str__(self):
        """Return a string showing who sent the friend request to whom."""
        return f"{self.from_user.username} -> {self.to_user.username}"


class UserAccExercise(models.Model):
    """
    Logs a user's specific exercise activity.

    Attributes:
        id (int): Primary key.
        user (User): Owner of the log.
        name (str): Name of the exercise.
        sets (int): Number of sets performed.
        reps (int): Number of reps per set.
        weight (int): Weight used for the exercise.
    """

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    sets = models.IntegerField(default=0)
    reps = models.IntegerField(default=0)
    weight = models.IntegerField(default=0)


class FoodDatabase(models.Model):
    """
    Logs nutritional data from food entries associated with a user.

    Attributes:
        id (int): Primary key.
        user (User): Owner of the food entry.
        datelog (date): The date the food was logged.
        barcode (int): Unique food barcode or identifier.
        name (str): Name of the food item.
        carbs (float): Carbohydrates per serving.
        protein (float): Protein per serving.
        fat (float): Fat per serving.
        servings (float): Number of servings consumed.
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
def create_or_save_userprofile(sender, instance, created, **kwargs):
    """
    Signal handler to create or save a UserProfile whenever a User instance is created or saved.

    Args:
        sender (Model): The model class (User).
        instance (User): The actual instance being saved.
        created (bool): Whether this is a new instance.
        **kwargs: Additional keyword arguments.
    """
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.userprofile.save()
