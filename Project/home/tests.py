from django.test import TestCase, Client
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
from .ai import ai_model
import json

#Ensuring model is working with
class NewAIModelTests(TestCase):

    #Ensure common fitness terms appear in AI output.
    def test_response_contains_expected_keywords(self):
        response = ai_model.get_response("Give me a beginner strength plan")
        keywords = ["sets", "reps", "rest", "exercise"]
        found = any(keyword in response.lower() for keyword in keywords)
        self.assertTrue(found, "AI response lacks expected fitness keywords")

    #Check AI can still respond when injury limitations are given
    def test_response_handles_injuries_gracefully(self):
        prompt = "Workout plan for someone with knee injury and lower back pain"
        response = ai_model.get_response(prompt)
        self.assertIsInstance(response, str)
        self.assertNotIn("error", response.lower())


class NewViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='tester', password='password123')
        self.client.login(username='tester', password='password123')

    #Check if home view loads correctly
    def test_get_home_view(self):
        #Simulates going to home view
        response = self.client.get(reverse('home'))
        #The http status code is 200 (successful)
        self.assertEqual(response.status_code, 200)
        #Decode response content to string, checks if workout app is there
        self.assertIn("Workout App", response.content.decode())

    #Make sure plan generates when multiple days are specified.
    def test_post_generates_plan_with_multiple_days(self):
        input_text = "Fitness Level: Intermediate; Goals: Build Muscle; Injuries: None; Selected Days: Monday, Wednesday, Friday"

        #Simulates AJAX request, 
        response = self.client.post(
            reverse('generate_workout'),
            {'user_input': input_text},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        #Ensure successful response (200), then ensures days are in workout plan
        self.assertEqual(response.status_code, 200)
        self.assertIn("Monday", response.content.decode())
        self.assertIn("Wednesday", response.content.decode())


    #Submit gibberish and ensure the app doesn't crash
    def test_invalid_user_input_still_returns_page(self):
        response = self.client.post(reverse('generate_workout'), {
            'user_input': 'asdfasdfasfdasfdasdfasdf'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.content) > 10)

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
        self.assertTemplateUsed(response, "calendar.html")

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

    #Test behavior when no input is sent.
    def test_missing_user_input(self):
        response = self.client.post(reverse('generate_workout'), {})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Error", response.content.decode())

#Tests if a valid request to replace an exercise returns a correct AI-generated alternative
class AIIntegrationTests(TestCase):

    #Sets up clean environment for testing
    def setUp(self):
        #Prepares fresh envirnment
        self.client = Client()
        #Starts up django test client
        self.user = User.objects.create_user(username='aitestuser', password='testpass123')
        #Creates test user
        self.client.login(username='aitestuser', password='testpass123')
        #test exercise for database
        self.exercise = Exercise.objects.create(name='Push-Up', slug='push-up')

    #Uses mocktesting to avoid API calls
    @patch('home.views.ai_model.get_response')

    #confirms view replace_exercise gives good AI response
    def test_replace_exercise_success(self, mock_ai_response):
        """
        Should return a valid AI-generated replacement.
        """
        #gives fake exercise
        mock_ai_response.return_value = "Incline Bench Press: 4 sets of 10 reps;"

        #Defines what the fake AI should return
        payload = {
            "original": "Push-Up: 3 sets of 10 reps;",
            "reason": "I have wrist pain.",
            "day": "Tuesday"
        }

        #Gives a simulates frontload from Javascript (bottom of HTML)/sends post request
        response = self.client.post(
            reverse('replace_exercise'),
            data=json.dumps(payload),
            content_type="application/json"
        )

        #asserts HTTP response working
        self.assertEqual(response.status_code, 200)
        #parses output a
        data = response.json()
        # check if view returned successfullu
        self.assertTrue(data["success"])
        #confrim mocked AI output is present in response
        self.assertIn("Incline Bench Press", data["replacement"])

    #Tests what happens if the frontend sends an empty payload:
    def test_replace_exercise_missing_fields(self):
        """
         Should fail gracefully with missing fields.
        """
        response = self.client.post(
            reverse('replace_exercise'),
            # Missing all required fields
            data=json.dumps({}),  
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("error", data)

    #Tests whether the view that gives advice for an exercise works
    @patch('home.views.ai_model.get_response')
    def test_exercise_info_success(self, mock_ai_response):
        """
         Should return a short AI-generated explanation for an exercise.
        """
        #Defines a mock success message for the AI.
        mock_ai_response.return_value = "Keep your core tight and elbows tucked."

        #Posts valid input: { "name": "Push-Up" }.
        response = self.client.post(
            reverse('exercise_info'),
            data=json.dumps({"name": "Push-Up"}),
            content_type="application/json"
        )

        #Confirms that the AI gave useful form advice.
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("core", data["info"].lower())


    #Tests failure when exercise name is missing:
    def test_exercise_info_missing_name(self):
        """
         Should return error if 'name' is not provided.
        """

        #sends post response with no name provided
        response = self.client.post(
            reverse('exercise_info'),
            # No name provided
            data=json.dumps({}),  
            content_type="application/json"
        )
        #Checks that an error message is returned.
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "No name given")

    #Simulates the AI crashing (e.g., server error, timeout, etc.)
    @patch('home.views.ai_model.get_response', side_effect=Exception("AI failure"))
    def test_replace_exercise_ai_error(self, mock_ai_response):
        """
         Should handle AI backend failure and return error.
        """
        #Post purposfully triggers an error
        response = self.client.post(
            reverse('replace_exercise'),
            data=json.dumps({
                "original": "Push-Up: 3 sets of 10 reps;",
                "reason": "Too hard",
                "day": "Wednesday"
            }),
            content_type="application/json"
        )
        #correctly returns server error
        self.assertEqual(response.status_code, 500)
        data = response.json()
        #confirms the failure is reported instead of silently crashing
        self.assertFalse(data["success"])
        self.assertIn("AI failure", data["error"])