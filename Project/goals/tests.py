# tests.py
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from .models import UserExercise, Exercise
from .forms import UserExerciseForm
import datetime

User = get_user_model()

class ModelsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.exercise = Exercise.objects.create(name='Bench Press', slug='bench-press')

    def test_goal_weight_calculation(self):
        """
        Test that the goal_weight property calculates the weight correctly.
        """
        user_exercise = UserExercise.objects.create(
            user=self.user,
            exercise=self.exercise,
            current_weight=Decimal('100.00'),
            reps=10,
            percent_increase=5,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=30),
            recurring_day=0
        )
        expected = Decimal('100.00') * (Decimal('1') + Decimal('5') / Decimal('100'))
        self.assertEqual(user_exercise.goal_weight, expected)

class FormsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.exercise = Exercise.objects.create(name='Squat', slug='squat')

    def test_valid_user_exercise_form(self):
        """
        Test that a valid form passes validation.
        """
        form_data = {
            'exercise': self.exercise.id,
            'current_weight': '150.00',
            'reps': 8,
            'percent_increase': 10,
            'start_date': str(datetime.date.today()),
            'end_date': str(datetime.date.today() + datetime.timedelta(days=30)),
            'recurring_day': '0',
        }
        form = UserExerciseForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_negative_current_weight(self):
        """
        Test that a negative current_weight value raises a validation error.
        """
        form_data = {
            'exercise': self.exercise.id,
            'current_weight': '-50.00',
            'reps': 8,
            'percent_increase': 10,
            'start_date': str(datetime.date.today()),
            'end_date': str(datetime.date.today() + datetime.timedelta(days=30)),
            'recurring_day': '0',
        }
        form = UserExerciseForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('current_weight', form.errors)

    def test_invalid_missing_exercise(self):
        """
        Test that omitting the exercise field raises a validation error.
        """
        form_data = {
            # 'exercise' omitted to trigger clean_exercise validation
            'current_weight': '150.00',
            'reps': 8,
            'percent_increase': 10,
            'start_date': str(datetime.date.today()),
            'end_date': str(datetime.date.today() + datetime.timedelta(days=30)),
            'recurring_day': '0',
        }
        form = UserExerciseForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('exercise', form.errors)

    def test_start_date_after_end_date(self):
        """
        Ensure form validation fails when start_date is after end_date.
        """
        form_data = {
            'exercise': self.exercise.id,
            'current_weight': '150.00',
            'reps': 8,
            'percent_increase': 10,
            'start_date': str(datetime.date.today() + datetime.timedelta(days=10)),
            'end_date': str(datetime.date.today()),
            'recurring_day': '1',
        }
        form = UserExerciseForm(data=form_data)
        self.assertFalse(form.is_valid())
        # The cross‑field clean() puts this message into non_field_errors()
        self.assertIn(
            "Start date cannot be after end date.",
            form.non_field_errors()
        )

    def test_invalid_recurring_day(self):
        """
        Ensure form validation fails for out-of-range recurring_day values.
        """
        form_data = {
            'exercise': self.exercise.id,
            'current_weight': '150.00',
            'reps': 8,
            'percent_increase': 10,
            'start_date': str(datetime.date.today()),
            'end_date': str(datetime.date.today() + datetime.timedelta(days=30)),
            'recurring_day': '7',  # Invalid; assuming 0 (Mon) to 6 (Sun)
        }
        form = UserExerciseForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('recurring_day', form.errors)

    def test_model_accepts_valid_date_range(self):
        """
        Ensure the model can store valid date ranges and recurring days.
        """
        user_ex = UserExercise.objects.create(
            user=self.user,
            exercise=self.exercise,
            current_weight=Decimal('120.00'),
            reps=6,
            percent_increase=5,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=45),
            recurring_day=3  # Thursday
        )
        self.assertEqual(user_ex.recurring_day, 3)
        self.assertLess(user_ex.start_date, user_ex.end_date)

class ViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client.login(username='testuser', password='pass')
        self.exercise = Exercise.objects.create(name='Deadlift', slug='deadlift')
        self.user_exercise = UserExercise.objects.create(
            user=self.user,
            exercise=self.exercise,
            current_weight=Decimal('200.00'),
            reps=5,
            percent_increase=10,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=30),
            recurring_day=0
        )

    def test_goals_view_requires_login(self):
        """
        Ensure that the goals view requires a logged in user.
        """
        self.client.logout()
        url = reverse('goals:goals')
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_goals_view(self):
        """
        Test that the goals view returns a 200 and includes the expected context.
        """
        url = reverse('goals:goals')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('exercises', response.context)
        self.assertEqual(len(response.context['exercises']), 1)

    def test_my_exercises_view_requires_login(self):
        self.client.logout()
        url = reverse('goals:my_exercises')
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_my_exercises_view(self):
        """
        Test that my_exercises view returns the correct exercise list.
        """
        url = reverse('goals:my_exercises')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('exercises', response.context)
        self.assertEqual(len(response.context['exercises']), 1)

    def test_delete_exercise_view_requires_login(self):
        self.client.logout()
        url = reverse('goals:delete_exercise', kwargs={'pk': self.user_exercise.pk})
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_delete_exercise_view_get(self):
        """
        Test that the GET request to the delete_exercise view renders the confirmation page.
        """
        url = reverse('goals:delete_exercise', kwargs={'pk': self.user_exercise.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'goals/confirm_delete.html')
        self.assertContains(response, self.user_exercise.exercise.name)

    def test_delete_exercise_view_post(self):
        """
        Test that a POST request to delete_exercise successfully deletes the entry.
        """
        url = reverse('goals:delete_exercise', kwargs={'pk': self.user_exercise.pk})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('goals:my_exercises'))
        self.assertFalse(UserExercise.objects.filter(pk=self.user_exercise.pk).exists())

    def test_delete_exercise_view_invalid_pk(self):
        """
        Test that accessing delete_exercise view with an invalid pk returns 404.
        """
        invalid_pk = self.user_exercise.pk + 999  # an ID that does not exist
        url = reverse('goals:delete_exercise', kwargs={'pk': invalid_pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_set_exercises_view_requires_login(self):
        self.client.logout()
        url = reverse('goals:set_exercises')
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

    def test_set_exercises_view_get(self):
        """
        Test that the GET request to set_exercises returns the formset.
        """
        url = reverse('goals:set_exercises')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('formset', response.context)

    def test_set_exercises_view_post_empty(self):
        """
        Test posting an empty formset to set_exercises.
        Since extra=0, no new forms are submitted and the view should redirect.
        """
        url = reverse('goals:set_exercises')
        data = {
            'form-TOTAL_FORMS': '0',
            'form-INITIAL_FORMS': '0',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('goals:my_exercises'))

    def test_set_exercises_view_post_valid(self):
        """
        Test posting a valid formset to set_exercises creates a new exercise.
        """
        url = reverse('goals:set_exercises')
        new_exercise = Exercise.objects.create(name='Overhead Press', slug='overhead-press')
        data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-0-exercise': str(new_exercise.id),
            'form-0-current_weight': '75.00',
            'form-0-reps': '8',
            'form-0-percent_increase': '5',
            'form-0-start_date': str(datetime.date.today()),
            'form-0-end_date': str(datetime.date.today() + datetime.timedelta(days=30)),
            'form-0-recurring_day': '1',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('goals:my_exercises'))
        self.assertEqual(UserExercise.objects.filter(user=self.user, exercise=new_exercise).count(), 1)

    def test_set_exercises_view_post_invalid(self):
        """
        Test posting an invalid formset (e.g., negative weight) to set_exercises does not create an exercise.
        """
        url = reverse('goals:set_exercises')
        invalid_exercise = Exercise.objects.create(name='Curl', slug='curl')
        data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-0-exercise': str(invalid_exercise.id),
            'form-0-current_weight': '-100.00',  # invalid: negative weight
            'form-0-reps': '10',
            'form-0-percent_increase': '5',
            'form-0-start_date': str(datetime.date.today()),
            'form-0-end_date': str(datetime.date.today() + datetime.timedelta(days=30)),
            'form-0-recurring_day': '1',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Current weight cannot be negative")
        self.assertEqual(UserExercise.objects.filter(user=self.user, exercise=invalid_exercise).count(), 0)

class GoalsViewNoProfileTests(TestCase):
    """
    Test the goals view when the user does not have an associated userprofile.
    """
    def setUp(self):
        self.client = Client()
        self.user_no_profile = User.objects.create_user(username='noprofile', password='pass')
        self.client.login(username='noprofile', password='pass')
        exercise = Exercise.objects.create(name='Row', slug='row')
        self.user_exercise = UserExercise.objects.create(
            user=self.user_no_profile,
            exercise=exercise,
            current_weight=Decimal('120.00'),
            reps=10,
            percent_increase=5,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=30),
            recurring_day=0
        )

    def test_goals_view_without_profile(self):
        url = reverse('goals:goals')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Convert user_goals to a list for comparison, accommodating both [] and an empty QuerySet.
        self.assertEqual(list(response.context.get('user_goals', [])), [])
        self.assertEqual(len(response.context['exercises']), 1)

class ModelStrTests(TestCase):
    """
    Test the __str__ methods of models.
    """
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.exercise = Exercise.objects.create(name='Bench Press', slug='bench-press')
        self.user_exercise = UserExercise.objects.create(
            user=self.user,
            exercise=self.exercise,
            current_weight=Decimal('100.00'),
            reps=10,
            percent_increase=5,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=30),
            recurring_day=0
        )

    def test_exercise_str(self):
        self.assertEqual(str(self.exercise), 'Bench Press')

    def test_user_exercise_str(self):
        expected_str = (
            f"{self.user.username} - {self.exercise.name} "
            f"(Every {self.user_exercise.get_recurring_day_display()} "
            f"from {self.user_exercise.start_date} to {self.user_exercise.end_date})"
        )
        self.assertEqual(str(self.user_exercise), expected_str)
