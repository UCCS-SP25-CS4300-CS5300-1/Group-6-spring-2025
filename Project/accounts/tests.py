from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import UserProfile, Goal, Injury
from .forms import UserRegistrationForm, UserProfileUpdateForm

class UserProfileModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpassword")

    def test_user_profile_creation(self):
        """Ensure a UserProfile is created when a User is created."""
        profile = UserProfile.objects.get(user=self.user)
        self.assertIsNotNone(profile)

    def test_bmi_calculation(self):
        """Check if BMI is calculated correctly."""
        profile = self.user.userprofile
        profile.height = 70  # inches
        profile.weight = 150  # lbs
        profile.save()

        height_m = profile.height * 0.0254
        weight_kg = profile.weight * 0.453592
        profile.bmi = weight_kg / (height_m ** 2) if height_m > 0 else None
        profile.save()

        expected_bmi = weight_kg / (height_m ** 2)
        self.assertAlmostEqual(profile.bmi, expected_bmi, places=2)

    def test_many_to_many_relationships(self):
        """Ensure goals and injuries can be added to a UserProfile."""
        goal = Goal.objects.create(name="Build Strength", description="Increase muscle mass")
        injury = Injury.objects.create(name="Knee Injury", description="Previous ACL tear")

        profile = self.user.userprofile
        profile.goals.add(goal)
        profile.injury_history.add(injury)

        self.assertIn(goal, profile.goals.all())
        self.assertIn(injury, profile.injury_history.all())

class UserAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=False)  # Disable CSRF for testing
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpassword")

    def test_register_view(self):
        """Ensure users can register successfully."""
        register_url = reverse("register")
        print(f"Register URL: {register_url}")  # Debugging URL resolution

        response = self.client.post(register_url, {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword"
        })

        self.assertEqual(response.status_code, 302)  # Expect redirect
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_login_view(self):
        """Ensure users can log in."""
        login_url = reverse("login")
        print(f"Login URL: {login_url}")  # Debugging URL resolution

        print(f"Users in DB: {User.objects.all()}")  # Ensure user exists
        response = self.client.post(login_url, {
            "username": "testuser",
            "password": "testpassword"
        })

        self.assertEqual(response.status_code, 302)  # Expect redirect
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_logout_view(self):
        """Ensure users can log out."""
        self.client.login(username="testuser", password="testpassword")
        logout_url = reverse("logout")
        print(f"Logout URL: {logout_url}")  # Debugging URL resolution

        response = self.client.get(logout_url)
        self.assertEqual(response.status_code, 302)  # Expect redirect

class UserProfileUpdateTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=False)  # Disable CSRF
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpassword")
        self.client.login(username="testuser", password="testpassword")

    def test_update_profile(self):
        """Ensure users can update their profile information."""
        goal = Goal.objects.create(name="Lose Weight", description="Cut fat percentage")
        injury = Injury.objects.create(name="Back Pain", description="Chronic lower back pain")

        update_profile_url = reverse("update_profile")
        print(f"Update Profile URL: {update_profile_url}")  # Debugging URL resolution

        response = self.client.post(update_profile_url, {
            "height": "72",
            "weight": "180",
            "goals": [goal.id],
            "injury_history": [injury.id]
        })

        self.assertEqual(response.status_code, 302)  # Expect redirect
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.height, 72)
        self.assertEqual(profile.weight, 180)
        self.assertIn(goal, profile.goals.all())
        self.assertIn(injury, profile.injury_history.all())

class FormTests(TestCase):
    def test_user_registration_form(self):
        """Ensure the UserRegistrationForm validates input correctly."""
        form = UserRegistrationForm(data={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword"
        })
        self.assertTrue(form.is_valid())

    def test_user_registration_form_invalid(self):
        """Ensure the UserRegistrationForm handles invalid input."""
        form = UserRegistrationForm(data={
            "username": "",  # Invalid username
            "email": "test@example.com",
            "password": "securepassword"
        })
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_user_profile_update_form(self):
        """Ensure the UserProfileUpdateForm works as expected."""
        form = UserProfileUpdateForm(data={
            "height": "70",
            "weight": "160",
            "fitness_level": "intermediate"
        })
        self.assertTrue(form.is_valid())

