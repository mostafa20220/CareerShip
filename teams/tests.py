from django.test import TestCase
from django.db.utils import IntegrityError
from teams.models import Team, Invitation
from users.models import User
from django.utils import timezone
import uuid
import datetime as dt
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status


class TeamModelTest(TestCase):
    """Test cases for the Team model, covering creation, uniqueness, member management, and string representation."""

    def setUp(self):
        """Set up user for team tests."""
        self.user = User.objects.create(
            first_name='Omar',
            last_name='Khaled',
            email='omar_team@gmail.com',
            password='test123',
        )

    def test_create_team(self):
        """Test creating a team with valid data."""
        team = Team.objects.create(name='Team Alpha', owner=self.user)
        self.assertEqual(team.name, 'Team Alpha')
        self.assertEqual(team.owner, self.user)

    def test_unique_team_name_per_owner(self):
        """Test that team name is unique per owner."""
        Team.objects.create(name='Team Alpha', owner=self.user)
        with self.assertRaises(IntegrityError):
            Team.objects.create(name='Team Alpha', owner=self.user)

    def test_add_and_remove_member(self):
        """Test adding and removing a member from a team."""
        team = Team.objects.create(name='Team Beta', owner=self.user)
        member = User.objects.create(
            first_name='Ahmed',
            last_name='Ali',
            email='ahmed_team@gmail.com',
            password='test123',
        )
        team.add_member(member)
        self.assertIn(member, team.members.all())
        team.remove_member(member)
        self.assertNotIn(member, team.members.all())

    def test_create_with_owner(self):
        """Test creating a team with owner using the class method."""
        team = Team.create_with_owner(name='Team Gamma', owner=self.user)
        self.assertEqual(team.owner, self.user)
        self.assertIn(self.user, team.members.all())

    def test_str_method(self):
        """Test the string representation of the team."""
        team = Team.objects.create(name='Team Delta', owner=self.user)
        self.assertIn('Team Delta', str(team))
        self.assertIn(str(team.uuid), str(team))


class InvitationModelTest(TestCase):
    """Test cases for the Invitation model, covering creation, uniqueness, expiration, cascade delete, and string representation."""

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

    def test_cascade_delete_team(self):
        """Test that deleting a team cascades and deletes related invitations."""
        invitation = Invitation.objects.create(team=self.team, created_by=self.user)
        self.team.delete()
        self.assertFalse(Invitation.objects.filter(pk=invitation.pk).exists())

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


class TeamViewSetAPITest(APITestCase):
    """Test cases for TeamViewSet endpoints: list, create, retrieve, update, delete, add/remove member, leave."""

    def setUp(self):
        """Set up users and teams for API tests."""
        self.owner = User.objects.create_user(
            email='omar_teamapi@gmail.com',
            first_name='Omar',
            last_name='Khaled',
            password='test123',
        )
        self.member = User.objects.create_user(
            email='ahmed_teamapi@gmail.com',
            first_name='Ahmed',
            last_name='Ali',
            password='test123',
        )
        self.team = Team.objects.create(name='Team Sigma', owner=self.owner)
        self.team.members.add(self.owner)
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

    def test_list_teams(self):
        """Test listing all teams for the authenticated user."""
        url = reverse('team-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [t['name'] for t in response.data]
        self.assertIn('Team Sigma', names)

    def test_create_team(self):
        """Test creating a new team."""
        url = reverse('team-list')
        data = {'name': 'Team Omega'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Team Omega')

    def test_retrieve_team(self):
        """Test retrieving a team by uuid."""
        url = reverse('team-detail', args=[self.team.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.team.name)

    def test_update_team(self):
        """Test updating a team (owner only)."""
        url = reverse('team-detail', args=[self.team.uuid])
        data = {'name': 'Team Sigma Updated'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Team Sigma Updated')

    def test_delete_team(self):
        """Test deleting a team (owner only)."""
        url = reverse('team-detail', args=[self.team.uuid])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Team.objects.filter(uuid=self.team.uuid).exists())

    def test_add_member(self):
        """Test adding a member to the team."""
        url = reverse('team-members', args=[self.team.uuid])
        data = {'email': self.member.email}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.team.refresh_from_db()
        self.assertIn(self.member, self.team.members.all())

    def test_remove_member(self):
        """Test removing a member from the team."""
        self.team.members.add(self.member)
        url = reverse('team-members', args=[self.team.uuid])
        data = {'email': self.member.email}
        response = self.client.delete(url, data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.team.refresh_from_db()
        self.assertNotIn(self.member, self.team.members.all())

    def test_leave_team(self):
        """Test leaving a team as a member."""
        self.team.members.add(self.member)
        self.client.force_authenticate(user=self.member)
        url = reverse('team-leave', args=[self.team.uuid])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.team.refresh_from_db()
        self.assertNotIn(self.member, self.team.members.all())


class InvitationViewSetAPITest(APITestCase):
    """Test cases for InvitationViewSet endpoints: list, create, retrieve, accept, disable, enable, delete."""

    def setUp(self):
        """Set up users, team, and invitation for API tests."""
        self.owner = User.objects.create_user(
            email='omar_invapi@gmail.com',
            first_name='Omar',
            last_name='Khaled',
            password='test123',
        )
        self.invitee = User.objects.create_user(
            email='ahmed_invapi@gmail.com',
            first_name='Ahmed',
            last_name='Ali',
            password='test123',
        )
        self.team = Team.objects.create(name='Team Theta', owner=self.owner)
        self.team.members.add(self.owner)
        self.invitation = Invitation.objects.create(
            team=self.team, created_by=self.owner
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

    def test_list_invitations(self):
        """Test listing all invitations for a team."""
        url = reverse('team-invitations-list', args=[self.team.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        uuids = [i['uuid'] for i in response.data]
        self.assertIn(self.invitation.uuid, uuids)

    def test_create_invitation(self):
        """Test creating an invitation as the team owner."""
        url = reverse('team-invitations-list', args=[self.team.uuid])
        data = {}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['team'], self.team.id)
        self.assertEqual(response.data['created_by'], self.owner.id)

    def test_create_invitation_not_owner(self):
        """Test creating an invitation as a non-owner fails."""
        self.client.force_authenticate(user=self.invitee)
        url = reverse('team-invitations-list', args=[self.team.uuid])
        data = {}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Only team owners', str(response.data))

    def test_retrieve_invitation(self):
        """Test retrieving an invitation by uuid."""
        url = reverse(
            'team-invitations-detail', args=[self.team.uuid, self.invitation.uuid]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['uuid'], self.invitation.uuid)

    def test_accept_invitation(self):
        """Test accepting an invitation as a user."""
        self.client.force_authenticate(user=self.invitee)
        url = reverse(
            'team-invitations-accept', args=[self.team.uuid, self.invitation.uuid]
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.team.refresh_from_db()
        self.assertIn(self.invitee, self.team.members.all())

    def test_disable_invitation(self):
        """Test disabling an invitation as the team owner."""
        url = reverse(
            'team-invitations-disable', args=[self.team.uuid, self.invitation.uuid]
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.invitation.refresh_from_db()
        self.assertFalse(self.invitation.is_active)

    def test_enable_invitation(self):
        """Test enabling an invitation as the team owner."""
        self.invitation.is_active = False
        self.invitation.save()
        url = reverse(
            'team-invitations-enable', args=[self.team.uuid, self.invitation.uuid]
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.invitation.refresh_from_db()
        self.assertTrue(self.invitation.is_active)

    def test_delete_invitation(self):
        """Test deleting an invitation as the team owner."""
        url = reverse(
            'team-invitations-detail', args=[self.team.uuid, self.invitation.uuid]
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Invitation.objects.filter(uuid=self.invitation.uuid).exists())
