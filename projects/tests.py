from django.test import TestCase
from django.db.utils import IntegrityError
from projects.models.projects import Project, TeamProject
from projects.models.categories_difficulties import Category, DifficultyLevel
from teams.models import Team, Invitation
from users.models import User
from django.utils import timezone
import datetime as dt
import uuid
from projects.models.tasks_endpoints import Task, Endpoint, MethodType
from projects.models.testcases import TestCase as ProjectTestCase, ApiTestCase, TestType
from projects.models.submission import Submission, PENDING, PASSED, FAILED
from projects.models.prerequisites import Prerequisite, TaskPrerequisite
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token


class ProjectModelTest(TestCase):
    """Test cases for the Project model, covering creation, uniqueness, and string representation."""

    def setUp(self):
        """Set up category and difficulty for project tests."""
        self.category = Category.objects.create(name='Web')
        self.difficulty = DifficultyLevel.objects.create(name='Easy')

    def test_create_project(self):
        """Test creating a project with valid data."""
        project = Project.objects.create(
            name='Portfolio',
            description='A web portfolio',
            slug='portfolio',
            category=self.category,
            difficulty_level=self.difficulty,
        )
        self.assertEqual(project.name, 'Portfolio')
        self.assertEqual(project.category, self.category)
        self.assertEqual(project.difficulty_level, self.difficulty)

    def test_unique_slug(self):
        """Test that project slug is unique."""
        Project.objects.create(
            name='Portfolio',
            description='A web portfolio',
            slug='portfolio',
            category=self.category,
            difficulty_level=self.difficulty,
        )
        with self.assertRaises(IntegrityError):
            Project.objects.create(
                name='Portfolio2',
                description='Another project',
                slug='portfolio',
                category=self.category,
                difficulty_level=self.difficulty,
            )

    def test_str_method(self):
        """Test the string representation of the project returns its name."""
        project = Project.objects.create(
            name='Portfolio',
            description='A web portfolio',
            slug='portfolio',
            category=self.category,
            difficulty_level=self.difficulty,
        )
        self.assertEqual(str(project), 'Portfolio')


class TeamProjectModelTest(TestCase):
    """Test cases for the TeamProject model, covering creation, uniqueness, cascade delete, and string representation."""

    def setUp(self):
        """Set up team, project, and related objects for team project tests."""
        self.category = Category.objects.create(name='Web')
        self.difficulty = DifficultyLevel.objects.create(name='Easy')
        self.project = Project.objects.create(
            name='Portfolio',
            description='A web portfolio',
            slug='portfolio',
            category=self.category,
            difficulty_level=self.difficulty,
        )
        self.team = Team.objects.create(name='Team Alpha')

    def test_create_team_project(self):
        """Test creating a team project with valid data."""
        team_project = TeamProject.objects.create(team=self.team, project=self.project)
        self.assertEqual(team_project.team, self.team)
        self.assertEqual(team_project.project, self.project)
        self.assertFalse(team_project.is_finished)

    def test_unique_team_project(self):
        """Test that (team, project) pair is unique."""
        TeamProject.objects.create(team=self.team, project=self.project)
        with self.assertRaises(IntegrityError):
            TeamProject.objects.create(team=self.team, project=self.project)

    def test_cascade_delete_team(self):
        """Test that deleting a team cascades and deletes related team projects."""
        team_project = TeamProject.objects.create(team=self.team, project=self.project)
        self.team.delete()
        self.assertFalse(TeamProject.objects.filter(pk=team_project.pk).exists())

    def test_cascade_delete_project(self):
        """Test that deleting a project cascades and deletes related team projects."""
        team_project = TeamProject.objects.create(team=self.team, project=self.project)
        self.project.delete()
        self.assertFalse(TeamProject.objects.filter(pk=team_project.pk).exists())

    def test_str_method(self):
        """Test the string representation of the team project."""
        team_project = TeamProject.objects.create(team=self.team, project=self.project)
        self.assertIn(self.team.name, str(team_project))
        self.assertIn(self.project.name, str(team_project))


class InvitationModelTest(TestCase):
    """Test cases for the Invitation model, covering creation, uniqueness, expiration, and string representation."""

    def setUp(self):
        """Set up user and team for invitation tests."""
        self.user = User.objects.create(
            first_name='Omar',
            last_name='Khaled',
            email='omar_invite@gmail.com',
            password='test123',
        )
        self.team = Team.objects.create(name='Team Beta', owner=self.user)

    def test_create_invitation(self):
        """Test creating an invitation with valid data."""
        invitation = Invitation.objects.create(team=self.team, created_by=self.user)
        self.assertEqual(invitation.team, self.team)
        self.assertEqual(invitation.created_by, self.user)
        self.assertTrue(invitation.is_active)
        self.assertFalse(invitation.is_expired())

    def test_unique_uuid(self):
        """Test that invitation uuid is unique."""
        invitation = Invitation.objects.create(team=self.team, created_by=self.user)
        with self.assertRaises(Exception):
            Invitation.objects.create(
                team=self.team, created_by=self.user, uuid=invitation.uuid
            )

    def test_expired_invitation(self):
        """Test that an invitation is expired after its expiration date."""
        invitation = Invitation.objects.create(
            team=self.team, created_by=self.user, expires_in_days=1
        )
        invitation.created_at = timezone.now() - dt.timedelta(days=2)
        invitation.save()
        self.assertTrue(invitation.is_expired())

    def test_str_method(self):
        """Test the string representation of the invitation."""
        invitation = Invitation.objects.create(team=self.team, created_by=self.user)
        self.assertIn('Invitation created at', str(invitation))
        self.assertIn('expires in', str(invitation))

    def test_get_invitation_url(self):
        """Test that get_invitation_url returns a valid URL pattern."""
        invitation = Invitation.objects.create(team=self.team, created_by=self.user)
        url = invitation.get_invitation_url()
        self.assertIn(str(self.team.uuid), url)
        self.assertIn(str(invitation.uuid), url)


class TaskModelTest(TestCase):
    """Test cases for the Task model, covering creation, uniqueness, cascade delete, and string representation."""

    def setUp(self):
        """Set up project and difficulty for task tests."""
        self.category = Category.objects.create(name='API')
        self.difficulty = DifficultyLevel.objects.create(name='Medium')
        self.project = Project.objects.create(
            name='API Project',
            description='API project desc',
            slug='api-project',
            category=self.category,
            difficulty_level=self.difficulty,
        )

    def test_create_task(self):
        """Test creating a task with valid data."""
        task = Task.objects.create(
            project=self.project,
            difficulty_level=self.difficulty,
            name='Task 1',
            slug='task-1',
            description='Test task',
            order=0,
        )
        self.assertEqual(task.project, self.project)
        self.assertEqual(task.difficulty_level, self.difficulty)
        self.assertEqual(task.name, 'Task 1')

    def test_unique_task_order_per_project(self):
        """Test that (project, order) pair is unique for tasks."""
        Task.objects.create(
            project=self.project,
            difficulty_level=self.difficulty,
            name='Task 1',
            slug='task-1',
            description='Test task',
            order=0,
        )
        with self.assertRaises(IntegrityError):
            Task.objects.create(
                project=self.project,
                difficulty_level=self.difficulty,
                name='Task 2',
                slug='task-2',
                description='Another task',
                order=0,
            )

    def test_str_method(self):
        """Test the string representation of the task returns its name."""
        task = Task.objects.create(
            project=self.project,
            difficulty_level=self.difficulty,
            name='Task 1',
            slug='task-1',
            description='Test task',
            order=0,
        )
        self.assertEqual(str(task), 'Task 1')


class EndpointModelTest(TestCase):
    """Test cases for the Endpoint model, covering creation, cascade delete, and string representation."""

    def setUp(self):
        """Set up task for endpoint tests."""
        self.category = Category.objects.create(name='API')
        self.difficulty = DifficultyLevel.objects.create(name='Medium')
        self.project = Project.objects.create(
            name='API Project',
            description='API project desc',
            slug='api-project',
            category=self.category,
            difficulty_level=self.difficulty,
        )
        self.task = Task.objects.create(
            project=self.project,
            difficulty_level=self.difficulty,
            name='Task 1',
            slug='task-1',
            description='Test task',
            order=0,
        )

    def test_create_endpoint(self):
        """Test creating an endpoint with valid data."""
        endpoint = Endpoint.objects.create(
            task=self.task,
            method=MethodType.GET,
            path='/api/test/',
            description='Test endpoint',
        )
        self.assertEqual(endpoint.task, self.task)
        self.assertEqual(endpoint.method, MethodType.GET)
        self.assertEqual(endpoint.path, '/api/test/')

    def test_cascade_delete_task(self):
        """Test that deleting a task cascades and deletes related endpoints."""
        endpoint = Endpoint.objects.create(
            task=self.task,
            method=MethodType.GET,
            path='/api/test/',
            description='Test endpoint',
        )
        self.task.delete()
        self.assertFalse(Endpoint.objects.filter(pk=endpoint.pk).exists())

    def test_str_method(self):
        """Test the string representation of the endpoint."""
        endpoint = Endpoint.objects.create(
            task=self.task,
            method=MethodType.GET,
            path='/api/test/',
            description='Test endpoint',
        )
        self.assertIn('GET', str(endpoint))
        self.assertIn('/api/test/', str(endpoint))


class ProjectTestCaseModelTest(TestCase):
    """Test cases for the TestCase model, covering creation, uniqueness, cascade delete, and string representation."""

    def setUp(self):
        """Set up task for test case tests."""
        self.category = Category.objects.create(name='Testing')
        self.difficulty = DifficultyLevel.objects.create(name='Hard')
        self.project = Project.objects.create(
            name='Testing Project',
            description='Testing project desc',
            slug='testing-project',
            category=self.category,
            difficulty_level=self.difficulty,
        )
        self.task = Task.objects.create(
            project=self.project,
            difficulty_level=self.difficulty,
            name='Test Task',
            slug='test-task',
            description='Test task',
            order=0,
        )

    def test_create_testcase(self):
        """Test creating a test case with valid data."""
        testcase = ProjectTestCase.objects.create(
            task=self.task,
            name='Test 404',
            description='Should return 404',
            test_type=TestType.API_REQUEST,
            points=10,
            stop_on_failure=True,
            order=0,
        )
        self.assertEqual(testcase.task, self.task)
        self.assertEqual(testcase.name, 'Test 404')
        self.assertEqual(testcase.test_type, TestType.API_REQUEST)

    def test_unique_order_per_task(self):
        """Test that (task, order) pair is unique for test cases."""
        ProjectTestCase.objects.create(
            task=self.task,
            name='Test 404',
            description='Should return 404',
            test_type=TestType.API_REQUEST,
            points=10,
            stop_on_failure=True,
            order=0,
        )
        with self.assertRaises(IntegrityError):
            ProjectTestCase.objects.create(
                task=self.task,
                name='Test 500',
                description='Should return 500',
                test_type=TestType.API_REQUEST,
                points=5,
                stop_on_failure=False,
                order=0,
            )

    def test_str_method(self):
        """Test the string representation of the test case."""
        testcase = ProjectTestCase.objects.create(
            task=self.task,
            name='Test 404',
            description='Should return 404',
            test_type=TestType.API_REQUEST,
            points=10,
            stop_on_failure=True,
            order=1,
        )
        self.assertIn('1', str(testcase))
        self.assertIn('Test 404', str(testcase))


class ApiTestCaseModelTest(TestCase):
    """Test cases for the ApiTestCase model, covering creation, cascade delete, and string representation."""

    def setUp(self):
        """Set up test case and endpoint for API test case tests."""
        self.category = Category.objects.create(name='API')
        self.difficulty = DifficultyLevel.objects.create(name='Medium')
        self.project = Project.objects.create(
            name='API Project',
            description='API project desc',
            slug='api-project',
            category=self.category,
            difficulty_level=self.difficulty,
        )
        self.task = Task.objects.create(
            project=self.project,
            difficulty_level=self.difficulty,
            name='Task 1',
            slug='task-1',
            description='Test task',
            order=0,
        )
        self.endpoint = Endpoint.objects.create(
            task=self.task,
            method=MethodType.GET,
            path='/api/test/',
            description='Test endpoint',
        )
        self.testcase = ProjectTestCase.objects.create(
            task=self.task,
            name='Test 404',
            description='Should return 404',
            test_type=TestType.API_REQUEST,
            points=10,
            stop_on_failure=True,
            order=0,
        )

    def test_create_apitestcase(self):
        """Test creating an API test case with valid data."""
        api_testcase = ApiTestCase.objects.create(
            test_case=self.testcase,
            endpoint=self.endpoint,
            path_params={'id': 1},
            request_payload={'key': 'value'},
            request_headers={'Authorization': 'Token'},
            expected_status_code=404,
            expected_response_schema={'type': 'object'},
        )
        self.assertEqual(api_testcase.test_case, self.testcase)
        self.assertEqual(api_testcase.endpoint, self.endpoint)
        self.assertEqual(api_testcase.expected_status_code, 404)

    def test_cascade_delete_testcase(self):
        """Test that deleting a test case cascades and deletes related API test case."""
        api_testcase = ApiTestCase.objects.create(
            test_case=self.testcase, endpoint=self.endpoint, expected_status_code=404
        )
        self.testcase.delete()
        self.assertFalse(ApiTestCase.objects.filter(pk=api_testcase.pk).exists())

    def test_str_method(self):
        """Test the string representation of the API test case."""
        api_testcase = ApiTestCase.objects.create(
            test_case=self.testcase, endpoint=self.endpoint, expected_status_code=404
        )
        self.assertIn('API Test for', str(api_testcase))
        self.assertIn(self.testcase.name, str(api_testcase))


class SubmissionModelTest(TestCase):
    """Test cases for the Submission model, covering creation, cascade delete, string representation, and stuck submissions."""

    def setUp(self):
        """Set up user, team, project, and task for submission tests."""
        self.user = User.objects.create(
            first_name='Omar',
            last_name='Khaled',
            email='omar_sub@gmail.com',
            password='test123',
        )
        self.team = Team.objects.create(name='Team Gamma', owner=self.user)
        self.category = Category.objects.create(name='ML')
        self.difficulty = DifficultyLevel.objects.create(name='Advanced')
        self.project = Project.objects.create(
            name='ML Project',
            description='ML project desc',
            slug='ml-project',
            category=self.category,
            difficulty_level=self.difficulty,
        )
        self.task = Task.objects.create(
            project=self.project,
            difficulty_level=self.difficulty,
            name='ML Task',
            slug='ml-task',
            description='ML task',
            order=0,
        )

    def test_create_submission(self):
        """Test creating a submission with valid data."""
        submission = Submission.objects.create(
            project=self.project,
            task=self.task,
            user=self.user,
            team=self.team,
            status=PENDING,
            passed_tests=0,
            failed_test_index=None,
            passed_percentage=0,
        )
        self.assertEqual(submission.project, self.project)
        self.assertEqual(submission.task, self.task)
        self.assertEqual(submission.user, self.user)
        self.assertEqual(submission.team, self.team)
        self.assertEqual(submission.status, PENDING)

    def test_str_method(self):
        """Test the string representation of the submission."""
        submission = Submission.objects.create(
            project=self.project,
            task=self.task,
            user=self.user,
            team=self.team,
            status=PASSED,
            passed_tests=5,
            failed_test_index=None,
            passed_percentage=100,
            deployment_url='http://example.com',
            completed_at=timezone.now(),
        )
        self.assertIn('passed', str(submission))
        self.assertIn('http://example.com', str(submission))

    def test_get_stuck_submissions(self):
        """Test get_stuck_submissions returns submissions pending for too long."""
        old_submission = Submission.objects.create(
            project=self.project,
            task=self.task,
            user=self.user,
            team=self.team,
            status=PENDING,
            passed_tests=0,
            failed_test_index=None,
            passed_percentage=0,
            created_at=timezone.now() - timezone.timedelta(minutes=10),
        )
        stuck = Submission.get_stuck_submissions(timeout_minutes=5)
        self.assertIn(old_submission, stuck)

    def test_cascade_delete_user(self):
        """Test that deleting a user cascades and deletes related submissions."""
        submission = Submission.objects.create(
            project=self.project,
            task=self.task,
            user=self.user,
            team=self.team,
            status=PENDING,
            passed_tests=0,
            failed_test_index=None,
            passed_percentage=0,
        )
        self.user.delete()
        self.assertFalse(Submission.objects.filter(pk=submission.pk).exists())

    def test_cascade_delete_team(self):
        """Test that deleting a team cascades and deletes related submissions."""
        submission = Submission.objects.create(
            project=self.project,
            task=self.task,
            user=self.user,
            team=self.team,
            status=PENDING,
            passed_tests=0,
            failed_test_index=None,
            passed_percentage=0,
        )
        self.team.delete()
        self.assertFalse(Submission.objects.filter(pk=submission.pk).exists())


class PrerequisiteModelTest(TestCase):
    """Test cases for the Prerequisite model, covering creation and string representation."""

    def test_create_prerequisite(self):
        """Test creating a prerequisite with valid data."""
        prerequisite = Prerequisite.objects.create(
            name='Python', description='Basic Python knowledge'
        )
        self.assertEqual(prerequisite.name, 'Python')
        self.assertEqual(prerequisite.description, 'Basic Python knowledge')

    def test_str_method(self):
        """Test the string representation of the prerequisite."""
        prerequisite = Prerequisite.objects.create(
            name='Python', description='Basic Python knowledge'
        )
        self.assertEqual(str(prerequisite), 'Python')


class TaskPrerequisiteModelTest(TestCase):
    """Test cases for the TaskPrerequisite model, covering creation and cascade delete."""

    def setUp(self):
        """Set up prerequisite and task for task prerequisite tests."""
        self.category = Category.objects.create(name='Backend')
        self.difficulty = DifficultyLevel.objects.create(name='Intermediate')
        self.project = Project.objects.create(
            name='Backend Project',
            description='Backend project desc',
            slug='backend-project',
            category=self.category,
            difficulty_level=self.difficulty,
        )
        self.task = Task.objects.create(
            project=self.project,
            difficulty_level=self.difficulty,
            name='Backend Task',
            slug='backend-task',
            description='Backend task',
            order=0,
        )
        self.prerequisite = Prerequisite.objects.create(
            name='Django', description='Django basics'
        )

    def test_create_task_prerequisite(self):
        """Test creating a task prerequisite with valid data."""
        tp = TaskPrerequisite.objects.create(
            task=self.task, prerequisite=self.prerequisite
        )
        self.assertEqual(tp.task, self.task)
        self.assertEqual(tp.prerequisite, self.prerequisite)

    def test_cascade_delete_task(self):
        """Test that deleting a task cascades and deletes related task prerequisites."""
        tp = TaskPrerequisite.objects.create(
            task=self.task, prerequisite=self.prerequisite
        )
        self.task.delete()
        self.assertFalse(TaskPrerequisite.objects.filter(pk=tp.pk).exists())

    def test_cascade_delete_prerequisite(self):
        """Test that deleting a prerequisite cascades and deletes related task prerequisites."""
        tp = TaskPrerequisite.objects.create(
            task=self.task, prerequisite=self.prerequisite
        )
        self.prerequisite.delete()
        self.assertFalse(TaskPrerequisite.objects.filter(pk=tp.pk).exists())


class ProjectListAndDetailAPITest(APITestCase):
    """Test cases for listing projects, project details, and filtering by category/difficulty."""

    def setUp(self):
        """Set up user, categories, difficulties, and projects for API tests."""
        self.user = User.objects.create_user(
            email='omar_api@gmail.com',
            first_name='Omar',
            last_name='Khaled',
            password='test123',
        )
        self.category1 = Category.objects.create(name='Web')
        self.category2 = Category.objects.create(name='ML')
        self.difficulty1 = DifficultyLevel.objects.create(name='Easy')
        self.difficulty2 = DifficultyLevel.objects.create(name='Hard')
        self.project1 = Project.objects.create(
            name='Portfolio',
            description='A web portfolio',
            slug='portfolio',
            category=self.category1,
            difficulty_level=self.difficulty1,
        )
        self.project2 = Project.objects.create(
            name='ML Classifier',
            description='A ML project',
            slug='ml-classifier',
            category=self.category2,
            difficulty_level=self.difficulty2,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_projects(self):
        """Test listing all projects."""
        url = reverse('list-projects')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 2)
        names = [p['name'] for p in response.data['results']]
        self.assertIn('Portfolio', names)
        self.assertIn('ML Classifier', names)

    def test_list_projects_filter_by_category(self):
        """Test filtering projects by category name."""
        url = reverse('list-projects') + f'?category={self.category1.name}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for project in response.data['results']:
            self.assertEqual(project['category'], self.category1.id)

    def test_list_projects_filter_by_difficulty(self):
        """Test filtering projects by difficulty level name."""
        url = reverse('list-projects') + f'?difficulty_level={self.difficulty2.name}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for project in response.data['results']:
            self.assertEqual(project['difficulty_level'], self.difficulty2.id)

    def test_project_details(self):
        """Test retrieving project details by project_id."""
        url = reverse('project-details', args=[self.project1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.project1.id)
        self.assertEqual(response.data['name'], self.project1.name)

    def test_project_details_not_found(self):
        """Test retrieving details for a non-existent project returns 404."""
        url = reverse('project-details', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CategoryAndDifficultyAPITest(APITestCase):
    """Test cases for listing categories and difficulties."""

    def setUp(self):
        """Set up user, categories, and difficulties for API tests."""
        self.user = User.objects.create_user(
            email='omar_catdiff@gmail.com',
            first_name='Omar',
            last_name='Khaled',
            password='test123',
        )
        self.category = Category.objects.create(name='Backend')
        self.difficulty = DifficultyLevel.objects.create(name='Intermediate')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_categories(self):
        """Test listing all categories."""
        url = reverse('list-categories')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [c['name'] for c in response.data]
        self.assertIn('Backend', names)

    def test_list_difficulties(self):
        """Test listing all difficulties."""
        url = reverse('list-difficulties')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [d['name'] for d in response.data]
        self.assertIn('Intermediate', names)


class TaskAndSubmissionAPITest(APITestCase):
    """Test cases for listing tasks, task details, and listing submissions for a project."""

    def setUp(self):
        """Set up user, project, tasks, and submissions for API tests."""
        self.user = User.objects.create_user(
            email='omar_tasksub@gmail.com',
            first_name='Omar',
            last_name='Khaled',
            password='test123',
        )
        self.category = Category.objects.create(name='Fullstack')
        self.difficulty = DifficultyLevel.objects.create(name='Expert')
        self.project = Project.objects.create(
            name='Fullstack Project',
            description='Fullstack desc',
            slug='fullstack-project',
            category=self.category,
            difficulty_level=self.difficulty,
        )
        self.task1 = Task.objects.create(
            project=self.project,
            difficulty_level=self.difficulty,
            name='Setup',
            slug='setup-task',
            description='Setup task',
            order=0,
        )
        self.task2 = Task.objects.create(
            project=self.project,
            difficulty_level=self.difficulty,
            name='API',
            slug='api-task',
            description='API task',
            order=1,
        )
        self.team = Team.objects.create(name='Team Delta', owner=self.user)
        self.submission = Submission.objects.create(
            project=self.project,
            task=self.task1,
            user=self.user,
            team=self.team,
            status=PENDING,
            passed_tests=0,
            failed_test_index=None,
            passed_percentage=0,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_project_tasks(self):
        """Test listing all tasks for a project."""
        url = reverse('list-project-tasks', args=[self.project.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [t['name'] for t in response.data]
        self.assertIn('Setup', names)
        self.assertIn('API', names)

    def test_task_details(self):
        """Test retrieving task details by project_id and task_id."""
        url = reverse('task-details', args=[self.project.id, self.task1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.task1.id)
        self.assertEqual(response.data['name'], self.task1.name)

    def test_task_details_not_found(self):
        """Test retrieving details for a non-existent task returns 404."""
        url = reverse('task-details', args=[self.project.id, 99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_project_submissions(self):
        """Test listing all submissions for a project."""
        url = reverse('list-project-submissions', args=[self.project.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        user_ids = [s['user'] for s in response.data]
        self.assertIn(self.user.id, user_ids)


class ProjectRegistrationAndCertificateAPITest(APITestCase):
    """Test cases for project registration, request certificate, and certificate available endpoints."""

    def setUp(self):
        """Set up user, project, and team for API tests."""
        self.user = User.objects.create_user(
            email='omar_regcert@gmail.com',
            first_name='Omar',
            last_name='Khaled',
            password='test123',
        )
        self.category = Category.objects.create(name='AI')
        self.difficulty = DifficultyLevel.objects.create(name='Challenging')
        self.project = Project.objects.create(
            name='AI Project',
            description='AI project desc',
            slug='ai-project',
            category=self.category,
            difficulty_level=self.difficulty,
        )
        self.team = Team.objects.create(name='Team Epsilon', owner=self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_request_certificate_not_finished(self):
        """Test requesting a certificate for a project not finished by the user returns 400."""
        url = reverse('request-certificate', args=[self.project.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Project not finished', str(response.data))

    def test_certificate_available_not_finished(self):
        """Test checking certificate availability for a project not finished by the user returns 400."""
        url = reverse('certificate-available', args=[self.project.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Project not finished', str(response.data))

    # To test the positive case, we need a finished TeamProject
    def test_request_certificate_success(self):
        """Test requesting a certificate for a finished project returns 201 and certificate id."""
        from projects.models.projects import TeamProject

        team_project = TeamProject.objects.create(
            team=self.team, project=self.project, is_finished=True
        )
        url = reverse('request-certificate', args=[self.project.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('certificate_id', response.data)

    def test_certificate_available_success(self):
        """Test checking certificate availability for a finished project returns available True."""
        from projects.models.projects import TeamProject

        team_project = TeamProject.objects.create(
            team=self.team, project=self.project, is_finished=True
        )
        url = reverse('certificate-available', args=[self.project.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['available'])

    def test_request_certificate_already_issued(self):
        """Test requesting a certificate when already issued returns 400."""
        from projects.models.projects import TeamProject

        team_project = TeamProject.objects.create(
            team=self.team, project=self.project, is_finished=True
        )
        # Issue certificate
        from certificates.models import Certificate

        Certificate.objects.create(
            user=self.user, project=self.project, no=uuid.uuid4()
        )
        url = reverse('request-certificate', args=[self.project.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Certificate already issued', str(response.data))

    def test_certificate_available_already_issued(self):
        """Test checking certificate availability when already issued returns available False."""
        from projects.models.projects import TeamProject

        team_project = TeamProject.objects.create(
            team=self.team, project=self.project, is_finished=True
        )
        from certificates.models import Certificate

        Certificate.objects.create(
            user=self.user, project=self.project, no=uuid.uuid4()
        )
        url = reverse('certificate-available', args=[self.project.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['available'])


class ProjectRegistrationAPITest(APITestCase):
    """Test cases for project registration endpoints."""

    def setUp(self):
        """Set up user, project, and team for registration API tests."""
        self.user = User.objects.create_user(
            email='omar_reg@gmail.com',
            first_name='Omar',
            last_name='Khaled',
            password='test123',
        )
        self.category = Category.objects.create(name='Cloud')
        self.difficulty = DifficultyLevel.objects.create(name='Cloudy')
        self.project = Project.objects.create(
            name='Cloud Project',
            description='Cloud project desc',
            slug='cloud-project',
            category=self.category,
            difficulty_level=self.difficulty,
        )
        self.team = Team.objects.create(name='Team Zeta', owner=self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_registration(self):
        """Test creating a project registration (POST) as an authenticated user."""
        url = reverse('project-registration-list')
        data = {
            'team': self.team.id,
            'project': self.project.id,
        }
        response = self.client.post(url, data)
        self.assertIn(
            response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK]
        )
        self.assertEqual(response.data['team'], self.team.id)
        self.assertEqual(response.data['project'], self.project.id)

    def test_create_registration_unauthenticated(self):
        """Test creating a project registration fails for unauthenticated users."""
        self.client.force_authenticate(user=None)
        url = reverse('project-registration-list')
        data = {
            'team': self.team.id,
            'project': self.project.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SubmissionViewSetAPITest(APITestCase):
    """Test cases for submission endpoints (list, create, permissions)."""

    def setUp(self):
        """Set up user, project, task, team, and submission for API tests."""
        self.user = User.objects.create_user(
            email='omar_subapi@gmail.com',
            first_name='Omar',
            last_name='Khaled',
            password='test123',
        )
        self.category = Category.objects.create(name='DevOps')
        self.difficulty = DifficultyLevel.objects.create(name='DevOpsy')
        self.project = Project.objects.create(
            name='DevOps Project',
            description='DevOps project desc',
            slug='devops-project',
            category=self.category,
            difficulty_level=self.difficulty,
        )
        self.task = Task.objects.create(
            project=self.project,
            difficulty_level=self.difficulty,
            name='CI Task',
            slug='ci-task',
            description='CI task',
            order=0,
        )
        self.team = Team.objects.create(name='Team Lambda', owner=self.user)
        self.submission = Submission.objects.create(
            project=self.project,
            task=self.task,
            user=self.user,
            team=self.team,
            status=PENDING,
            passed_tests=0,
            failed_test_index=None,
            passed_percentage=0,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_task_submissions(self):
        """Test listing all submissions for a specific task in a project."""
        url = reverse(
            'task-submissions-list',
            kwargs={'project_id': self.project.id, 'task_id': self.task.id},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_ids = [s['user'] for s in response.data]
        self.assertIn(self.user.id, user_ids)

    def test_create_submission(self):
        """Test creating a submission for a task in a project."""
        url = reverse(
            'task-submissions-list',
            kwargs={'project_id': self.project.id, 'task_id': self.task.id},
        )
        data = {
            'project': self.project.id,
            'task': self.task.id,
            'user': self.user.id,
            'team': self.team.id,
            'status': PENDING,
            'passed_tests': 0,
            'failed_test_index': None,
            'passed_percentage': 0,
        }
        response = self.client.post(url, data)
        self.assertIn(
            response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK]
        )
        self.assertEqual(response.data['user'], self.user.id)
        self.assertEqual(response.data['task'], self.task.id)

    def test_create_submission_unauthenticated(self):
        """Test creating a submission fails for unauthenticated users."""
        self.client.force_authenticate(user=None)
        url = reverse(
            'task-submissions-list',
            kwargs={'project_id': self.project.id, 'task_id': self.task.id},
        )
        data = {
            'project': self.project.id,
            'task': self.task.id,
            'user': self.user.id,
            'team': self.team.id,
            'status': PENDING,
            'passed_tests': 0,
            'failed_test_index': None,
            'passed_percentage': 0,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
