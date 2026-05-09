from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import CustomUser
from projects.models import Project, ProjectMembership
from kanban.models import Task


class AuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            username='testuser', email='test@test.com', password='test123'
        )

    def test_register(self):
        res = self.client.post('/api/users/register/', {
            'username': 'newuser', 'email': 'new@test.com', 'password': 'pass123'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_login_jwt(self):
        res = self.client.post('/api/token/', {
            'username': 'testuser', 'password': 'test123'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)

    def test_profile_requires_auth(self):
        res = self.client.get('/api/users/me/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_authenticated(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get('/api/users/me/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], 'testuser')

    def test_change_password(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post('/api/users/change-password/', {
            'old_password': 'test123', 'new_password': 'newpass456'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class ProjectTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = CustomUser.objects.create_user(username='owner', password='pass123')
        self.member = CustomUser.objects.create_user(username='member', password='pass123')
        self.client.force_authenticate(user=self.owner)

    def test_create_project(self):
        res = self.client.post('/api/projects/', {'name': 'Mon Projet', 'description': 'Test'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)

    def test_owner_is_set(self):
        self.client.post('/api/projects/', {'name': 'Projet A'})
        project = Project.objects.first()
        self.assertEqual(project.owner, self.owner)

    def test_membership_created_on_project_creation(self):
        self.client.post('/api/projects/', {'name': 'Projet B'})
        project = Project.objects.first()
        self.assertTrue(ProjectMembership.objects.filter(project=project, user=self.owner).exists())

    def test_member_cannot_delete_project(self):
        project = Project.objects.create(name='Projet C', owner=self.owner)
        ProjectMembership.objects.create(project=project, user=self.member, role='membre')
        self.client.force_authenticate(user=self.member)
        res = self.client.delete(f'/api/projects/{project.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class TaskTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(username='user1', password='pass123')
        self.project = Project.objects.create(name='Projet Test', owner=self.user)
        ProjectMembership.objects.create(project=self.project, user=self.user, role='chef')
        self.client.force_authenticate(user=self.user)

    def test_create_task(self):
        res = self.client.post('/api/kanban/tasks/', {
            'project': self.project.id,
            'title': 'Ma tâche',
            'priority': 'high',
            'story_points': 3,
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_move_task(self):
        task = Task.objects.create(project=self.project, title='Tâche 1', status='todo')
        res = self.client.patch(f'/api/kanban/tasks/{task.id}/move/', {'status': 'in_progress'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.status, 'in_progress')

    def test_duplicate_task(self):
        task = Task.objects.create(project=self.project, title='Tâche originale', story_points=5)
        res = self.client.post(f'/api/kanban/tasks/{task.id}/duplicate/')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 2)
        self.assertIn('copie', res.data['title'])

    def test_overdue_endpoint(self):
        from datetime import date, timedelta
        Task.objects.create(
            project=self.project, title='En retard',
            due_date=date.today() - timedelta(days=1), status='in_progress'
        )
        res = self.client.get('/api/kanban/tasks/overdue/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_focus_endpoint(self):
        res = self.client.get('/api/kanban/tasks/focus/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('focus_tasks', res.data)