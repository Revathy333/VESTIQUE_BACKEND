from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import FCMToken

class SaveFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get('fcm_token', '').strip()
        if not token:
            return Response({'error': 'fcm_token is required'}, status=status.HTTP_400_BAD_REQUEST)
        FCMToken.objects.update_or_create(
            user=request.user,
            defaults={'token': token},
        )
        return Response({'message': 'Token saved'})
