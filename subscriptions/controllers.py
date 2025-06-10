from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import NotFound as NotFoundAPIException
from rest_framework.exceptions import PermissionDenied as PermissionDeniedAPIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from channels.exceptions import ChannelNotFoundException
from channels.types import ChannelId
from common.exceptions import NotFoundException, PermissionDeniedException
from common.params import PaginationParams
from common.responses import PaginatedResponse
from common.serializers import PaginatedResponseSerializer
from common.swagger_schemas import (
    unauthorized_response,
    permission_denied_response,
    not_found_response,
    subscribers_paginated_response,
    subscriptions_paginated_response
)
from subscriptions.exceptions import SubscriptionPermissionDeniedException
from subscriptions.params import SubscriptionsParams
from subscriptions.serializers import (
    SubscriberSerializer,
    SubscribersQueryParamsSerializer,
    SubscriptionSerializer,
    SubscriptionsQueryParamsSerializer,
)
from subscriptions.services import SubscriptionService
from users.exceptions import UserNotFoundException
from users.types import UserId


class SubscribersListController(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        operation_summary="List subscribers of a channel",
        operation_description=(
            "Returns all users subscribed to a given channel. "
            "Only accessible by channel owner or admin."
        ),
        tags=["Subscriptions"],
        query_serializer=SubscribersQueryParamsSerializer(),
        responses={
            200: openapi.Response(
                description="Paginated list of subscribers",
                schema=subscribers_paginated_response()
            ),
            400: openapi.Response(
                description="Invalid query parameters",
                schema=SubscribersQueryParamsSerializer()
            ),
            401: unauthorized_response(),
            403: permission_denied_response("You do not have permission to view subscribers."),
            404: not_found_response(f"Channel with id 123 not found."),
        },
    )
    def get(self, request: Request, channel_id: ChannelId):
        query_serializer = SubscribersQueryParamsSerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = SubscriptionsParams(**query_serializer.validated_data)

        try:
            subscribers = SubscriptionService.get_subscriptions_by_channel_id(
                channel_id=channel_id,
                requester=request.user,
                pagination=PaginationParams(limit=params.limit, offset=params.offset),
            )
            count = SubscriptionService.get_subscriptions_count_by_channel_id(
                channel_id=channel_id,
                requester=request.user
            )
        except NotFoundException as e:
            raise NotFoundAPIException(detail=str(e))
        except PermissionDeniedException as e:
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
            "Subscribes the authenticated user to the specified channel by ID. "
            "Does nothing if already subscribed."
        ),
        tags=["Subscriptions"],
        responses={
            204: openapi.Response(description="Subscribed successfully (no content)"),
            401: unauthorized_response(),
            404: not_found_response(f"Channel with id 123 not found."),
        },
    )
    def post(self, request: Request, channel_id: ChannelId):
        try:
            SubscriptionService.subscribe(channel_id, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except NotFoundException as e:
            raise NotFoundAPIException(str(e))


class UnsubscribeController(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        operation_summary="Unsubscribe from a channel",
        operation_description=(
            "Unsubscribes the authenticated user from the specified channel by ID. "
            "Does nothing if not already subscribed."
        ),
        tags=["Subscriptions"],
        responses={
            204: openapi.Response(description="Unsubscribed successfully (no content)"),
            401: unauthorized_response(),
            404: not_found_response(f"Channel with id 123 not found."),
        },
    )
    def delete(self, request: Request, channel_id: ChannelId):
        try:
            SubscriptionService.unsubscribe(channel_id=channel_id, subscriber=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except NotFoundException as e:
            raise NotFoundAPIException(str(e))


class SubscriptionsListController(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        operation_summary="List user subscriptions",
        operation_description=(
            "Returns a paginated list of channels a specific user is subscribed to. "
            "Accessible by the user themselves or by an admin."
        ),
        tags=["Subscriptions"],
        query_serializer=SubscriptionsQueryParamsSerializer(),
        responses={
            200: openapi.Response(
                description="Paginated list of subscribed channels",
                schema=subscriptions_paginated_response()
            ),
            400: openapi.Response(
                description="Invalid query parameters",
                schema=SubscriptionsQueryParamsSerializer()
            ),
            401: unauthorized_response(),
            403: permission_denied_response("You don't have permission to view this user's subscriptions."),
            404: not_found_response(f"User with id 123 not found."),
        },
    )
    def get(self, request: Request, user_id: UserId):
        query_serializer = SubscriptionsQueryParamsSerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = SubscriptionsParams(**query_serializer.validated_data)

        try:
            subscriptions = SubscriptionService.get_subscriptions_by_user_id(
                user_id=user_id,
                requester=request.user,
                pagination=PaginationParams(limit=params.limit, offset=params.offset),
            )
            count = SubscriptionService.get_subscriptions_count_by_user_id(
                user_id=user_id,
                requester=request.user,
            )
        except NotFoundException as e:
            raise NotFoundAPIException(str(e))
        except PermissionDeniedException as e:
            raise PermissionDeniedAPIException(detail=str(e))

        serializer = SubscriptionSerializer(subscriptions, many=True)
        return PaginatedResponse(
            results=serializer.data,
            count=count,
            request=request,
        )

