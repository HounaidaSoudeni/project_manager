from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Task, SubTask, Comment
from .serializers import TaskSerializer, SubTaskSerializer, CommentSerializer


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'assigned_to', 'project']
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'priority', 'order', 'created_at']

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(project__memberships__user=user).distinct()

    @action(detail=True, methods=['patch'], url_path='move')
    def move(self, request, pk=None):
        task = self.get_object()
        new_status = request.data.get('status')
        valid = [s[0] for s in Task.STATUS_CHOICES]
        if new_status not in valid:
            return Response({'error': 'Statut invalide.'}, status=400)
        task.status = new_status
        task.save()
        return Response(TaskSerializer(task).data)

    @action(detail=True, methods=['post'], url_path='subtasks')
    def add_subtask(self, request, pk=None):
        task = self.get_object()
        serializer = SubTaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(task=task)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=True, methods=['post'], url_path='comments')
    def add_comment(self, request, pk=None):
        task = self.get_object()
        serializer = CommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(task=task)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    @action(detail=False, methods=['get'], url_path='overdue')
    def overdue(self, request):
        from django.utils import timezone
        tasks = self.get_queryset().filter(
            due_date__lt=timezone.now().date()
        ).exclude(status='done')
        return Response(TaskSerializer(tasks, many=True).data)


class SubTaskViewSet(viewsets.ModelViewSet):
    serializer_class = SubTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SubTask.objects.filter(
            task__project__memberships__user=self.request.user
        ).distinct()