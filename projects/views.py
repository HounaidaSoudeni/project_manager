from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Project, ProjectMembership
from .serializers import ProjectSerializer, ProjectMembershipSerializer
from users.models import CustomUser


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(memberships__user=user).distinct()

    @action(detail=True, methods=['post'], url_path='invite')
    def invite_member(self, request, pk=None):
        project = self.get_object()
        email = request.data.get('email')
        role = request.data.get('role', 'membre')
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=404)
        membership, created = ProjectMembership.objects.get_or_create(
            project=project, user=user,
            defaults={'role': role}
        )
        if not created:
            return Response({'error': 'Déjà membre du projet.'}, status=400)
        return Response(ProjectMembershipSerializer(membership).data, status=201)

    @action(detail=True, methods=['post'], url_path='archive')
    def archive(self, request, pk=None):
        project = self.get_object()
        project.status = 'archive'
        project.save()
        return Response({'status': 'Projet archivé.'})