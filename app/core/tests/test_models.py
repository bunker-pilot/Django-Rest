from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from core import models


class ModelTests(TestCase):

    def test_create_user_successful(self):
        email = "test@example.com"
        password = "Test2121!"
        user = get_user_model().objects.create_user(
            email=email, password=password
        )  # noqa
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email normalized"""
        sample_emails = [
            ["test1@Example.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.com", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                email=email, password="test"
            )  # noqa
            self.assertEqual(user.email, expected)

    def test_new_user_without_user_error(self):
        """Test that creating a user without email raises a ValueError"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email="", password="test1234")

    def test_create_superuser(self):
        """Test craeting a superuser"""
        user = get_user_model().objects.create_superuser(
            "erfan@example.com", "shitman1234"
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_create_recipe(self):
        """Test creating a recipe"""
        user = get_user_model().objects.create_user(
            email="shitman@gmail.com", password="shitman"
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title="sample name",
            time_minutes=5,
            price=Decimal("5.50"),
            description="A simple meal",
        )
        self.assertEqual(str(recipe), recipe.title)
