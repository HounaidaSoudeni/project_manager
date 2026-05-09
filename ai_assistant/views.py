import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from kanban.models import Task
from projects.models import Project


def build_project_context(user):
    projects = Project.objects.filter(memberships__user=user)
    context = []
    for p in projects:
        tasks = Task.objects.filter(project=p)
        overdue = tasks.filter(status__in=['todo', 'in_progress', 'review'])
        context.append(
            f"Projet '{p.name}' (statut: {p.status}) — "
            f"{tasks.count()} tâches, avancement: {p.completion_rate}%, "
            f"tâches en retard potentiel: {overdue.count()}"
        )
    return "\n".join(context)


class ChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user_message = request.data.get('message', '').strip()
        if not user_message:
            return Response({'error': 'Message vide.'}, status=400)

        project_context = build_project_context(request.user)

        system_prompt = f"""Tu es un assistant intelligent intégré dans une plateforme de gestion de projets.
Tu aides l'équipe à prioriser les tâches, anticiper les retards, et améliorer leur productivité.
Réponds toujours en français, de façon concise et actionnable.

Contexte actuel des projets de l'utilisateur :
{project_context if project_context else "Aucun projet trouvé."}
"""

        payload = {
            "model": "claude-sonnet-4-5",
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_message}
            ]
        }

        headers = {
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            reply = data['content'][0]['text']
            return Response({'reply': reply})
        except requests.exceptions.RequestException as e:
            return Response({'error': f'Erreur API Claude : {str(e)}'}, status=503)


class ProjectSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, memberships__user=request.user)
        except Project.DoesNotExist:
            return Response({'error': 'Projet introuvable.'}, status=404)

        tasks = Task.objects.filter(project=project)
        todo = tasks.filter(status='todo').count()
        in_progress = tasks.filter(status='in_progress').count()
        review = tasks.filter(status='review').count()
        done = tasks.filter(status='done').count()

        from django.utils import timezone
        overdue = tasks.filter(due_date__lt=timezone.now().date()).exclude(status='done')

        prompt = f"""Génère un résumé hebdomadaire du projet '{project.name}' :
- Tâches à faire : {todo}
- En cours : {in_progress}
- En révision : {review}
- Terminées : {done}
- Tâches en retard : {overdue.count()} ({', '.join([t.title for t in overdue[:5]])})
- Taux d'avancement : {project.completion_rate}%

Donne un résumé structuré avec : état général, points bloquants, recommandations prioritaires."""

        payload = {
            "model": "claude-sonnet-4-5",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]
        }
        headers = {
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                json=payload, headers=headers, timeout=30
            )
            response.raise_for_status()
            summary = response.json()['content'][0]['text']
            return Response({'project': project.name, 'summary': summary})
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=503)