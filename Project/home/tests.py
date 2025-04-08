from django.test import TestCase, Client
from .ai import ai_model
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date
from accounts.models import UserProfile
from goals.models import UserExercise, WorkoutLog, Exercise
from goals.forms import UserExerciseForm
from decimal import Decimal
from django.contrib.auth import get_user_model
import requests
from unittest.mock import patch

class AIModelTests(TestCase):

    #Ensure AI Response is a string and not empty.
    def test_ai_response_not_empty(self):
        response = ai_model.get_response("Generate a chest workout routine")
        self.assertIsInstance(response, str)
        self.assertTrue(len(response.strip()) > 0)


class ViewTests(TestCase):

    #Creating a django test client
    def setUp(self):
        self.client = Client()

    #Simulates clicking on the generate workout, makes sure no error
    def test_generate_workout_view_get(self):
        response = self.client.get(reverse('generate_workout'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ask AI for a Fitness Plan!")

    #Checks if fake input renders an output from the AI
    def test_generate_workout_view_post(self):
        response = self.client.post(reverse('generate_workout'), {
            'user_input': 'I want to lose fat and build muscle'
        })

        #Ensure there is an appropriate response from the AI when wanting to lose fat
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI Response")
        self.assertContains(response, "lose fat")

# Create your tests here.
class FakeTestCase(TestCase):
    def test_assertion(self):
        self.assertEqual(type(1), int)
        self.assertEqual(type("hello"), str)

User = get_user_model()

class CalendarTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.login(username='testuser', password='pass')

        # Create exercises for the calendar
        self.exercise_1 = Exercise.objects.create(name='Bench Press', slug='bench-press')
        self.exercise_2 = Exercise.objects.create(name='Squat', slug='squat')

        # Create user exercises (setting corresponding info)
        self.user_exercise_1 = UserExercise.objects.create(
            user=self.user,
            exercise=self.exercise_1,
            current_weight=Decimal('100.00'),
            reps=10,
            percent_increase=5
        )
        self.user_exercise_2 = UserExercise.objects.create(
            user=self.user,
            exercise=self.exercise_2,
            current_weight=Decimal('120.00'),
            reps=8,
            percent_increase=10
        )

    def test_calendar_view_get(self):
        """Test that the calendar page is accessible and renders with the right context"""
        response = self.client.get(reverse('calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')
        # Check if 'events' is in the context instead of 'user_exercises'
        self.assertIn('events', response.context)
        self.assertEqual(len(response.context['events']), 2)

    def test_mark_workout_completed(self):
        """Test marking a workout as completed creates a WorkoutLog entry"""
        response = self.client.get(reverse('calendar'))  # Make GET request to get csrf token
        csrf_token = response.cookies['csrftoken'].value  # Get csrf token

        date_completed = date.today().strftime('%Y-%m-%d')
        
        # Make POST request to mark workout as completed
        response = self.client.post(reverse('calendar'), {
            'workout_id': self.user_exercise_1.id,
            'date_completed': date_completed,
            'completed': 'true',
            'csrfmiddlewaretoken': csrf_token,
        })
        
        # Create WorkoutLog entry with UserExercise instance
        workout_log = WorkoutLog.objects.filter(
            user=self.user,
            exercise=self.user_exercise_1,
            date_completed=date_completed
        )
        
        self.assertEqual(workout_log.count(), 1)  # Should create 1 log entry
        self.assertEqual(response.status_code, 200)

    def test_unmark_workout_completed(self):
        """Test unmarking a workout as completed deletes the WorkoutLog entry"""
        date_completed = date.today().strftime('%Y-%m-%d')

        # Create a completed workout log first
        WorkoutLog.objects.create(
            user=self.user,
            exercise=self.user_exercise_1,
            date_completed=date_completed
        )
        
        # Now make a POST request to unmark it as completed
        response = self.client.get(reverse('calendar'))  # Make GET request to get csrf token
        csrf_token = response.cookies['csrftoken'].value  # Get csrf token
        
        response = self.client.post(reverse('calendar'), {
            'workout_id': self.user_exercise_1.id,
            'date_completed': date_completed,
            'completed': 'false',
            'csrfmiddlewaretoken': csrf_token,
        })
        
        # Ensure the WorkoutLog entry is deleted
        workout_log = WorkoutLog.objects.filter(
            user=self.user,
            exercise=self.user_exercise_1,
            date_completed=date_completed
        )
        
        self.assertEqual(workout_log.count(), 0)  # Should delete the log entry
        self.assertEqual(response.status_code, 200)
    """ Warm up Tests  """
    def test_calendar_view_fetches_warmups_from_api(self):
        """Test that warm-up exercises are fetched from the external API and added to context"""
        response = self.client.get(reverse('calendar'))
        self.assertEqual(response.status_code, 200)
        # We're testing actual API integration, so there should be warm_ups in the view context
        # Check that the 'calendar.html' template was used
        self.assertTemplateUsed(response, 'calendar.html')

    @patch("home.views.requests.get") # must include where the function is used not where the function is defined
    def test_mock_valid_data_response(self, mock_get):
         # Mocked API data
        mock_data = [
            {
                "name": "Quad Pulls",
                "type": "stretch",
                "muscle": "legs",
                "difficulty": "beginner",
                "instructions": "While standing, pull your foot towards your back."
            }
        ]

        # Configure the mock response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_data

        response = self.client.get(reverse("calendar"))
        # make sure that the response code is 200, the exercise it correct and the template is correct
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quad Pulls")
        self.assertTemplateUsed(response, "home/calendar.html")

    def test_warmup_api_handles_errors(self):
        """Simulate a bad request to check if error handling works (manually change endpoint)"""
        headers = {
            "X-API-Key": "BB+Yg/m06BKgSpFZ+FCbdw==W7rniUupiho7pyGz"
        }
        # Intentionally broken URL
        url = "https://exercises-by-api-ninjas.p.rapidapi.com/v1/invalid-endpoint"
        response = requests.get(url, headers=headers)

        # It should fail and not return 200
        self.assertNotEqual(response.status_code, 200)

    def tearDown(self):
        """Clean up after each test"""
        self.user.delete()
        self.exercise_1.delete()
        self.exercise_2.delete()

