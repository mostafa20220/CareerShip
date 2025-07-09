from typing import Optional, Tuple
from django.contrib.auth import get_user_model
import uuid

from certificates.models import Certificate
from projects.models.projects import Project, TeamProject

User = get_user_model()


class CertificateService:
    """Service responsible for certificate-related business logic."""
    
    @staticmethod
    def can_request_certificate(user: User, project: Project) -> Tuple[bool, str]:
        """
        Check if user can request a certificate for the given project.
        
        Returns:
            Tuple of (can_request: bool, message: str)
        """
        # Check if user is in any team that has finished this project
        team_project = TeamProject.objects.filter(
            team__members=user,
            project=project,
            is_finished=True
        ).first()
        
        if not team_project:
            return False, "No team you're a member of has finished this project."
        
        # Check if certificate already exists
        if Certificate.objects.filter(user=user, project=project).exists():
            return False, "Certificate already issued."
        
        return True, "Certificate is available to be requested."
    
    @staticmethod
    def create_certificate(user: User, project: Project) -> Certificate:
        """Create a new certificate for the user and project."""
        return Certificate.objects.create(
            user=user,
            project=project,
            no=uuid.uuid4()
        )
    
    @staticmethod
    def is_certificate_available(user: User, project: Project) -> Tuple[bool, str]:
        """
        Check if certificate is available for request.
        
        Returns:
            Tuple of (available: bool, message: str)
        """
        can_request, message = CertificateService.can_request_certificate(user, project)
        
        if not can_request:
            if "already issued" in message:
                return False, "Certificate already issued for that project."
            return False, message
        
        return True, "Certificate is available to be requested."
