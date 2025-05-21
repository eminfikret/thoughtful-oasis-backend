from django.urls import path

from . import controllers

urlpatterns = [
    path('analyse/', controllers.TextAnalysisController.as_view(), name='analyse-text'),
    path('<int:claim_id>/', controllers.ClaimDetailController.as_view(), name='claim-detail'),
]