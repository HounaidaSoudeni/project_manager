from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('chef', 'Chef de projet'),
        ('membre', 'Membre'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='membre')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"