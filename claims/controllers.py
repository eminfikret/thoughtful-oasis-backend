from django.core.exceptions import FieldError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from .serializers import TextSubmissionSerializer
from .services import ClaimService
from common.swagger_schemas import (
    unauthorized_response, 
    claim_with_fact_check_example,
    error_response,
    not_found_response,
    permission_denied_response
)


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
                            example="Text analysed successfully"
                        ),
                        'claims_count': openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=2
                        ),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=claim_with_fact_check_example()
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
            401: unauthorized_response(),
            500: openapi.Response(
                description="Server error",
                schema=error_response("Error processing text", "Error processing text")
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
                'message': "Text analysed successfully",
                'claims_count': len(results),
                'results': results
            }, status=status.HTTP_201_CREATED)
            
        except Exception:
            return Response(
                {'error': "Error processing text"},
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
        operation_description="Get detailed information about a specific claim including its fact check if available",
        tags=["Claims"],
        responses={
            200: openapi.Response(
                description="Claim details retrieved successfully",
                schema=claim_with_fact_check_example()
            ),
            401: unauthorized_response(),
            404: not_found_response("Claim not found"),
            500: openapi.Response(
                description="Server error",
                schema=error_response("Error retrieving claim", "Database error")
            )
        }
    )
    def get(self, request, claim_id: int):
        """Get claim details"""
        try:
            claim_service = ClaimService()
            result = claim_service.get_claim_with_fact_check(claim_id)
            
            if not result:
                return Response({"error": "Claim not found"}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(result)
        
        except FieldError:
    
            return Response(
                {'error': "Database schema mismatch. Run migrations to update the database."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        except Exception as e:
            return Response(
                {'error': f"Error retrieving claim: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DeleteClaimController(APIView):
    """
    Controller for deleting a user's claim
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @swagger_auto_schema(
        operation_summary="Delete a claim",
        operation_description="Delete a specific claim owned by the current user",
        tags=["Claims"],
        responses={
            200: openapi.Response(
                description="Claim deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Claim deleted successfully"
                        )
                    }
                )
            ),
            401: unauthorized_response(),
            403: permission_denied_response("You don't have permission to delete this claim"),
            404: not_found_response("Claim not found"),
        }
    )
    def delete(self, request, claim_id: int):
        """Delete a claim owned by the current user"""
        user_id = request.user.id
        
        try:
            claim_service = ClaimService()
            success, message = claim_service.delete_claim(claim_id, user_id)
            
            if success:
                return Response({'message': message}, status=status.HTTP_200_OK)
            elif message == "Claim not found":
                return Response({'error': message}, status=status.HTTP_404_NOT_FOUND)
            elif message == "You don't have permission to delete this claim":
                return Response({'error': message}, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({'error': message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response(
                {'error': f"Error deleting claim: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserClaimsController(APIView):
    """
    Controller for retrieving the current user's claims
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @swagger_auto_schema(
        operation_summary="Get current user's claims",
        operation_description="Retrieve a list of all claims created by the current user",
        tags=["Claims"],
        responses={
            200: openapi.Response(
                description="User claims retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=claim_with_fact_check_example()
                )
            ),
            401: unauthorized_response(),
            500: openapi.Response(
                description="Server error",
                schema=error_response("Error retrieving claims", "Database error")
            )
        }
    )
    def get(self, request):
        """Get claims for the current user"""
        user_id = request.user.id
        
        try:
            claim_service = ClaimService()
            claims = claim_service.get_user_claims(user_id)
            
            return Response({
                'claims_count': len(claims),
                'claims': claims
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f"Error retrieving claims: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )