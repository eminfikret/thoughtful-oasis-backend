from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ClaimSubmissionSerializer, FactualClaimSerializer
from .services import ClaimService


class ClaimSubmissionController(APIView):
    """
    Controller for submitting content for claim extraction and fact checking
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.claim_service = ClaimService()
    
    @swagger_auto_schema(
        operation_summary="Submit content for claim extraction",
        operation_description="Submit post or comment content for factual claim extraction",
        request_body=ClaimSubmissionSerializer,
        responses={
            201: openapi.Response(
                description="Claims extracted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'claims': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'content_fragment': openapi.Schema(type=openapi.TYPE_STRING),
                                }
                            )
                        )
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    def post(self, request):
        """
        Submit content for claim extraction and fact checking
        """
        serializer = ClaimSubmissionSerializer(data=request.data)
        
        if serializer.is_valid():
            content = serializer.validated_data['content']
            source_type = serializer.validated_data['source_type']
            source_id = serializer.validated_data['source_id']
            
            # Process content and extract claims
            claims = self.claim_service.process_content_for_claims(
                content, source_type, source_id
            )
            
            # Return simple response with claim IDs and fragments
            claims_data = [
                {
                    'id': claim.id, 
                    'content_fragment': claim.content_fragment
                } for claim in claims
            ]
            
            return Response({
                'message': f'Successfully extracted {len(claims)} claims',
                'claims': claims_data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClaimDetailController(APIView):
    """
    Controller for retrieving claim details including fact checks
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.claim_service = ClaimService()
    
    @swagger_auto_schema(
        operation_summary="Get claim details",
        operation_description="Get details for a specific claim including fact checks",
        responses={
            200: FactualClaimSerializer(),
            404: "Claim not found"
        }
    )
    def get(self, request, claim_id):
        """
        Get details for a specific claim
        """
        claim = self.claim_service.claim_repository.get_claim_by_id(claim_id)
        if not claim:
            return Response({"error": "Claim not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = FactualClaimSerializer(claim)
        return Response(serializer.data)