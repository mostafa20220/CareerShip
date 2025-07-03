import json

from django.db import transaction
from django.test import TestCase
from .models import User, STUDENT, ADMIN, Skill, UserSkills
from django.db.utils import IntegrityError
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status


class UserModelTest(TestCase):
    """Test cases for the custom User model, covering creation, uniqueness, user type logic, optional fields, and more."""

    def setUp(self):
        """Set up a sample user for use in multiple tests."""
        self.user = User.objects.create(
            first_name='Omar',
            last_name='Khaled',
            email='omar@gmail.com',
            password='test123',
            user_type=STUDENT,
        )

    def test_create_user(self):
        """Test creating a user with required fields and check user type helpers."""
        self.assertEqual(self.user.email, 'omar@gmail.com')
        self.assertEqual(self.user.first_name, 'Omar')
        self.assertTrue(self.user.is_student())
        self.assertFalse(self.user.is_admin())

    def test_email_uniqueness(self):
        """Test that creating a user with a duplicate email raises an IntegrityError."""
        with self.assertRaises(IntegrityError):
            User.objects.create(
                first_name='Ahmed',
                last_name='Mohamed',
                email='omar@gmail.com',  # duplicate
                password='anotherpass',
                user_type=ADMIN,
            )

    def test_optional_fields(self):
        """Test creating a user with optional fields like phone and avatar."""
        user = User.objects.create(
            first_name='Mostafa',
            last_name='Ibrahim',
            email='mostafa@gmail.com',
            password='testpass',
            phone='+1234567890',
            avatar="https://gratisography.com/wp-content/uploads/2023/10/gratisography-headless-scarecrow-1170x780.jpg",
        )
        self.assertEqual(user.phone.as_e164, '+1234567890')
        self.assertEqual(user.avatar, "https://gratisography.com/wp-content/uploads/2023/10/gratisography-headless-scarecrow-1170x780.jpg")

    def test_str_method(self):
        """Test the string representation of the user returns the email."""
        self.assertEqual(str(self.user), 'omar@gmail.com')

    def test_user_type_switching(self):
        """Test switching the user type and the corresponding helper methods."""
        self.user.user_type = ADMIN
        self.user.save()
        self.assertTrue(self.user.is_admin())
        self.assertFalse(self.user.is_student())



    def test_premium_user(self):
        """Test creating a user with is_premium set to True."""
        user = User.objects.create(
            first_name='Salma',
            last_name='Hassan',
            email='salma@gmail.com',
            password='salmapass',
            is_premium=True,
        )
        self.assertTrue(user.is_premium)

    def test_google_and_github_ids(self):
        """Test creating a user with Google and GitHub IDs set."""
        user = User.objects.create(
            first_name='Karim',
            last_name='Fahmy',
            email='karim@gmail.com',
            password='karimpass',
            google_id='google-123',
            github_id='github-456',
        )
        self.assertEqual(user.google_id, 'google-123')
        self.assertEqual(user.github_id, 'github-456')

    def test_update_user_fields(self):
        """Test updating user fields and verifying persistence."""
        self.user.first_name = 'Omar-Updated'
        self.user.email = 'omar.updated@gmail.com'
        self.user.save()
        updated_user = User.objects.get(pk=self.user.pk)
        self.assertEqual(updated_user.first_name, 'Omar-Updated')
        self.assertEqual(updated_user.email, 'omar.updated@gmail.com')

    def test_required_fields_validation(self):
        """Test that missing required fields or empty email raises an error."""
        with self.assertRaises(TypeError):
            User.objects.create(password='noparams')  # missing required fields
        with self.assertRaises(ValueError):
            User.objects.create(
                first_name='Nada', last_name='Samir', email='', password='nopass'
            )  # empty email


class SkillModelTest(TestCase):
    """Test cases for the Skill model, covering creation and uniqueness."""

    def test_create_skill(self):
        """Test creating a skill with a unique name."""
        skill = Skill.objects.create(name='Python')
        self.assertEqual(skill.name, 'Python')

    def test_unique_skill_name(self):
        """Test that creating a skill with a duplicate name raises an IntegrityError."""
        Skill.objects.create(name='Django')
        with self.assertRaises(IntegrityError):
            Skill.objects.create(name='Django')  # duplicate name


class UserSkillsModelTest(TestCase):
    """Test cases for the UserSkills model, covering creation, uniqueness,
    and cascade delete behavior."""

    def setUp(self):
        """Set up a sample user and skill for use in multiple tests."""
        self.user = User.objects.create(
            first_name='Omar',
            last_name='Khaled',
            email='omar2@gmail.com',
            password='test123',
        )
        self.skill = Skill.objects.create(name='JavaScript')

    def test_create_user_skill(self):
        """Test creating a user-skill relationship."""
        user_skill = UserSkills.objects.create(user=self.user, skill=self.skill)
        self.assertEqual(user_skill.user, self.user)
        self.assertEqual(user_skill.skill, self.skill)

    def test_cascade_delete_user(self):
        """Test that deleting a user cascades and deletes related UserSkills."""
        user_skill = UserSkills.objects.create(user=self.user, skill=self.skill)
        self.user.delete()
        self.assertFalse(UserSkills.objects.filter(pk=user_skill.pk).exists())

    def test_cascade_delete_skill(self):
        """Test that deleting a skill cascades and deletes related UserSkills."""
        user_skill = UserSkills.objects.create(user=self.user, skill=self.skill)
        self.skill.delete()
        self.assertFalse(UserSkills.objects.filter(pk=user_skill.pk).exists())


class RegisterViewTest(APITestCase):
    """Test cases for the user registration endpoint."""

    def test_register_user(self):
        """Test registering a new user with valid data."""
        url = reverse('register')
        data = {
            'first_name': 'Omar',
            'last_name': 'Khaled',
            'email': 'omar3@gmail.com',
            'password': 'testpass123',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'omar3@gmail.com')
        self.assertEqual(response.data['first_name'], 'Omar')
        self.assertEqual(response.data['last_name'], 'Khaled')

    def test_register_user_password_mismatch(self):
        """Test registration fails if passwords do not match."""
        url = reverse('register')
        data = {
            'first_name': 'Omar',
            'last_name': 'Khaled',
            'email': 'omar4@gmail.com',
            'password1': 'testpass123',
            'password2': 'wrongpass',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', str(response.data).lower())

    def test_missing_first_name(self):
        """Test registration fails if first_name is missing."""
        url = reverse('register')
        data = {
            'last_name': 'Khaled',
            'email': 'missingfirst@gmail.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)

    def test_missing_last_name(self):
        """Test registration fails if last_name is missing."""
        url = reverse('register')
        data = {
            'first_name': 'Omar',
            'email': 'missinglast@gmail.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('last_name', response.data)

    def test_missing_email(self):
        """Test registration fails if email is missing."""
        url = reverse('register')
        data = {
            'first_name': 'Omar',
            'last_name': 'Khaled',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_missing_password1(self):
        """Test registration fails if password1 is missing."""
        url = reverse('register')
        data = {
            'first_name': 'Omar',
            'last_name': 'Khaled',
            'email': 'missingpass1@gmail.com',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_password2(self):
        """Test registration fails if password2 is missing."""
        url = reverse('register')
        data = {
            'first_name': 'Omar',
            'last_name': 'Khaled',
            'email': 'missingpass2@gmail.com',
            'password1': 'testpass123',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



class ProfileViewTest(APITestCase):
    """Test cases for the user profile endpoint (GET, PUT, PATCH, DELETE)."""

    def setUp(self):
        """Create and authenticate a user for profile tests."""
        self.user = User.objects.create(
            email='omar5@gmail.com',
            first_name='Omar',
            last_name='Khaled',
            password='testpass123',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        """Test retrieving the authenticated user's profile."""
        url = reverse('profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'omar5@gmail.com')

    def test_update_profile(self):
        """Test updating the user's profile with PUT."""
        url = reverse('profile')
        data = {
            'first_name': 'OmarUpdated',
            'last_name': 'Khaled',
            'email': 'omar5@gmail.com',
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'OmarUpdated')

    def test_partial_update_profile(self):
        """Test partially updating the user's profile with PATCH."""
        url = reverse('profile')
        data = {'first_name': 'OmarPatched'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'OmarPatched')

    def test_delete_profile(self):
        """Test deactivating the user's profile with DELETE."""
        url = reverse('profile')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)


class SkillsViewTest(APITestCase):
    """Test cases for the skills listing endpoint."""

    def setUp(self):
        """Create some skills for listing."""
        Skill.objects.create(name='Python')
        Skill.objects.create(name='Django')

    def test_list_skills(self):
        """Test retrieving the list of all skills."""
        url = reverse('skills-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Python')


class UserSkillsViewTest(APITestCase):
    """Test cases for the user skills endpoint (list, add, remove)."""

    def setUp(self):
        """Create a user and some skills, and authenticate the user."""
        self.user = User.objects.create(
            email='omar6@gmail.com',
            first_name='Omar',
            last_name='Khaled',
            password='testpass123',
        )
        self.skill = Skill.objects.create(name='JavaScript')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_user_skills(self):
        """Test retrieving the user's skills."""
        UserSkills.objects.create(user=self.user, skill=self.skill)
        url = reverse('user-skills-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['skill_name'], 'JavaScript')

    def test_add_user_skill(self):
        """Test adding a skill to the user."""
        url = reverse('user-skills-list')
        response = self.client.post(url, {'skill_id': self.skill.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detail'], 'Skill added.')
        # Check that a UserSkills object was created
        self.assertTrue(
            UserSkills.objects.filter(user=self.user, skill=self.skill).exists()
        )

    def test_add_existing_user_skill(self):
        """Test adding a skill that is already added returns an error."""
        UserSkills.objects.create(user=self.user, skill=self.skill)
        url = reverse('user-skills-list')
        response = self.client.post(url, {'skill_id': self.skill.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Skill already added.')

    def test_remove_user_skill(self):
        """Test removing a skill from the user."""
        user_skill = UserSkills.objects.create(user=self.user, skill=self.skill)
        url = reverse('user-skills-delete', args=[self.skill.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserSkills.objects.filter(pk=user_skill.pk).exists())
