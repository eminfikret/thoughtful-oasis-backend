from django.urls import path

from . import controllers

urlpatterns = [
    path('analyze/', controllers.TextAnalysisController.as_view(), name='analyze-text'),
    path('<int:claim_id>/', controllers.ClaimDetailController.as_view(), name='claim-detail'),
]