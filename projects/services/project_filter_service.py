from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from django.db.models import QuerySet, Q
from django.contrib.auth import get_user_model

from projects.models import Project
from projects.models.projects import Project, TeamProject

User = get_user_model()


class ProjectFilter(ABC):
    """Abstract base class for project filters following the Strategy pattern."""
    
    @abstractmethod
    def apply(self, queryset: QuerySet[Project], value: str, user: User) -> QuerySet[Project]:
        """Apply the filter to the queryset."""
        pass


class CategoryFilter(ProjectFilter):
    """Filter projects by category."""
    
    def apply(self, queryset: QuerySet[Project], value: str, user: User) -> QuerySet[Project]:
        if not value:
            return queryset
        return queryset.filter(category__name=value)


class DifficultyLevelFilter(ProjectFilter):
    """Filter projects by difficulty level."""
    
    def apply(self, queryset: QuerySet[Project], value: str, user: User) -> QuerySet[Project]:
        if not value:
            return queryset
        return queryset.filter(difficulty_level__name=value)


class PremiumFilter(ProjectFilter):
    """Filter projects by premium status."""
    
    def apply(self, queryset: QuerySet[Project], value: str, user: User) -> QuerySet[Project]:
        if not value:
            return queryset
        
        if value.lower() == 'true':
            return queryset.filter(is_premium=True)
        elif value.lower() == 'false':
            return queryset.filter(is_premium=False)
        
        return queryset


class PublicFilter(ProjectFilter):
    """Filter projects by public/private status."""
    
    def apply(self, queryset: QuerySet[Project], value: str, user: User) -> QuerySet[Project]:
        if not value:
            return queryset
        
        if value.lower() == 'true':
            return queryset.filter(is_public=True)
        elif value.lower() == 'false':
            return queryset.filter(is_public=False, created_by=user)
        
        return queryset


class RegistrationFilter(ProjectFilter):
    """Filter projects by user registration status."""
    
    def apply(self, queryset: QuerySet[Project], value: str, user: User) -> QuerySet[Project]:
        if not value:
            return queryset
        
        user_registered_projects = TeamProject.objects.filter(
            team__members=user
        ).values_list('project_id', flat=True)
        
        if value.lower() == 'true':
            return queryset.filter(id__in=user_registered_projects)
        elif value.lower() == 'false':
            return queryset.exclude(id__in=user_registered_projects)
        
        return queryset


class ProjectFilterService:
    """Service responsible for applying filters to project querysets."""
    
    def __init__(self):
        self._filters = {
            'category': CategoryFilter(),
            'difficulty_level': DifficultyLevelFilter(),
            'is_premium': PremiumFilter(),
            'is_public': PublicFilter(),
            'is_registered': RegistrationFilter(),
        }
    
    def get_base_queryset(self, user: User) -> QuerySet[Project]:
        """Get the base queryset that shows projects visible to the user."""
        return Project.objects.filter(
            Q(is_public=True) | Q(created_by=user)
        )
    
    def apply_filters(self, queryset: QuerySet[Project], filters: Dict[str, Any], user: User) -> QuerySet[Project]:
        """Apply all provided filters to the queryset."""
        for filter_name, filter_value in filters.items():
            if filter_name in self._filters and filter_value is not None:
                queryset = self._filters[filter_name].apply(queryset, filter_value, user)
        
        return queryset
    
    def get_filtered_projects(self, filters: Dict[str, Any], user: User) -> QuerySet[Project]:
        """Get filtered projects for a user."""
        queryset = self.get_base_queryset(user)
        return self.apply_filters(queryset, filters, user)
