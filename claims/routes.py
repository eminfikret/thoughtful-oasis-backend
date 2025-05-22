from django.urls import path

from . import controllers
from .controllers import (
    DeleteClaimController,
    UserClaimsController
)

urlpatterns = [
    path('analyse/', controllers.TextAnalysisController.as_view(), name='analyse-text'),
    path('<int:claim_id>/', controllers.ClaimDetailController.as_view(), name='claim-detail'),
    path('<int:claim_id>/delete', DeleteClaimController.as_view(), name='delete-claim'),
    path('user/claims', UserClaimsController.as_view(), name='user-claims'),
]