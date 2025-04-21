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
          # Mock API response for warm-ups
        self.mock_warmup_data = [
            {
                "name": "Hamstring Stretch",
                "type": "stretching",
                "muscle": "Hamstrings",
                "difficulty": "beginner",
                "instructions": "Sit and extend legs."
            },
            {
                "name": "Shoulder Stretch",
                "type": "stretching",
                "muscle": "Shoulders",
                "difficulty": "beginner",
                "instructions": "Pull arm across body."
            },
            {
                "name": "Calf Stretch",
                "type": "stretching",
                "muscle": "Calves",
                "difficulty": "beginner",
                "instructions": "Lean against wall."
            }
        ]

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
    @patch('home.views.requests.get')
    def test_calendar_view_fetches_warmups_with_workout(self, mock_get):
        """Test that warm-up exercises are fetched when a workout exists for today"""
        today = timezone.now().date()
        UserExercise.objects.create(
            user=self.user,
            exercise=self.exercise_1,
            start_date=today - datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=1),
            recurring_day=today.weekday()
        )

        # Configure mock response
        mock_get.return_value = Mock(status_code=200)
        mock_get.return_value.json.return_value = self.mock_warmup_data

        response = self.client.get(reverse('calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')
        self.assertEqual(len(response.context['warm_ups']), 3)
        self.assertContains(response, 'Hamstring Stretch')
        self.assertContains(response, 'Shoulder Stretch')
        self.assertContains(response, 'Calf Stretch')
        mock_get.assert_called_with(
            "https://api.api-ninjas.com/v1/exercises?type=stretching",
            headers={"X-API-Key": "BB+Yg/m06BKgSpFZ+FCbdw==W7rniUupiho7pyGz"}
        )

    def test_calendar_view_no_warmups_without_workout(self):
        """Test that no warm-ups are fetched when no workout exists for today"""
        # No UserExercise for today
        response = self.client.get(reverse('calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')
        self.assertEqual(response.context['warm_ups'], [])
        self.assertContains(response, 'No warm-up exercises available')

    @patch('home.views.requests.get')
    def test_calendar_view_handles_api_error(self, mock_get):
        """Test that warm-up section handles API errors gracefully"""
        today = timezone.now().date()
        UserExercise.objects.create(
            user=self.user,
            exercise=self.exercise_1,
            start_date=today - datetime.timedelta(days=1),
            end_date=today + datetime.timedelta(days=1),
            recurring_day=today.weekday()
        )

        # Simulate API failure
        mock_get.side_effect = Exception('API Error')

        response = self.client.get(reverse('calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'calendar.html')
        self.assertEqual(response.context['warm_ups'], [])
        self.assertContains(response, 'No warm-up exercises available')

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
