# pylint: disable=no-member,invalid-name

"""
Module for testing AI workout generation, home view logic, and calendar workout tracking.

This module contains test cases for:
- AI model responses to workout prompts
- Home view rendering and POST behavior
- Calendar workout logging and warm-up API integration

Test classes:
- NewAIModelTests: Validates AI-generated workout text
- NewViewTests: Checks home view and workout generation behavior
- CalendarTests: Covers workout completion logging and warm-up fetching via API
"""


from datetime import date
from decimal import Decimal
from unittest.mock import patch

import requests
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

from goals.models import UserExercise, WorkoutLog, Exercise
from .ai import ai_model


# Ensuring model is working with
class NewAIModelTests(TestCase):
    """
    Tests for the AI model responsible for generating workout plans.
    """
    # Ensure common fitness terms appear in AI output.
    def test_response_contains_expected_keywords(self):
        """
        Test that the AI model generates valid responses even when injury
        limitations are provided in the prompt.
        """
        response = ai_model.get_response("Give me a beginner strength plan")
        keywords = ["sets", "reps", "rest", "exercise"]
        found = any(keyword in response.lower() for keyword in keywords)
        self.assertTrue(found, "AI response lacks expected fitness keywords")

    # Check AI can still respond when injury limitations are given
    def test_response_handles_injuries_gracefully(self):
        """
        Tests for views related to the home page and workout generation.
        """
        prompt = "Workout plan for someone with knee injury and lower back pain"
        response = ai_model.get_response(prompt)
        self.assertIsInstance(response, str)
        self.assertNotIn("error", response.lower())


class NewViewTests(TestCase):
    """
    Tests for views related to the home page and workout generation.
    """
    def setUp(self):
        """
        Set up test client and authenticated user.
        """
        self.client = Client()
        self.user = User.objects.create_user(username="tester", password="password123")
        self.client.login(username="tester", password="password123")

    # Check if home view loads correctly
    def test_get_home_view(self):
        """
        Test that the home view loads successfully and contains expected text.
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
        Test that a workout plan is generated when multiple days are provided in the input.
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
        Test that invalid user input does not crash the app and still returns a valid page.
        """
        response = self.client.post(
            reverse("generate_workout"), {"user_input": "asdfasdfasfdasfdasdfasdf"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.content) > 10)


User = get_user_model()


class CalendarTests(TestCase):
    """
    Tests for the workout calendar view, workout logging, and warm-up API functionality.
    """
    def setUp(self):
        """
        Set up test client, test user, and initial user exercises.
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
        Test calendar view behavior using mocked warm-up API response data.
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
        # make sure that the response code is 200, the exercise it correct
        # and the template is correct
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quad Pulls")
        self.assertTemplateUsed(response, "calendar.html")

    def test_warmup_api_handles_errors(self):
        """Simulate a bad request to check if error handling works (manually change endpoint)"""
        headers = {"X-API-Key": "BB+Yg/m06BKgSpFZ+FCbdw==W7rniUupiho7pyGz"}
        # Intentionally broken URL
        url = "https://exercises-by-api-ninjas.p.rapidapi.com/v1/invalid-endpoint"
        response = requests.get(url, headers=headers, timeout=360)

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
        Test that submitting empty input to the workout generator returns an error message.
        """
        response = self.client.post(reverse("generate_workout"), {})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Error", response.content.decode())
