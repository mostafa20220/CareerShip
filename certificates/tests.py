from django.test import TestCase
from django.db.utils import IntegrityError
from certificates.models import Certificate
from users.models import User
from projects.models.projects import Project
from projects.models.categories_difficulties import Category, DifficultyLevel
import uuid
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status


class CertificateModelTest(TestCase):
    """Test cases for the Certificate model, covering creation, uniqueness, and cascade delete."""

    def setUp(self):
        """Set up user, project, and related objects for certificate tests."""
        self.user = User.objects.create(
            first_name='Omar',
            last_name='Khaled',
            email='omar@gmail.com',
            password='test123',
        )
        self.category = Category.objects.create(name='Web')
        self.difficulty = DifficultyLevel.objects.create(name='Easy')
        self.project = Project.objects.create(
            name='Portfolio',
            description='A web portfolio',
            slug='portfolio',
            category=self.category,
            difficulty_level=self.difficulty,
        )
        self.certificate_no = uuid.uuid4()

    def test_create_certificate(self):
        """Test creating a certificate with valid data."""
        certificate = Certificate.objects.create(
            project=self.project, user=self.user, no=self.certificate_no
        )
        self.assertEqual(certificate.project, self.project)
        self.assertEqual(certificate.user, self.user)
        self.assertEqual(certificate.no, self.certificate_no)

    def test_unique_certificate_no(self):
        """Test that certificate 'no' field is unique."""
        Certificate.objects.create(
            project=self.project, user=self.user, no=self.certificate_no
        )
        with self.assertRaises(IntegrityError):
            Certificate.objects.create(
                project=self.project, user=self.user, no=self.certificate_no
            )

    def test_cascade_delete_user(self):
        """Test that deleting a user cascades and deletes related certificates."""
        certificate = Certificate.objects.create(
            project=self.project, user=self.user, no=uuid.uuid4()
        )
        self.user.delete()
        self.assertFalse(Certificate.objects.filter(pk=certificate.pk).exists())

    def test_cascade_delete_project(self):
        """Test that deleting a project cascades and deletes related certificates."""
        certificate = Certificate.objects.create(
            project=self.project, user=self.user, no=uuid.uuid4()
        )
        self.project.delete()
        self.assertFalse(Certificate.objects.filter(pk=certificate.pk).exists())


class CertificateAPITest(APITestCase):
    """Test cases for certificate API endpoints: list, retrieve, and download."""

    def setUp(self):
        """Set up users, project, and certificates for API tests."""
        self.user = User.objects.create(
            email='omar_cert_api@gmail.com',
            first_name='Omar',
            last_name='Khaled',
            password='test123',
        )
        self.other_user = User.objects.create(
            email='ahmed_cert_api@gmail.com',
            first_name='Ahmed',
            last_name='Ali',
            password='test123',
        )
        self.category = Category.objects.create(name='Web')
        self.difficulty = DifficultyLevel.objects.create(name='Easy')
        self.project = Project.objects.create(
            name='Portfolio',
            description='A web portfolio',
            slug='portfolio',
            category=self.category,
            difficulty_level=self.difficulty,
        )
        self.certificate = Certificate.objects.create(
            project=self.project, user=self.user, no=uuid.uuid4()
        )
        self.other_certificate = Certificate.objects.create(
            project=self.project, user=self.other_user, no=uuid.uuid4()
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_certificates(self):
        """Test listing certificates for the authenticated user."""
        url = reverse('list_certificates')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user'], self.user.id)

    def test_list_certificates_unauthenticated(self):
        """Test listing certificates fails for unauthenticated users."""
        self.client.force_authenticate(user=None)
        url = reverse('list_certificates')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_certificate(self):
        """Test retrieving a certificate by UUID for the authenticated user."""
        url = reverse('retrieve_certificate', args=[self.certificate.no])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.user.id)
        self.assertEqual(response.data['project'], self.project.id)
        self.assertEqual(str(self.certificate.no), response.data['no'])

    def test_retrieve_certificate_not_found(self):
        """Test retrieving a certificate that does not exist returns 404."""
        url = reverse('retrieve_certificate', args=[uuid.uuid4()])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_certificate_not_owned(self):
        """Test retrieving a certificate not owned by the user returns 404."""
        url = reverse('retrieve_certificate', args=[self.other_certificate.no])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_certificate(self):
        """Test downloading a certificate as the owner (should return a PDF file response)."""
        url = reverse('download_certificate', args=[self.certificate.no])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get('content-type'), 'application/pdf')
        self.assertIn(
            f'certificate_{self.certificate.no}', response.get('content-disposition')
        )

    def test_download_certificate_not_found(self):
        """Test downloading a non-existent certificate returns 404."""
        url = reverse('download_certificate', args=[uuid.uuid4()])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_certificate_not_owned(self):
        """Test downloading a certificate not owned by the user returns 404."""
        url = reverse('download_certificate', args=[self.other_certificate.no])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_certificate_unauthenticated(self):
        """Test downloading a certificate fails for unauthenticated users."""
        self.client.force_authenticate(user=None)
        url = reverse('download_certificate', args=[self.certificate.no])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
