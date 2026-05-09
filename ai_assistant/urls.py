from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.ChatView.as_view(), name='ai-chat'),
    path('summary/<int:project_id>/', views.ProjectSummaryView.as_view(), name='ai-summary'),
    path('prioritize/<int:project_id>/', views.PrioritizeTasksView.as_view(), name='ai-prioritize'),
    path('detect-blocked/<int:project_id>/', views.DetectBlockedTasksView.as_view(), name='ai-blocked'),
    path('standup/', views.DailyStandupView.as_view(), name='ai-standup'),
]