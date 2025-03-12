from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    FITNESS_LEVEL_CHOICES = [
        ('beginner', 'Beginner – New to exercise or returning after a long break. Low endurance, strength, and flexibility.'),
        ('intermediate', 'Intermediate – Engages in regular physical activity (e.g., 1-3 times per week), has moderate endurance and strength.'),
        ('advanced', 'Advanced – High fitness level with consistent training (e.g., 3+ times per week), strong endurance, strength, and flexibility.'),
        ('athlete', 'Athlete – Trains for specific performance goals (e.g., competitive sports, weightlifting, endurance events).'),
        ('rehab', 'Rehabilitation/Recovery – Focused on regaining fitness after an injury, surgery, or medical condition.'),
        ('senior', 'Senior/Low Impact – Prioritizes joint-friendly and lower-intensity movements, often for older adults or those with physical limitations.'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    height = models.FloatField(null=True, blank=True, help_text="Height in centimeters")
    weight = models.FloatField(null=True, blank=True, help_text="Weight in kilograms")
    bmi = models.FloatField(null=True, blank=True)
    fitness_level = models.CharField(max_length=20, choices=FITNESS_LEVEL_CHOICES, null=True, blank=True)
    goals = models.ManyToManyField('Goal', blank=True)
    injury_history = models.ManyToManyField('Injury', blank=True)

    def __str__(self):
        return self.user.username

class FitnessLevel(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Goal(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class Injury(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created: 
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

