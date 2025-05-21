from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Claim
from .serializers import TextSubmissionSerializer, ClaimWithFactCheckSerializer
from .services import ClaimService


class TextAnalysisController(APIView):
    """
    Controller for submitting text for claim extraction and fact checking
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @swagger_auto_schema(
        operation_summary="Submit text for claim analysis",
        operation_description=(
            "Submit text for factual claim extraction and verification. "
            "The system will identify factual claims in the text and run them through "
            "a fact-checking pipeline."
        ),
        tags=["Claims"],
        request_body=TextSubmissionSerializer,
        responses={
            201: openapi.Response(
                description="Claims extracted and fact-checked successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Text analyzed successfully"
                        ),
                        'claims_count': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=2
                        ),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'claim': openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                            'extracted_claim': openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                example="The Amazon rainforest produces 20% of the world's oxygen"
                                            ),
                                            'claim_index': openapi.Schema(
                                                type=openapi.TYPE_INTEGER,
                                                example=1
                                            )
                                        }
                                    ),
                                    'fact_check': openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'id': openapi.Schema(
                                                type=openapi.TYPE_INTEGER,
                                                example=1
                                            ),
                                            'verdict': openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                example="contradicted"
                                            ),
                                            'summary': openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                example="The claim is contradicted by available evidence. According to research, the Amazon rainforest produces approximately 6-9% of the world's oxygen, not 20%."
                                            ),
                                            'sources': openapi.Schema(
                                                type=openapi.TYPE_ARRAY,
                                                items=openapi.Schema(
                                                    type=openapi.TYPE_OBJECT,
                                                    properties={
                                                        'id': openapi.Schema(
                                                            type=openapi.TYPE_INTEGER,
                                                            example=1
                                                        ),
                                                        'url': openapi.Schema(
                                                            type=openapi.TYPE_STRING,
                                                            example="https://en.wikipedia.org/wiki/Amazon_rainforest"
                                                        ),
                                                        'title': openapi.Schema(
                                                            type=openapi.TYPE_STRING,
                                                            example="Amazon rainforest"
                                                        )
                                                    }
                                                )
                                            )
                                        }
                                    )
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request - Invalid input data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'text': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["This field is required."]
                        )
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Authentication credentials were not provided."
                        )
                    }
                )
            ),
            500: openapi.Response(
                description="Server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Error processing text"
                        )
                    }
                )
            )
        }
    )
    def post(self, request):
        """
        Submit text for claim extraction and fact checking
        """
        serializer = TextSubmissionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        text = serializer.validated_data['text']
        user_id = request.user.id
        
        try:
            claim_service = ClaimService()
            results = claim_service.process_raw_text(user_id, text)
            
            return Response({
                'message': "Text analyzed successfully",
                'claims_count': len(results),
                'results': results
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f"Error processing text: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
                        'claim': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                'extracted_claim': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="The Amazon rainforest produces 20% of the world's oxygen"
                                ),
                                'source_type': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="raw"
                                ),
                                'claim_index': openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    example=1
                                ),
                                'created_at': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    format=openapi.FORMAT_DATETIME,
                                    example="2025-05-14T10:30:45.123Z"
                                )
                            }
                        ),
                        'fact_check': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    example=1
                                ),
                                'verdict': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="contradicted"
                                ),
                                'summary': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="The claim is contradicted by available evidence."
                                ),
                                'sources': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'id': openapi.Schema(
                                                type=openapi.TYPE_INTEGER,
                                                example=1
                                            ),
                                            'url': openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                example="https://en.wikipedia.org/wiki/Amazon_rainforest"
                                            ),
                                            'title': openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                example="Amazon rainforest"
                                            ),
                                            'description': openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                example="The Amazon rainforest, also called the Amazonia, Amazon jungle or Amazonian forest..."
                                            )
                                        }
                                    )
                                )
                            }
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
            401: openapi.Response(
                description="Unauthorized",
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
    def get(self, request, claim_id):
        """
        Get details for a specific claim
        """
        try:
            claim_service = ClaimService()
            result = claim_service.get_claim_with_fact_check(claim_id)
            
            if not result:
                return Response({"error": "Claim not found"}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(result)
            
        except Exception as e:
            return Response(
                {'error': f"Error retrieving claim: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )