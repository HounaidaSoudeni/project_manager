from django.urls import path
from . import views
 
urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('me/', views.ProfileView.as_view(), name='profile'),
    path('list/', views.UserListView.as_view(), name='user-list'),
]
 