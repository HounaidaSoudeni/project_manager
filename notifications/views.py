from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone
from datetime import timedelta
from kanban.models import Task
from .models import Notification


class NotificationListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifs = Notification.objects.filter(user=request.user)[:30]
        data = [{
            'id': n.id,
            'type': n.type,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat(),
        } for n in notifs]
        unread = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'notifications': data, 'unread_count': unread})


class MarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, notif_id):
        try:
            notif = Notification.objects.get(id=notif_id, user=request.user)
            notif.is_read = True
            notif.save()
            return Response({'status': 'Lu.'})
        except Notification.DoesNotExist:
            return Response({'error': 'Introuvable.'}, status=404)


class MarkAllReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': f'{count} notifications marquées comme lues.'})


class DeadlineAlertsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        in_3_days = today + timedelta(days=3)
        tasks = Task.objects.filter(
            assigned_to=request.user,
            due_date__range=[today, in_3_days],
        ).exclude(status='done')
        data = [{
            'id': t.id,
            'title': t.title,
            'project': t.project.name,
            'due_date': t.due_date.isoformat(),
            'priority': t.priority,
            'status': t.status,
        } for t in tasks]
        return Response({'alerts': data, 'count': len(data)})