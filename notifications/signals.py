from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from kanban.models import Task
from .models import Notification


@receiver(pre_save, sender=Task)
def track_task_changes(sender, instance, **kwargs):
    """Mémorise l'état précédent de la tâche avant sauvegarde."""
    if instance.pk:
        try:
            instance._old = Task.objects.get(pk=instance.pk)
        except Task.DoesNotExist:
            instance._old = None
    else:
        instance._old = None


@receiver(post_save, sender=Task)
def create_task_notifications(sender, instance, created, **kwargs):
    """Crée des notifications automatiques selon les changements."""

    # Nouvelle tâche assignée
    if created and instance.assigned_to:
        Notification.objects.create(
            user=instance.assigned_to,
            type='task_assigned',
            message=f'Vous avez été assigné à la tâche "{instance.title}" dans le projet "{instance.project.name}".'
        )
        return

    # Réassignation d'une tâche existante
    if not created and instance._old:
        old = instance._old
        if old.assigned_to != instance.assigned_to and instance.assigned_to:
            Notification.objects.create(
                user=instance.assigned_to,
                type='task_assigned',
                message=f'La tâche "{instance.title}" vous a été réassignée dans "{instance.project.name}".'
            )

        # Tâche passée en retard
        from django.utils import timezone
        if (
            instance.due_date and
            instance.due_date < timezone.now().date() and
            instance.status != 'done' and
            old.status != 'done'
        ):
            if instance.assigned_to:
                Notification.objects.create(
                    user=instance.assigned_to,
                    type='task_overdue',
                    message=f'La tâche "{instance.title}" est en retard (échéance: {instance.due_date}).'
                )
            # Notifier aussi le chef de projet
            from projects.models import ProjectMembership
            chefs = ProjectMembership.objects.filter(
                project=instance.project, role='chef'
            ).select_related('user')
            for chef_membership in chefs:
                if chef_membership.user != instance.assigned_to:
                    Notification.objects.create(
                        user=chef_membership.user,
                        type='task_overdue',
                        message=f'Alerte retard : "{instance.title}" dans "{instance.project.name}".'
                    )