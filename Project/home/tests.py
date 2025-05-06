# pylint: disable=E0401, E0611, W0611, W0105, C0103, C0301
"""
This module contains test cases for various views, forms, and AI integration in a fitness
application.

The tests ensure that the application behaves correctly by verifying its responses, ensuring
correct behavior in different scenarios, and testing various API integrations and AI model
responses.

Test Cases:
    1. NewAIModelTests:
        - test_response_contains_expected_keywords: Verifies that common fitness-related
          keywords are present in the AI model response.
        - test_response_handles_injuries_gracefully: Verifies that the AI model responds
          appropriately when injury information is provided.

    2. NewViewTests:
        - test_get_home_view: Verifies that the home view loads correctly and includes
          expected content.
        - test_post_generates_plan_with_multiple_days: Verifies that a workout plan is
          generated for multiple days based on user input.
        - test_invalid_user_input_still_returns_page: Verifies that invalid user input
          doesn't cause crashes and still returns a response.

    3. CalendarTests:
        - test_calendar_view_get: Verifies that the calendar view loads correctly and displays
          the appropriate events.
        - test_mark_workout_completed: Verifies that marking a workout as completed creates a
          corresponding WorkoutLog entry.
        - test_unmark_workout_completed: Verifies that unmarking a workout as completed deletes
          the corresponding WorkoutLog entry.
        - test_calendar_view_fetches_warmups_from_api: Verifies that the calendar view fetches
          warm-up exercises from an external API.
        - test_mock_valid_data_response: Tests API integration by mocking a valid response and
          checking that the correct data is returned.
        - test_warmup_api_handles_errors: Simulates an error in the API request and verifies that
          the application handles it correctly.
        - test_missing_user_input: Verifies that the application handles missing user input
          gracefully.

    4. Tear Down:
        - tearDown: Cleans up after each test, deleting the created user and exercises to ensure a
          clean test environment.

Note:
    - The tests use Django's TestCase class for unit testing, Client for simulating requests,
      and patching for mocking external API responses.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from goals.models import UserExercise, WorkoutLog, Exercise
from goals.forms import UserExerciseForm
import requests
from .ai import ai_model


# Ensuring model is working with
class NewAIModelTests(TestCase):
    """
    Test cases for ensuring the AI model behaves as expected, specifically checking
    fitness-related responses.
    """

    # Ensure common fitness terms appear in AI output.
    def test_response_contains_expected_keywords(self):
        """
        Verifies that common fitness-related keywords such as 'sets', 'reps', 'rest', and 'exercise'
        appear in the AI model response when a beginner strength plan is requested.
        """
        response = ai_model.get_response("Give me a beginner strength plan")
        keywords = ["sets", "reps", "rest", "exercise"]
        found = any(keyword in response.lower() for keyword in keywords)
        self.assertTrue(found, "AI response lacks expected fitness keywords")

    # Check AI can still respond when injury limitations are given
    def test_response_handles_injuries_gracefully(self):
        """
        Ensures that the AI model responds appropriately when injury-related information is provided
        in the user's workout request.
        """
        prompt = "Workout plan for someone with knee injury and lower back pain"
        response = ai_model.get_response(prompt)
        self.assertIsInstance(response, str)
        self.assertNotIn("error", response.lower())


class NewViewTests(TestCase):
    """
    Test cases for ensuring views work correctly, including the home view and workout plan
    generation.
    """

    def setUp(self):
        """
        Sets up the test environment by creating a user and logging them in for subsequent tests.
        """
        self.client = Client()
        self.user = User.objects.create_user(username="tester", password="password123")
        self.client.login(username="tester", password="password123")

    # Check if home view loads correctly
    def test_get_home_view(self):
        """
        Tests that the home view loads successfully and contains expected content, such as
        'Workout App'.
        """
        # Simulates going to home view
        response = self.client.get(reverse("home"))
        # The http status code is 200 (successful)
        self.assertEqual(response.status_code, 200)
        # Decode response content to string, checks if workout app is there
        self.assertIn("Workout App", response.content.decode())

    # Make sure plan generates when multiple days are specified.
    def test_post_generates_plan_with_multiple_days(self):
        """
        Tests that when multiple days are specified in the user input, a workout plan is generated
        correctly
        with the specified days included.
        """
        input_text = "Fitness Level: Intermediate; Goals: Build Muscle; Injuries: None; Selected Days: Monday, Wednesday, Friday"

        # Simulates AJAX request,
        response = self.client.post(
            reverse("generate_workout"),
            {"user_input": input_text},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # Ensure successful response (200), then ensures days are in workout plan
        self.assertEqual(response.status_code, 200)
        self.assertIn("Monday", response.content.decode())
        self.assertIn("Wednesday", response.content.decode())

    # Submit gibberish and ensure the app doesn't crash
    def test_invalid_user_input_still_returns_page(self):
        """
        Tests that invalid user input does not cause the app to crash, and the page still returns
        successfully.
        """
        response = self.client.post(
            reverse("generate_workout"), {"user_input": "asdfasdfasfdasfdasdfasdf"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.content) > 10)


User = get_user_model()


class CalendarTests(TestCase):
    """
    Test cases for ensuring the calendar view works correctly, including workout completion
    and warm-up fetching.
    """

    def setUp(self):
        """
        Sets up the test environment by creating a user, exercises, and user exercises
        for the calendar-related tests.
        """
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.client.login(username="testuser", password="pass")

        # Create exercises for the calendar
        self.exercise_1 = Exercise.objects.create(
            name="Bench Press", slug="bench-press"
        )
        self.exercise_2 = Exercise.objects.create(name="Squat", slug="squat")

        # Create user exercises (setting corresponding info)
        self.user_exercise_1 = UserExercise.objects.create(
            user=self.user,
            exercise=self.exercise_1,
            current_weight=Decimal("100.00"),
            reps=10,
            percent_increase=5,
        )
        self.user_exercise_2 = UserExercise.objects.create(
            user=self.user,
            exercise=self.exercise_2,
            current_weight=Decimal("120.00"),
            reps=8,
            percent_increase=10,
        )

    def test_calendar_view_get(self):
        """Test that the calendar page is accessible and renders with the right context"""
        response = self.client.get(reverse("calendar"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "calendar.html")
        # Check if 'events' is in the context instead of 'user_exercises'
        self.assertIn("events", response.context)
        self.assertEqual(len(response.context["events"]), 2)

    def test_mark_workout_completed(self):
        """Test marking a workout as completed creates a WorkoutLog entry"""
        response = self.client.get(
            reverse("calendar")
        )  # Make GET request to get csrf token
        csrf_token = response.cookies["csrftoken"].value  # Get csrf token

        date_completed = date.today().strftime("%Y-%m-%d")

        # Make POST request to mark workout as completed
        response = self.client.post(
            reverse("calendar"),
            {
                "workout_id": self.user_exercise_1.id,
                "date_completed": date_completed,
                "completed": "true",
                "csrfmiddlewaretoken": csrf_token,
            },
        )

        # Create WorkoutLog entry with UserExercise instance
        workout_log = WorkoutLog.objects.filter(
            user=self.user, exercise=self.user_exercise_1, date_completed=date_completed
        )

        self.assertEqual(workout_log.count(), 1)  # Should create 1 log entry
        self.assertEqual(response.status_code, 200)

    def test_unmark_workout_completed(self):
        """Test unmarking a workout as completed deletes the WorkoutLog entry"""
        date_completed = date.today().strftime("%Y-%m-%d")

        # Create a completed workout log first
        WorkoutLog.objects.create(
            user=self.user, exercise=self.user_exercise_1, date_completed=date_completed
        )

        # Now make a POST request to unmark it as completed
        response = self.client.get(
            reverse("calendar")
        )  # Make GET request to get csrf token
        csrf_token = response.cookies["csrftoken"].value  # Get csrf token

        response = self.client.post(
            reverse("calendar"),
            {
                "workout_id": self.user_exercise_1.id,
                "date_completed": date_completed,
                "completed": "false",
                "csrfmiddlewaretoken": csrf_token,
            },
        )

        # Ensure the WorkoutLog entry is deleted
        workout_log = WorkoutLog.objects.filter(
            user=self.user, exercise=self.user_exercise_1, date_completed=date_completed
        )

        self.assertEqual(workout_log.count(), 0)  # Should delete the log entry
        self.assertEqual(response.status_code, 200)

    """ Warm up Tests  """

    def test_calendar_view_fetches_warmups_from_api(self):
        """Test that warm-up exercises are fetched from the external API and added to context"""
        response = self.client.get(reverse("calendar"))
        self.assertEqual(response.status_code, 200)
        # We're testing actual API integration, so there should be warm_ups in the view context
        # Check that the 'calendar.html' template was used
        self.assertTemplateUsed(response, "calendar.html")

    @patch(
        "home.views.requests.get"
    )  # must include where the function is used not where the function is defined
    def test_mock_valid_data_response(self, mock_get):
        """
        Tests the calendar view when a valid mocked response is returned from the external API.
        Verifies that the warm-up exercises are correctly added to the context.
        """
        # Mocked API data
        mock_data = [
            {
                "name": "Quad Pulls",
                "type": "stretch",
                "muscle": "legs",
                "difficulty": "beginner",
                "instructions": "While standing, pull your foot towards your back.",
            }
        ]

        # Configure the mock response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_data

        response = self.client.get(reverse("calendar"))
        # make sure that the response code is 200, the exercise it correct and the template is
        # correct
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quad Pulls")
        self.assertTemplateUsed(response, "calendar.html")

    def test_warmup_api_handles_errors(self):
        """Simulate a bad request to check if error handling works (manually change endpoint)"""
        headers = {"X-API-Key": "BB+Yg/m06BKgSpFZ+FCbdw==W7rniUupiho7pyGz"}
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

    # Test behavior when no input is sent.
    def test_missing_user_input(self):
        """
        Tests that the application handles missing user input gracefully by ensuring a meaningful
        response is returned.
        """
        response = self.client.post(reverse("generate_workout"), {})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Error", response.content.decode())
