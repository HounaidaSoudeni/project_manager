from django.urls import path
from . import views

urlpatterns = [
    path('kpi/<int:project_id>/', views.ProjectKPIView.as_view(), name='project-kpi'),
    path('burndown/<int:project_id>/', views.BurndownChartView.as_view(), name='burndown'),
    path('activity/<int:project_id>/', views.ActivityLogView.as_view(), name='activity-log'),
]