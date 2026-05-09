from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import CustomUser
from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        if not old_password or not new_password:
            return Response({'error': 'old_password et new_password sont requis.'}, status=400)
        if not user.check_password(old_password):
            return Response({'error': 'Ancien mot de passe incorrect.'}, status=400)
        if len(new_password) < 6:
            return Response({'error': 'Minimum 6 caractères.'}, status=400)
        user.set_password(new_password)
        user.save()
        return Response({'status': 'Mot de passe mis à jour.'})


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email requis.'}, status=400)
        try:
            user = CustomUser.objects.get(email=email)
            import secrets
            token = secrets.token_urlsafe(32)
            # Stocker le token temporairement dans le profil (simplifié)
            user.set_unusable_password()
            from django.core.cache import cache
            cache.set(f'reset_token_{email}', token, timeout=3600)
            return Response({
                'status': 'Token généré.',
                'reset_token': token,
                'note': 'En production ce token est envoyé par email.'
            })
        except CustomUser.DoesNotExist:
            return Response({'status': 'Si cet email existe, un lien a été envoyé.'})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        if not all([email, token, new_password]):
            return Response({'error': 'email, token et new_password requis.'}, status=400)
        from django.core.cache import cache
        cached_token = cache.get(f'reset_token_{email}')
        if not cached_token or cached_token != token:
            return Response({'error': 'Token invalide ou expiré.'}, status=400)
        try:
            user = CustomUser.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            cache.delete(f'reset_token_{email}')
            return Response({'status': 'Mot de passe réinitialisé.'})
        except CustomUser.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=404)