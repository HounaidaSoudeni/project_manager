from django.db import models
from django.conf import settings


class Project(models.Model):
    STATUS_CHOICES = [
        ('actif', 'Actif'),
        ('en_pause', 'En pause'),
        ('termine', 'Terminé'),
        ('archive', 'Archivé'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_projects'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='actif')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def completion_rate(self):
        total = self.tasks.count()
        if total == 0:
            return 0
        done = self.tasks.filter(status='termine').count()
        return round((done / total) * 100, 1)


class ProjectMembership(models.Model):
    ROLE_CHOICES = [
        ('chef', 'Chef de projet'),
        ('membre', 'Membre'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='membre')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')

    def __str__(self):
        return f"{self.user.username} → {self.project.name} ({self.role})"