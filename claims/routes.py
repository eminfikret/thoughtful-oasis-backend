from django.urls import path

from . import controllers

urlpatterns = [
    path('', controllers.ClaimController.as_view(), name='submit-claim'),
    path('<int:claim_id>/', controllers.ClaimDetailController.as_view(), name='claim-detail'),
]