from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ChannelSerializer
from .services import ChannelService


class ChannelListController(APIView):
    """Controller for channel listing and creation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_service = ChannelService()
    
    def get(self, request):
        """Get all channels"""
        channels = self.channel_service.get_all_channels()
        serializer = ChannelSerializer(channels, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new channel"""
        serializer = ChannelSerializer(data=request.data)
        if serializer.is_valid():
            # Use AnonymousUser if not authenticated (for testing)
            user = request.user
            if user.is_anonymous:
                # For demonstration purposes: get or create a demo user
                from django.contrib.auth.models import User
                user, _ = User.objects.get_or_create(
                    username='demo_user',
                    defaults={'email': 'demo@example.com'}
                )
                
            channel = self.channel_service.create_channel(
                user=user,
                name=serializer.validated_data['name'],
                description=serializer.validated_data['description']
            )
            return Response(ChannelSerializer(channel).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)