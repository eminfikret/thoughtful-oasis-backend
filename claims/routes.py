from django.urls import path

from . import controllers

urlpatterns = [
    path('', controllers.ClaimSubmissionController.as_view(), name='claim-submission'),
    path('<int:claim_id>/', controllers.ClaimDetailController.as_view(), name='claim-detail'),
]