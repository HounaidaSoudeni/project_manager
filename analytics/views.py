from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone
from django.http import HttpResponse
from projects.models import Project, ProjectMembership
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
        total_sp = sum(t.story_points for t in tasks)
        done_sp = sum(t.story_points for t in tasks.filter(status='done'))

        return Response({
            'project': project.name,
            'completion_rate': project.completion_rate,
            'tasks': {
                'total': tasks.count(),
                'todo': tasks.filter(status='todo').count(),
                'in_progress': tasks.filter(status='in_progress').count(),
                'review': tasks.filter(status='review').count(),
                'done': tasks.filter(status='done').count(),
                'overdue': tasks.filter(due_date__lt=today).exclude(status='done').count(),
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

        from collections import defaultdict
        done_by_date = defaultdict(int)
        for t in tasks.filter(status='done'):
            date_str = t.updated_at.date().isoformat()
            done_by_date[date_str] += t.story_points

        remaining = total_sp
        chart_data = []
        for date in sorted(done_by_date.keys()):
            remaining -= done_by_date[date]
            chart_data.append({'date': date, 'remaining_sp': remaining})

        return Response({
            'project': project.name,
            'total_story_points': total_sp,
            'burndown': chart_data,
        })


class MemberStatsView(APIView):
    """Statistiques individuelles par membre."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, memberships__user=request.user)
        except Project.DoesNotExist:
            return Response({'error': 'Projet introuvable.'}, status=404)

        members = ProjectMembership.objects.filter(project=project).select_related('user')
        stats = []
        today = timezone.now().date()

        for m in members:
            user_tasks = Task.objects.filter(project=project, assigned_to=m.user)
            velocity = sum(t.story_points for t in user_tasks.filter(status='done'))
            stats.append({
                'username': m.user.username,
                'full_name': m.user.get_full_name(),
                'role': m.role,
                'tasks_total': user_tasks.count(),
                'tasks_done': user_tasks.filter(status='done').count(),
                'tasks_in_progress': user_tasks.filter(status='in_progress').count(),
                'tasks_overdue': user_tasks.filter(due_date__lt=today).exclude(status='done').count(),
                'velocity_sp': velocity,
                'completion_rate': round(
                    user_tasks.filter(status='done').count() / user_tasks.count() * 100, 1
                ) if user_tasks.count() > 0 else 0,
            })

        return Response({'project': project.name, 'member_stats': stats})


class ActivityLogView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, memberships__user=request.user)
        except Project.DoesNotExist:
            return Response({'error': 'Projet introuvable.'}, status=404)

        tasks = Task.objects.filter(project=project).order_by('-updated_at')[:20]
        log = [{
            'task': t.title,
            'status': t.status,
            'priority': t.priority,
            'assigned_to': t.assigned_to.username if t.assigned_to else None,
            'updated_at': t.updated_at.isoformat(),
        } for t in tasks]
        return Response({'project': project.name, 'activity': log})


class ExportPDFView(APIView):
    """Export PDF du rapport de projet."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id, memberships__user=request.user)
        except Project.DoesNotExist:
            return Response({'error': 'Projet introuvable.'}, status=404)

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            import io
        except ImportError:
            return Response({'error': 'ReportLab non installé. Lancez: pip install reportlab'}, status=500)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                                 topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []

        # Titre
        title_style = ParagraphStyle('title', parent=styles['Heading1'], alignment=TA_CENTER,
                                      fontSize=20, spaceAfter=12)
        story.append(Paragraph(f"Rapport de Projet", title_style))
        story.append(Paragraph(f"{project.name}", title_style))
        story.append(Spacer(1, 0.5*cm))

        # Infos générales
        today = timezone.now().date()
        story.append(Paragraph(f"Date du rapport: {today}", styles['Normal']))
        story.append(Paragraph(f"Statut: {project.get_status_display()}", styles['Normal']))
        story.append(Paragraph(f"Taux d'avancement: {project.completion_rate}%", styles['Normal']))
        story.append(Spacer(1, 0.5*cm))

        # KPIs
        tasks = Task.objects.filter(project=project)
        story.append(Paragraph("Résumé des tâches", styles['Heading2']))
        kpi_data = [
            ['Statut', 'Nombre'],
            ['À faire', str(tasks.filter(status='todo').count())],
            ['En cours', str(tasks.filter(status='in_progress').count())],
            ['En révision', str(tasks.filter(status='review').count())],
            ['Terminées', str(tasks.filter(status='done').count())],
            ['En retard', str(tasks.filter(due_date__lt=today).exclude(status='done').count())],
            ['Total', str(tasks.count())],
        ]
        table = Table(kpi_data, colWidths=[8*cm, 4*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#534AB7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.5*cm))

        # Liste des tâches
        story.append(Paragraph("Détail des tâches", styles['Heading2']))
        task_data = [['Titre', 'Priorité', 'Statut', 'Assigné à', 'Deadline']]
        for t in tasks.order_by('status', '-priority')[:30]:
            task_data.append([
                t.title[:40],
                t.get_priority_display(),
                t.get_status_display(),
                t.assigned_to.username if t.assigned_to else '-',
                str(t.due_date) if t.due_date else '-',
            ])
        task_table = Table(task_data, colWidths=[6*cm, 2.5*cm, 2.5*cm, 3*cm, 2.5*cm])
        task_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#534AB7')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))
        story.append(task_table)

        doc.build(story)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_{project.name}.pdf"'
        return response