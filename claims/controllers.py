from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Claim
from .serializers import ClaimSerializer


class ClaimController(APIView):
    """
    Controller for submitting claims for fact checking
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @swagger_auto_schema(
        operation_summary="Submit a claim",
        operation_description=(
            "Submit a claim for verification. This endpoint allows submitting "
            "standalone claims that aren't attached to posts or comments."
        ),
        tags=["Claims"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['content'],
            properties={
                'content': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The claim text to be fact-checked",
                    example="The Great Wall of China is visible from the Moon with the naked eye."
                ),
                'content_position': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Optional position data if this claim is extracted from larger content",
                    properties={
                        'start': openapi.Schema(type=openapi.TYPE_INTEGER, example=0),
                        'end': openapi.Schema(type=openapi.TYPE_INTEGER, example=67),
                    },
                    example={"start": 0, "end": 67}
                ),
            }
        ),
        responses={
            201: openapi.Response(
                description="Claim submitted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Claim submitted successfully for fact checking"
                        ),
                        'claim': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    example=1
                                ),
                                'content_fragment': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="The Great Wall of China is visible from the Moon with the naked eye."
                                ),
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request - Invalid input data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'content': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["This field is required."]
                        )
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized - Authentication credentials were not provided or are invalid",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Authentication credentials were not provided."
                        )
                    }
                )
            )
        }
    )
    def post(self, request):
        """
        Submit a claim for verification
        """
        serializer = ClaimSerializer(data=request.data)
        
        if serializer.is_valid():
            content = serializer.validated_data['content']
            content_position = serializer.validated_data.get('content_position') or {"start": 0, "end": len(content)}
            
            # Create a standalone claim (not tied to post or comment)
            claim = Claim.objects.create(
                post_id=None,
                comment_id=None,
                content_fragment=content,
                content_position=content_position
            )
            
            # In the future, this will trigger the async fact-checking pipeline
            # For now, just return the created claim
            
            return Response({
                'message': 'Claim submitted successfully for fact checking',
                'claim': {
                    'id': claim.id,
                    'content_fragment': claim.content_fragment
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClaimDetailController(APIView):
    """
    Controller for retrieving claim details
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @swagger_auto_schema(
        operation_summary="Get claim details",
        operation_description="Get details for a specific claim by ID",
        tags=["Claims"],
        responses={
            200: openapi.Response(
                description="Successful operation",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                        'content_fragment': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="The Great Wall of China is visible from the Moon with the naked eye."
                        ),
                        'post_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=None, nullable=True),
                        'comment_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=None, nullable=True),
                        'content_position': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            example={"start": 0, "end": 67}
                        ),
                        'created_at': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            format=openapi.FORMAT_DATETIME,
                            example="2025-05-14T10:30:45.123Z"
                        )
                    }
                )
            ),
            404: openapi.Response(
                description="Claim not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            example="Claim not found"
                        )
                    }
                )
            ),
        }
    )
    def get(self, request, claim_id):
        """
        Get details for a specific claim
        """
        try:
            claim = Claim.objects.get(id=claim_id)
        except Claim.DoesNotExist:
            return Response({"error": "Claim not found"}, status=status.HTTP_404_NOT_FOUND)
        
        result = {
            'id': claim.id,
            'content_fragment': claim.content_fragment,
            'post_id': claim.post_id,
            'comment_id': claim.comment_id,
            'content_position': claim.content_position,
            'created_at': claim.created_at
        }
        
        return Response(result)