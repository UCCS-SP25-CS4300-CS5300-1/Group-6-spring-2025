from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bmi = models.FloatField(null=True, blank=True)
    fitness_level = models.CharField(max_length=100, null=True, blank=True)
    goals = models.TextField(null=True, blank=True)
    injury_history = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user.username

class UserData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    bmi = models.FloatField(null=True, blank=True)
    fitness_level = models.CharField(max_length=100, null=True, blank=True)
    goals = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.date}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created: 
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.UserProfile.save()

