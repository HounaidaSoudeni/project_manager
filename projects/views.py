from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Project, ProjectMembership
from .serializers import ProjectSerializer, ProjectMembershipSerializer
from .permissions import IsProjectChefOrReadOnly
from users.models import CustomUser


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectChefOrReadOnly]

    def get_queryset(self):
        return Project.objects.filter(memberships__user=self.request.user).distinct()

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        if project.owner != request.user:
            return Response({'error': 'Seul le propriétaire peut supprimer ce projet.'}, status=403)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='invite')
    def invite_member(self, request, pk=None):
        project = self.get_object()
        if project.owner != request.user and not ProjectMembership.objects.filter(
            project=project, user=request.user, role='chef'
        ).exists():
            return Response({'error': 'Permission refusée.'}, status=403)
        email = request.data.get('email')
        role = request.data.get('role', 'membre')
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=404)
        membership, created = ProjectMembership.objects.get_or_create(
            project=project, user=user, defaults={'role': role}
        )
        if not created:
            return Response({'error': 'Déjà membre du projet.'}, status=400)
        return Response(ProjectMembershipSerializer(membership).data, status=201)

    @action(detail=True, methods=['delete'], url_path='members/(?P<user_id>[^/.]+)')
    def remove_member(self, request, pk=None, user_id=None):
        project = self.get_object()
        if project.owner != request.user:
            return Response({'error': 'Seul le propriétaire peut retirer des membres.'}, status=403)
        try:
            membership = ProjectMembership.objects.get(project=project, user__id=user_id)
            if membership.user == project.owner:
                return Response({'error': 'Impossible de retirer le propriétaire.'}, status=400)
            membership.delete()
            return Response({'status': 'Membre retiré.'})
        except ProjectMembership.DoesNotExist:
            return Response({'error': 'Membre introuvable.'}, status=404)

    @action(detail=True, methods=['post'], url_path='archive')
    def archive(self, request, pk=None):
        project = self.get_object()
        project.status = 'archive'
        project.save()
        return Response({'status': 'Projet archivé.'})

    @action(detail=True, methods=['get'], url_path='dashboard')
    def dashboard(self, request, pk=None):
        project = self.get_object()
        from kanban.models import Task
        from django.utils import timezone
        tasks = Task.objects.filter(project=project)
        today = timezone.now().date()
        members = ProjectMembership.objects.filter(project=project).select_related('user')
        return Response({
            'project': project.name,
            'status': project.status,
            'completion_rate': project.completion_rate,
            'tasks': {
                'total': tasks.count(),
                'todo': tasks.filter(status='todo').count(),
                'in_progress': tasks.filter(status='in_progress').count(),
                'review': tasks.filter(status='review').count(),
                'done': tasks.filter(status='done').count(),
                'overdue': tasks.filter(due_date__lt=today).exclude(status='done').count(),
            },
            'members': [
                {
                    'username': m.user.username,
                    'role': m.role,
                    'tasks_assigned': tasks.filter(assigned_to=m.user).count(),
                    'tasks_done': tasks.filter(assigned_to=m.user, status='done').count(),
                }
                for m in members
            ],
        })