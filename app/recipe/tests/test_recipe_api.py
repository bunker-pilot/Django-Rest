"""
Tests for the recipe api
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer
import tempfile
import os
from PIL import Image

RECIPES_URL = reverse("recipe:recipe-list")


def image_upload_url(recipe_id):
    """Craete and return an image upload url"""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def detail_url(recipe_id):
    """Create and return a recipe detail URL"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_recipe(user, **kwargs):
    """Create and return a sample recipe"""
    defaults = {
        "title": "sample title",
        "time_minutes": 5,
        "price": Decimal("5.50"),
        "description": "A recipe for your recipe",
        "link": "https://www.shitman.com",
    }
    defaults.update(kwargs)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


class PublicRecipeApiTests(TestCase):
    """Uauthenticated user tests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth required to use api"""

        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated api requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="shitman@example.com", password="shitman"
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by("-id")

        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited only to the authenticated user"""
        other_user = get_user_model().objects.create_user(
            email="who@example.com", password="who12345"
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test getting recipe detail"""

        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)

        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe"""

        payload = {
            "title": "sample recipe",
            "time_minutes": 30,
            "price": Decimal("9.99"),
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(pk=res.data["id"])

        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe"""

        original_link = "www.example.com"
        recipe = create_recipe(
            user=self.user, title="sample bitch", link=original_link
        )  # noqa
        payload = {"title": "Haji inn car mikone?"}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.user, self.user)
        self.assertEqual(recipe.link, original_link)

    def test_full_update(self):
        """Test full update for recipe(recreating a new object)"""
        recipe = create_recipe(
            user=self.user,
            title="Sample title",
            link="somehting.pd",
            description="A sad life",
        )

        payload = {
            "title": "A new sad life",
            "link": "sjaoijfij.sadge",
            "description": "another sad life BUT with a cat :(",
            "price": Decimal("9.99"),
            "time_minutes": 10,
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe"""

        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_change_recipe_user(self):
        """Test changing recipe user returns error."""
        recipe = create_recipe(user=self.user)
        new_user = get_user_model().objects.create(
            email="shitman2@example.com", password="shitman212324"
        )
        payload = {"user": new_user.id}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(
            res.status_code, status.HTTP_200_OK
        )  # why does it return 200 ?!!
        self.assertEqual(recipe.user, self.user)

    def test_recipe_with_new_tags(self):
        """Test creating a recipe with new tags"""

        payload = {
            "title": "A sample",
            "time_minutes": 10,
            "price": Decimal("9.99"),
            "tags": [{"name": "desert"}, {"name": "Thao"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            exists = recipe.tags.filter(
                name=tag["name"], user=self.user
            ).exists()  # noqa
            self.assertTrue(exists)

    def test_creating_recipe_with_existing_tags(self):
        """Test creting recipe with existing tags"""
        tag_sample = Tag.objects.create(name="sample", user=self.user)
        payload = {
            "title": "sample recipe",
            "time_minutes": 10,
            "price": Decimal("9.89"),
            "tags": [{"name": "sample"}, {"name": "desert"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)

        self.assertIn(tag_sample, recipe.tags.all())

        for tag in payload["tags"]:
            exists = recipe.tags.filter(
                user=self.user, name=tag["name"]
            ).exists()  # noqa
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating a tag when updating a recipe"""

        recipe = create_recipe(user=self.user)

        payload = {"tags": [{"name": "desert"}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(user=self.user, name="desert")

        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_asign_tags(self):
        """Test asigning an existing tag when creating a recipe"""

        recipe = create_recipe(user=self.user)
        tag_desert = Tag.objects.create(user=self.user, name="desert")
        recipe.tags.add(tag_desert)

        tag_pashmak = Tag.objects.create(user=self.user, name="pashmak")
        payload = {"tags": [{"name": "pashmak"}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn(tag_pashmak, recipe.tags.all())

        self.assertNotIn(tag_desert, recipe.tags.all())

    def test_clear_recipe_tegs(self):
        """Test clearing a recipe's Tags"""

        recipe = create_recipe(user=self.user)

        tag = Tag.objects.create(user=self.user, name="Desert")
        recipe.tags.add(tag)
        payload = {"tags": []}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """Test creting recipe with new ingredients"""
        payload = {
            "title": "A sample recipe",
            "time_minutes": 10,
            "price": Decimal("10.99"),
            "ingredients": [{"name": "Celery"}, {"name": "Vanilla"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]

        self.assertEqual(recipe.ingredients.count(), 2)

        for ingredient in payload["ingredients"]:
            exists = Ingredient.objects.filter(
                name=ingredient["name"], user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        """Test craeting recipes with existing ingredients"""

        ingredient = Ingredient.objects.create(name="celery", user=self.user)

        payload = {
            "title": "A sample recipe",
            "time_minutes": 10,
            "price": Decimal("5.44"),
            "ingredients": [{"name": "celery"}, {"name": "Vanilla"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]

        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload["ingredients"]:
            exists = Ingredient.objects.filter(
                name=ingredient["name"], user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """Test creating an ingredient when updating a recipe"""

        recipe = create_recipe(user=self.user)
        payload = {"ingredients": [{"name": "celery"}]}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_ingredient = Ingredient.objects.get(name="celery", user=self.user)
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_asign_ingredient(self):
        """Test asigning an existing ingredient when updating a recipe"""

        ingredient = Ingredient.objects.create(user=self.user, name="Vanilla")
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        ingredient2 = Ingredient.objects.create(user=self.user, name="Celery")
        payload = {"ingredients": [{"name": "Celery"}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        """Test clearing a recipe's ingredients"""
        ingredient = Ingredient.objects.create(name="Celery", user=self.user)
        recipe = create_recipe(user=self.user)

        recipe.ingredients.add(ingredient)

        payload = {"ingredients": []}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(recipe.ingredients.count(), 0)


class ImageUploadTests(TestCase):
    """Tests for the image upload API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="example@example.com", password="shitman"
        )
        self.client.force_authenticate(user=self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(url, payload, format="multipart")
        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image"""
        url = image_upload_url(self.recipe.id)

        payload = {"imag": "somthingf"}

        res = self.client.post(url, payload, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
