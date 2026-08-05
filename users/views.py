from django.contrib.auth.models import User

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .serializers import RegisterSerializer, UserProfileSerializer


class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class ProfileAPIView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user