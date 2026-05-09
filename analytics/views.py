from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone
from projects.models import Project
from kanban.models import Task


class ProjectKPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, memberships__user=request.user)
        except Project.DoesNotExist:
            return Response({'error': 'Projet introuvable.'}, status=404)

        tasks = Task.objects.filter(project=project)
        today = timezone.now().date()

        total = tasks.count()
        done = tasks.filter(status='done').count()
        in_progress = tasks.filter(status='in_progress').count()
        review = tasks.filter(status='review').count()
        todo = tasks.filter(status='todo').count()
        overdue = tasks.filter(due_date__lt=today).exclude(status='done').count()

        total_sp = sum(t.story_points for t in tasks)
        done_sp = sum(t.story_points for t in tasks.filter(status='done'))

        return Response({
            'project': project.name,
            'completion_rate': project.completion_rate,
            'tasks': {
                'total': total,
                'todo': todo,
                'in_progress': in_progress,
                'review': review,
                'done': done,
                'overdue': overdue,
            },
            'story_points': {
                'total': total_sp,
                'done': done_sp,
                'remaining': total_sp - done_sp,
            },
            'velocity': done_sp,
        })


class BurndownChartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, memberships__user=request.user)
        except Project.DoesNotExist:
            return Response({'error': 'Projet introuvable.'}, status=404)

        tasks = Task.objects.filter(project=project)
        total_sp = sum(t.story_points for t in tasks)

        # Grouper les tâches terminées par date de mise à jour
        from collections import defaultdict
        done_by_date = defaultdict(int)
        for t in tasks.filter(status='done'):
            date_str = t.updated_at.date().isoformat()
            done_by_date[date_str] += t.story_points

        # Construire la courbe
        sorted_dates = sorted(done_by_date.keys())
        remaining = total_sp
        chart_data = []
        for date in sorted_dates:
            remaining -= done_by_date[date]
            chart_data.append({'date': date, 'remaining_sp': remaining})

        return Response({
            'project': project.name,
            'total_story_points': total_sp,
            'burndown': chart_data,
        })


class ActivityLogView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, memberships__user=request.user)
        except Project.DoesNotExist:
            return Response({'error': 'Projet introuvable.'}, status=404)

        tasks = Task.objects.filter(project=project).order_by('-updated_at')[:20]
        log = []
        for t in tasks:
            log.append({
                'task': t.title,
                'status': t.status,
                'assigned_to': t.assigned_to.username if t.assigned_to else None,
                'updated_at': t.updated_at.isoformat(),
            })
        return Response({'project': project.name, 'activity': log})