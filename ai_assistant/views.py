import requests
from django.conf import settings
from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from kanban.models import Task
from projects.models import Project


def call_claude(messages, system_prompt="Tu es un assistant de gestion de projets. Réponds en français."):
    payload = {
        "model": "claude-sonnet-4-5",
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": messages
    }
    headers = {
        "x-api-key": settings.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        json=payload, headers=headers, timeout=30
    )
    response.raise_for_status()
    return response.json()['content'][0]['text']


def get_project_context(user):
    projects = Project.objects.filter(memberships__user=user)
    lines = []
    for p in projects:
        tasks = Task.objects.filter(project=p)
        from django.utils import timezone
        overdue = tasks.filter(due_date__lt=timezone.now().date()).exclude(status='done').count()
        lines.append(
            f"- Projet '{p.name}' ({p.status}): {tasks.count()} tâches, "
            f"{p.completion_rate}% terminé, {overdue} en retard"
        )
    return "\n".join(lines) if lines else "Aucun projet."


class ChatView(APIView):
    """Chat conversationnel avec historique de session."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user_message = request.data.get('message', '').strip()
        history = request.data.get('history', [])

        if not user_message:
            return Response({'error': 'Message vide.'}, status=400)

        context = get_project_context(request.user)
        system = f"""Tu es un assistant intelligent intégré dans une plateforme de gestion de projets.
Tu aides à prioriser les tâches, anticiper les retards, et améliorer la productivité.
Réponds toujours en français, de façon concise et actionnable.

Contexte des projets de {request.user.username} :
{context}"""

        messages = history + [{"role": "user", "content": user_message}]

        try:
            reply = call_claude(messages, system)
            return Response({
                'reply': reply,
                'history': messages + [{"role": "assistant", "content": reply}]
            })
        except requests.exceptions.RequestException as e:
            return Response({'error': f'Erreur API Claude: {str(e)}'}, status=503)


class ProjectSummaryView(APIView):
    """Résumé hebdomadaire IA d'un projet."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, memberships__user=request.user)
        except Project.DoesNotExist:
            return Response({'error': 'Projet introuvable.'}, status=404)

        from django.utils import timezone
        tasks = Task.objects.filter(project=project)
        overdue = tasks.filter(due_date__lt=timezone.now().date()).exclude(status='done')

        prompt = f"""Génère un résumé hebdomadaire structuré du projet '{project.name}':
Tâches: {tasks.filter(status='todo').count()} à faire, {tasks.filter(status='in_progress').count()} en cours,
{tasks.filter(status='review').count()} en révision, {tasks.filter(status='done').count()} terminées.
Tâches en retard: {overdue.count()} ({', '.join([t.title for t in overdue[:5]])})
Avancement global: {project.completion_rate}%

Fournis: 1) État général 2) Points bloquants 3) Recommandations prioritaires 4) Prévision de fin."""

        try:
            summary = call_claude([{"role": "user", "content": prompt}])
            return Response({'project': project.name, 'summary': summary})
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=503)


class PrioritizeTasksView(APIView):
    """IA priorise les tâches d'un projet."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, memberships__user=request.user)
        except Project.DoesNotExist:
            return Response({'error': 'Projet introuvable.'}, status=404)

        from django.utils import timezone
        today = timezone.now().date()
        tasks = Task.objects.filter(project=project).exclude(status='done')

        task_list = "\n".join([
            f"- ID:{t.id} | '{t.title}' | priorité:{t.priority} | statut:{t.status} | "
            f"deadline:{t.due_date or 'non définie'} | assigné à:{t.assigned_to.username if t.assigned_to else 'personne'} | "
            f"story points:{t.story_points}"
            for t in tasks
        ])

        prompt = f"""Analyse ces tâches du projet '{project.name}' et donne un ordre de priorité d'exécution.
Date aujourd'hui: {today}

Tâches:
{task_list if task_list else 'Aucune tâche active.'}

Pour chaque tâche, indique:
1. Rang de priorité (1 = le plus urgent)
2. Raison courte
3. Action recommandée

Ensuite donne 3 recommandations globales pour l'équipe."""

        try:
            analysis = call_claude([{"role": "user", "content": prompt}])
            return Response({'project': project.name, 'prioritization': analysis, 'tasks_analyzed': tasks.count()})
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=503)


class DetectBlockedTasksView(APIView):
    """IA détecte les tâches bloquées ou à risque."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, memberships__user=request.user)
        except Project.DoesNotExist:
            return Response({'error': 'Projet introuvable.'}, status=404)

        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()

        tasks = Task.objects.filter(project=project).exclude(status='done')
        blocked = []

        for t in tasks:
            reasons = []
            if t.due_date and t.due_date < today:
                reasons.append(f"en retard de {(today - t.due_date).days} jours")
            if t.status == 'in_progress' and t.updated_at.date() < today - timedelta(days=3):
                reasons.append("aucune mise à jour depuis 3+ jours")
            if not t.assigned_to:
                reasons.append("non assignée")
            if t.due_date and t.due_date <= today + timedelta(days=2) and t.status == 'todo':
                reasons.append("deadline dans 2 jours mais pas encore commencée")
            if reasons:
                blocked.append({
                    'id': t.id,
                    'title': t.title,
                    'status': t.status,
                    'priority': t.priority,
                    'assigned_to': t.assigned_to.username if t.assigned_to else None,
                    'due_date': t.due_date.isoformat() if t.due_date else None,
                    'risk_reasons': reasons,
                })

        task_summary = "\n".join([
            f"- '{b['title']}': {', '.join(b['risk_reasons'])}" for b in blocked
        ])

        recommendations = "Aucune tâche bloquée détectée."
        if blocked:
            try:
                prompt = f"""Ces tâches du projet '{project.name}' semblent bloquées ou à risque:
{task_summary}

Donne des recommandations concrètes pour débloquer chaque situation en 1-2 phrases par tâche."""
                recommendations = call_claude([{"role": "user", "content": prompt}])
            except Exception:
                recommendations = "Impossible de contacter l'IA pour les recommandations."

        return Response({
            'project': project.name,
            'blocked_tasks': blocked,
            'blocked_count': len(blocked),
            'ai_recommendations': recommendations,
        })


class DailyStandupView(APIView):
    """Smart Daily Standup — rapport quotidien personnalisé par membre."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.utils import timezone
        today = timezone.now().date()
        user = request.user

        my_tasks = Task.objects.filter(
            project__memberships__user=user,
            assigned_to=user
        ).exclude(status='done')

        done_today = Task.objects.filter(
            assigned_to=user,
            status='done',
            updated_at__date=today
        )

        task_info = "\n".join([
            f"- '{t.title}' ({t.status}) — deadline: {t.due_date or 'non définie'}"
            for t in my_tasks[:10]
        ])
        done_info = "\n".join([f"- '{t.title}'" for t in done_today])

        prompt = f"""Génère un Daily Standup pour {user.get_full_name() or user.username} (date: {today}):

Tâches actives:
{task_info or 'Aucune tâche active.'}

Terminées aujourd'hui:
{done_info or 'Aucune tâche terminée aujourd\'hui.'}

Format: 1) Ce qui a été fait 2) Ce qui est prévu aujourd'hui 3) Blocages potentiels.
Sois concis (max 150 mots)."""

        try:
            standup = call_claude([{"role": "user", "content": prompt}])
            return Response({
                'user': user.username,
                'date': today.isoformat(),
                'standup': standup,
                'active_tasks': my_tasks.count(),
                'done_today': done_today.count(),
            })
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=503)