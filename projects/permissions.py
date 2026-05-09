from rest_framework.permissions import BasePermission
from .models import ProjectMembership


class IsProjectMember(BasePermission):
    """Autorise uniquement les membres du projet."""
    def has_object_permission(self, request, view, obj):
        project = obj if hasattr(obj, 'memberships') else getattr(obj, 'project', None)
        if project is None:
            return False
        return ProjectMembership.objects.filter(project=project, user=request.user).exists()


class IsProjectOwner(BasePermission):
    """Autorise uniquement le propriétaire du projet."""
    def has_object_permission(self, request, view, obj):
        project = obj if hasattr(obj, 'owner') else getattr(obj, 'project', None)
        if project is None:
            return False
        return project.owner == request.user


class IsProjectChefOrReadOnly(BasePermission):
    """Chef de projet = lecture + écriture. Membre = lecture seule."""
    def has_object_permission(self, request, view, obj):
        from rest_framework.permissions import SAFE_METHODS
        project = obj if hasattr(obj, 'memberships') else getattr(obj, 'project', None)
        if project is None:
            return False
        if request.method in SAFE_METHODS:
            return ProjectMembership.objects.filter(project=project, user=request.user).exists()
        return ProjectMembership.objects.filter(
            project=project, user=request.user, role='chef'
        ).exists() or project.owner == request.user