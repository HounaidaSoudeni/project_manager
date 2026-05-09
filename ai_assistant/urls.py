from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.ChatView.as_view(), name='ai-chat'),
    path('summary/<int:project_id>/', views.ProjectSummaryView.as_view(), name='ai-summary'),
]