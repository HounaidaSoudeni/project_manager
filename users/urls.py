from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('me/', views.ProfileView.as_view(), name='profile'),
    path('list/', views.UserListView.as_view(), name='user-list'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]