from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notifications'),
    path('<int:notif_id>/read/', views.MarkReadView.as_view(), name='notif-read'),
    path('read-all/', views.MarkAllReadView.as_view(), name='notif-read-all'),
    path('alerts/', views.DeadlineAlertsView.as_view(), name='deadline-alerts'),
]