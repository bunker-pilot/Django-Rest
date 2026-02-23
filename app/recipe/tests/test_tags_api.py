"""
Tests for the tags api
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from core.models import Tag

from recipe.serializers import TagSerializer

TAGS_URL = reverse("recipe:tag-list")


def create_user(email="shitman@example.com", password="shitman"):
    """Create and return a user"""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagApiTests(TestCase):
    """Test unauthenricated user"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_reuqired(self):
        """Test authentication is required"""

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagApiTests(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags"""

        Tag.objects.create(user=self.user, name="sample")
        Tag.objects.create(user=self.user, name="Desert")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")

        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to the current user"""

        new_user = create_user(email="who@example.com", password="shitman")

        Tag.objects.create(user=new_user, name="Ajab")
        tag = Tag.objects.create(user=self.user, name="Sample")

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)

        self.assertEqual(res.data[0]["id"], tag.id)
