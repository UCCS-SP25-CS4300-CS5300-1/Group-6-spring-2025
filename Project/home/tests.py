from django.test import TestCase, Client
from django.urls import reverse
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
        """Check AI can still respond when injury limitations are given."""
        prompt = "Workout plan for someone with knee injury and lower back pain"
        response = ai_model.get_response(prompt)
        self.assertIsInstance(response, str)
        self.assertNotIn("error", response.lower())


class NewViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    #Check if home view loads correctly
    def test_get_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Workout App", response.content.decode())

    #Make sure plan generates when multiple days are specified.
    def test_post_generates_plan_with_multiple_days(self):
        input_text = "Fitness Level: Intermediate; Goals: Build Muscle; Injuries: None; Selected Days: Monday, Wednesday, Friday"
        response = self.client.post(
            reverse('generate_workout'),
            {'user_input': input_text},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
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

    #Test behavior when no input is sent.
    def test_missing_user_input(self):
        response = self.client.post(reverse('generate_workout'), {})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Error", response.content.decode())
