from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import NotFound as ChannelNotFoundAPIException
from rest_framework.exceptions import PermissionDenied as PermissionDeniedAPIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from channels.exceptions import ChannelNotFoundException
from channels.types import ChannelId
from common.responses import PaginatedResponse
from common.serializers import PaginatedResponseSerializer
from subscriptions.exceptions import UnauthorizedSubscriptionAccessException
from subscriptions.params import SubscriptionsParams
from subscriptions.serializers import (
    MySubscriptionSerializer,
    SubscriberSerializer,
    SubscribersQueryParamsSerializer,
    SubscriptionsQueryParamsSerializer,
)
from subscriptions.services import SubscriptionService


class SubscribersListController(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        operation_summary="List subscribers of a channel",
        operation_description=(
            "Returns all users subscribed to a given channel."
            "Only accessible by channel owner or admin."
        ),
        tags=["Subscriptions"],
        responses={
            200: openapi.Response(
                description="Paginated list of subscribers",
                schema=PaginatedResponseSerializer(Serializer)
            ),
            400: openapi.Response(
                description="Invalid query parameters",
                schema=SubscribersQueryParamsSerializer()
            ),
            401: openapi.Response(description="Unauthorized - Authentication required"),
            403: openapi.Response(
                description=str(UnauthorizedSubscriptionAccessException())
            ),
            404: openapi.Response(
                description=str(ChannelNotFoundException(ChannelId(123)))
            ),
        },
    )
    def get(self, request, pk: ChannelId):
        query_serializer = SubscribersQueryParamsSerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = SubscriptionsParams(**query_serializer.validated_data)

        try:
            subscribers = SubscriptionService.get_subscriptions_by_channel(
                channel_id=pk,
                params=params,
                user=request.user
            )
            count = SubscriptionService.get_subscriptions_count()
        except ChannelNotFoundException as e:
            raise ChannelNotFoundAPIException(detail=str(e))
        except UnauthorizedSubscriptionAccessException as e:
            raise PermissionDeniedAPIException(detail=str(e))

        serializer = SubscriberSerializer(subscribers, many=True)
        return PaginatedResponse(
            results=serializer.data,
            count=count,
            request=request,
        )

class SubscribeController(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        operation_summary="Subscribe to a channel",
        operation_description=(
            "Subscribes the authenticated user to the specified channel by ID."
            "Does nothing if already subscribed."
        ),
        tags=["Subscriptions"],
        responses={
            204: openapi.Response(description="Subscribed successfully (no content)"),
            401: openapi.Response(description="Unauthorized - Authentication required"),
            404: openapi.Response(description=str(ChannelNotFoundException(ChannelId(123)))),
        },
    )
    def post(self, request: Request, pk: ChannelId):
        try:
            SubscriptionService.subscribe(pk, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ChannelNotFoundException as e:
            raise ChannelNotFoundAPIException(str(e))

class UnsubscribeController(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        operation_summary="Unsubscribe from a channel",
        operation_description=(
                "Unsubscribes the authenticated user from the specified channel by ID."
                "Does nothing if not already subscribed."
        ),
        tags=["Subscriptions"],
        responses={
            204: openapi.Response(description="Unsubscribed successfully (no content)"),
            401: openapi.Response(description="Unauthorized - Authentication required"),
            404: openapi.Response(description=str(ChannelNotFoundException(ChannelId(123)))),
        },
    )
    def delete(self, request: Request, pk: ChannelId):
        try:
            SubscriptionService.unsubscribe(channel_id=pk, subscriber=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ChannelNotFoundException as e:
            raise ChannelNotFoundAPIException(str(e))

class MySubscriptionsController(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        operation_summary="List my subscriptions",
        operation_description=(
                "Returns a paginated list of channels the authenticated user is subscribed to."
        ),
        tags=["Subscriptions"],
        query_serializer=SubscriptionsQueryParamsSerializer(),
        responses={
            200: openapi.Response(
                description="Paginated list of subscribed channels",
                schema=PaginatedResponseSerializer(MySubscriptionSerializer)
            ),
            400: openapi.Response(
                description="Invalid query parameters",
                schema=SubscriptionsQueryParamsSerializer()
            ),
            401: openapi.Response(description="Unauthorized - Authentication required"),
        },
    )
    def get(self, request: Request):
        query_serializer = SubscriptionsQueryParamsSerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = SubscriptionsParams(**query_serializer.validated_data)

        subscriptions = SubscriptionService.get_subscriptions_by_subscriber(
            subscriber=request.user,
            params=params,
        )
        count = SubscriptionService.get_subscriptions_count(subscriber=request.user)

        serializer = MySubscriptionSerializer(subscriptions, many=True)
        return PaginatedResponse(
            results=serializer.data,
            count=count,
            request=request,
        )

