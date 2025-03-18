from django.test import TestCase, Client
from .ai import ai_model
from django.urls import reverse


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

