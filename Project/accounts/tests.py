# pylint: disable=E1101, W0611, E0611, E0401, C0103
"""
Test module for user friendship functionalities in the application.

This module contains a set of tests to verify the behavior of various friendship-related views,
including adding/removing friends, viewing the friend list, searching for friends, and accessing
friend data. The tests ensure that only valid friendships allow access to certain data and that
friendship actions such as removal and search behave as expected.

Tests include:
- Removing friends and ensuring the relationship is deleted.
- Viewing a user's friend list and verifying the context contains friends.
- Searching for friends while ensuring only non-friends are returned in the results.
- Accessing friend data when a valid friendship exists and ensuring restrictions are
enforced for non-friends.

Each test verifies the integrity of the friendship features and ensures the correct user experience
in the context of friendship management.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from .models import UserProfile, Goal, Injury, FriendRequest
from .forms import UserRegistrationForm, UserProfileUpdateForm


class UserProfileModelTests(TestCase):
    """
    Test suite for the UserProfile model and its related features.
    """

    def setUp(self):
        """
        Set up a test user for UserProfile-related tests.
        """
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )

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
        profile.bmi = weight_kg / (height_m**2) if height_m > 0 else None
        profile.save()

        expected_bmi = weight_kg / (height_m**2)
        self.assertAlmostEqual(profile.bmi, expected_bmi, places=2)

    def test_many_to_many_relationships(self):
        """Ensure goals and injuries can be added to a UserProfile."""
        goal = Goal.objects.create(
            name="Build Strength", description="Increase muscle mass"
        )
        injury = Injury.objects.create(
            name="Knee Injury", description="Previous ACL tear"
        )

        profile = self.user.userprofile
        profile.goals.add(goal)
        profile.injury_history.add(injury)

        self.assertIn(goal, profile.goals.all())
        self.assertIn(injury, profile.injury_history.all())


class UserAuthenticationTests(TestCase):
    """
    Test suite for user registration, login, and logout views.
    """

    def setUp(self):
        """
        Set up a test client and user for authentication tests.
        """

        self.client = Client(enforce_csrf_checks=False)  # Disable CSRF for testing
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )

    def test_register_view(self):
        """Ensure users can register successfully."""
        register_url = reverse("register")
        print(f"Register URL: {register_url}")  # Debugging URL resolution

        response = self.client.post(
            register_url,
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpassword",
            },
        )

        self.assertEqual(response.status_code, 302)  # Expect redirect
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_login_view(self):
        """Ensure users can log in."""
        login_url = reverse("login")
        print(f"Login URL: {login_url}")  # Debugging URL resolution

        print(f"Users in DB: {User.objects.all()}")  # Ensure user exists
        response = self.client.post(
            login_url, {"username": "testuser", "password": "testpassword"}
        )

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
    """
    Test suite for updating user profile data through the update form.
    """

    def setUp(self):
        """
        Set up test client and log in a user for profile update tests.
        """

        self.client = Client(enforce_csrf_checks=False)  # Disable CSRF
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")

    def test_update_profile(self):
        """Ensure users can update their profile information."""
        goal = Goal.objects.create(name="Lose Weight", description="Cut fat percentage")
        injury = Injury.objects.create(
            name="Back Pain", description="Chronic lower back pain"
        )

        update_profile_url = reverse("update_profile")
        print(f"Update Profile URL: {update_profile_url}")  # Debugging URL resolution

        response = self.client.post(
            update_profile_url,
            {
                "height": "72",
                "weight": "180",
                "goals": [goal.id],
                "injury_history": [injury.id],
            },
        )

        self.assertEqual(response.status_code, 302)  # Expect redirect
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.height, 72)
        self.assertEqual(profile.weight, 180)
        self.assertIn(goal, profile.goals.all())
        self.assertIn(injury, profile.injury_history.all())


class FormTests(TestCase):
    """
    Test suite for validating custom form logic.
    """

    def test_user_registration_form(self):
        """Ensure the UserRegistrationForm validates input correctly."""
        form = UserRegistrationForm(
            data={
                "username": "testuser",
                "email": "test@example.com",
                "password": "securepassword",
            }
        )
        self.assertTrue(form.is_valid())

    def test_user_registration_form_invalid(self):
        """Ensure the UserRegistrationForm handles invalid input."""
        form = UserRegistrationForm(
            data={
                "username": "",  # Invalid username
                "email": "test@example.com",
                "password": "securepassword",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_user_profile_update_form(self):
        """Ensure the UserProfileUpdateForm works as expected."""
        form = UserProfileUpdateForm(
            data={"height": "70", "weight": "160", "fitness_level": "intermediate"}
        )
        self.assertTrue(form.is_valid())


# FRIENDS TESTS


class FriendRequestTestCase(TestCase):
    """
    Test suite for FriendRequest model functionality.
    """

    def setUp(self):
        """
        Create two users that we can use throughout our tests.
        """
        self.user1 = User.objects.create_user(
            username="User1", password="testpassword1"
        )
        self.user2 = User.objects.create_user(
            username="User2", password="testpassword2"
        )

    def test_friend_request_creation(self):
        """
        Test that a FriendRequest can be created and saved.
        """
        friend_request = FriendRequest.objects.create(
            from_user=self.user1, to_user=self.user2
        )
        self.assertIsNotNone(
            friend_request.id, "FriendRequest should have an ID after creation"
        )
        self.assertEqual(friend_request.from_user, self.user1)
        self.assertEqual(friend_request.to_user, self.user2)

    def test_str_representation(self):
        """
        Test the __str__ method of the FriendRequest model.
        """
        friend_request = FriendRequest.objects.create(
            from_user=self.user1, to_user=self.user2
        )
        expected_str = f"{self.user1.username} -> {self.user2.username}"
        self.assertEqual(str(friend_request), expected_str)


class FriendViewsTestCase(TestCase):
    """
    Ensure a FriendRequest can be created between two users.
    """

    def setUp(self):
        """
        Ensure the __str__ method returns a readable format.
        """

        self.client = Client()
        # Create two users. Assume that a signal creates a related userprofile automatically.
        self.user1 = User.objects.create_user(username="user1", password="password1")
        self.user2 = User.objects.create_user(username="user2", password="password2")
        # Clear any existing friends (if necessary)
        self.user1.userprofile.friends.clear()
        self.user2.userprofile.friends.clear()

    def test_profile_view_requires_login(self):
        """
        Verify that accessing the user data view without login redirects to login page.
        """
        url = reverse("user_data")
        response = self.client.get(url)
        # Expect a redirect to the login page for an unauthenticated user.
        self.assertNotEqual(response.status_code, 200)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    # def test_profile_view_with_search(self):
    #    self.client.login(username="user1", password="password1")
    # Create another user that should appear in search results.
    #    user3 = User.objects.create_user(username="searchuser", password="password3")
    #    url = reverse('user_data')
    #    response = self.client.get(url, {'q': 'search'})
    #    self.assertEqual(response.status_code, 200)
    # Check that the context contains the search query and results.
    #    self.assertIn('search_query', response.context)
    #    self.assertEqual(response.context['search_query'], 'search')
    #    self.assertIn('search_results', response.context)
    # The search should include user3 (since 'searchuser' contains "search")
    #    self.assertIn(user3, response.context['search_results'])
    # It should not include the logged-in user.
    #    self.assertNotIn(self.user1, response.context['search_results'])

    def test_send_friend_request(self):
        """
        Test that a friend request can be sent and duplicates are handled.
        """

        self.client.login(username="user1", password="password1")
        url = reverse("send_friend_request", args=[self.user2.id])
        # Send friend request the first time.
        response = self.client.get(url)
        fr = FriendRequest.objects.filter(
            from_user=self.user1, to_user=self.user2
        ).first()
        self.assertIsNotNone(fr)
        # Check that the view redirects to the expected URL.
        self.assertRedirects(response, reverse("user_data"))

        # Send the friend request a second time; it should not create a duplicate.
        response = self.client.get(url)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("already sent" in m.message for m in messages_list))

    def test_accept_friend_request(self):
        """
        Ensure accepting a friend request works and adds users to each other’s friend list.
        """

        # Create a friend request from user2 to user1.
        friend_request = FriendRequest.objects.create(
            from_user=self.user2, to_user=self.user1
        )
        self.client.login(username="user1", password="password1")
        url = reverse("accept_friend_request", args=[friend_request.id])
        response = self.client.get(url)
        # After accepting, the friend request should be deleted.
        self.assertFalse(FriendRequest.objects.filter(id=friend_request.id).exists())
        # And both users should now be friends (assuming a symmetrical relationship).
        self.assertIn(self.user2.userprofile, self.user1.userprofile.friends.all())
        self.assertIn(self.user1.userprofile, self.user2.userprofile.friends.all())
        self.assertRedirects(response, reverse("user_data"))

    def test_reject_friend_request(self):
        """
        Ensure rejecting a friend request deletes it and does not add users as friends.
        """

        friend_request = FriendRequest.objects.create(
            from_user=self.user2, to_user=self.user1
        )
        self.client.login(username="user1", password="password1")
        url = reverse("reject_friend_request", args=[friend_request.id])
        response = self.client.get(url)
        # The friend request should be deleted.
        self.assertFalse(FriendRequest.objects.filter(id=friend_request.id).exists())
        self.assertRedirects(response, reverse("user_data"))

    def test_remove_friend(self):
        """
        Test that a friendship can be removed and the friends are no longer connected.
        The friendship should be deleted from both user's friend lists.
        """
        # Set up a friendship between user1 and user2.
        self.user1.userprofile.friends.add(self.user2.userprofile)
        self.user2.userprofile.friends.add(self.user1.userprofile)
        self.client.login(username="user1", password="password1")
        url = reverse("remove_friend", args=[self.user2.id])
        response = self.client.get(url)
        # The friendship should be removed in both directions.
        self.assertNotIn(self.user2.userprofile, self.user1.userprofile.friends.all())
        self.assertNotIn(self.user1.userprofile, self.user2.userprofile.friends.all())
        self.assertRedirects(response, reverse("user_data"))

    def test_friend_list(self):
        """
        Test that the friend list is properly returned in the context when accessing the friend
        list page.
        """
        # Set up a friendship.
        self.user1.userprofile.friends.add(self.user2.userprofile)
        self.client.login(username="user1", password="password1")
        url = reverse("friend_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Verify that the context contains the friends list.
        self.assertIn("friends", response.context)
        self.assertIn(self.user2.userprofile, response.context["friends"])

    def test_friend_search(self):
        """
        Test the functionality of the friend search feature to ensure non-friends are included
        and friends are excluded.
        """
        # Create an extra user who is not a friend.
        user3 = User.objects.create_user(username="searchable", password="password3")
        # Establish a friendship with user2 (so that user2 is excluded).
        self.user1.userprofile.friends.add(self.user2.userprofile)
        self.client.login(username="user1", password="password1")
        url = reverse("friend_search")
        response = self.client.get(url, {"q": "search"})
        self.assertEqual(response.status_code, 200)
        # The search should return user3 (matching 'searchable') but exclude self and friends.
        results = response.context.get("search_results", [])
        self.assertIn(user3, results)
        self.assertNotIn(self.user2, results)  # user2 is already a friend
        self.assertNotIn(self.user1, results)  # self should be excluded

    def test_friend_data_allowed(self):
        """
        Test that a user can view a friend's data when a friendship exists.
        """

        # Establish friendship between user1 and user2.
        self.user1.userprofile.friends.add(self.user2.userprofile)
        self.user2.userprofile.friends.add(self.user1.userprofile)
        self.client.login(username="user1", password="password1")
        url = reverse("friend_data", args=[self.user2.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Check that the context contains the friend's profile.
        self.assertIn("user_profile", response.context)

    def test_friend_data_not_allowed(self):
        """
        Test that an error message is displayed if a user attempts to view data of someone
        who is not a friend.
        """

        # No friendship established between user1 and user2.
        self.client.login(username="user1", password="password1")
        url = reverse("friend_data", args=[self.user2.id])
        response = self.client.get(url)
        # Since user2 is not a friend, the view should add an error message and redirect.
        self.assertNotEqual(response.status_code, 200)
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any("not allowed" in m.message for m in messages_list))
