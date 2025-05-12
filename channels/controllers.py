from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import NotFound as ChannelNotFoundAPIException
from rest_framework.exceptions import PermissionDenied as PermissionDeniedAPIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from channels.dtos import CreateChannelDto, UpdateChannelDto
from channels.exceptions import ChannelNotFoundException, UnauthorizedChannelAccessException
from channels.params import ChannelsParams
from channels.serializers import (
    ChannelCreateSerializer,
    ChannelSerializer,
    ChannelsQueryParamsSerializer,
    ChannelUpdateSerializer,
)
from channels.services import ChannelService
from channels.types import ChannelId
from common.params import PaginationParams
from common.responses import PaginatedResponse
from common.serializers import PaginatedResponseSerializer


class ChannelListController(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        operation_summary="List all channels",
        operation_description="Get a list of all channels",
        tags=["Channels"],
        query_serializer=ChannelsQueryParamsSerializer(),
        responses={
            200: openapi.Response(
                description="Paginated list of channels",
                schema=PaginatedResponseSerializer(ChannelSerializer)
            ),
            400: openapi.Response(
                description="Invalid query parameters",
                schema=ChannelsQueryParamsSerializer()
            ),
            401: openapi.Response(description="Unauthorized - Authentication required"),
        },
    )
    def get(self, request: Request):
        query_serializer = ChannelsQueryParamsSerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = ChannelsParams(**query_serializer.validated_data)

        channels = ChannelService.get_channels(
            search=params.search,
            pagination=PaginationParams(limit=params.limit, offset=params.offset)
        )
        serializer = ChannelSerializer(channels, many=True)

        count = ChannelService.get_channels_count(search=params.search)

        return PaginatedResponse(
            results=serializer.data,
            count=count,
            request=request,
        )

    @swagger_auto_schema(
        operation_summary="Create a new channel",
        operation_description="Create a new channel",
        tags=["Channels"],
        request_body=ChannelCreateSerializer,
        responses={
            201: openapi.Response(
                description="Channel created successfully",
                schema=ChannelSerializer()
            ),
            400: openapi.Response(
                description="Invalid input data",
                schema=ChannelCreateSerializer()
            ),
            401: openapi.Response(description="Unauthorized - Authentication required"),
        },
    )
    def post(self, request: Request):
        serializer = ChannelCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dto = CreateChannelDto(
            name=serializer.validated_data['name'],
            description=serializer.validated_data['description']
        )

        channel = ChannelService.create_channel(
            dto=dto,
            owner=request.user
        )

        serializer = ChannelSerializer(channel)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ChannelDetailController(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        operation_summary="Retrieve a single channel",
        operation_description="Get a channel by its ID",
        tags=["Channels"],
        responses={
            200: openapi.Response(
                description="Channel retrieved successfully",
                schema=ChannelSerializer()
            ),
            401: openapi.Response(description="Unauthorized - Authentication required"),
            404: openapi.Response(
                description=str(ChannelNotFoundException(ChannelId(123)))
            )
        }
    )
    def get(self, request: Request, pk: ChannelId):
        try:
            channel = ChannelService.get_channel_by_id(pk)
        except ChannelNotFoundException as e:
            raise ChannelNotFoundAPIException(detail=str(e))

        serializer = ChannelSerializer(channel)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Partially update a channel",
        operation_description="Update a channel's name and/or description",
        tags=["Channels"],
        request_body=ChannelUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Channel updated successfully",
                schema=ChannelSerializer()
            ),
            400: openapi.Response(
                description="Invalid input data",
                schema=ChannelUpdateSerializer()
            ),
            401: openapi.Response(description="Unauthorized - Authentication required"),
            403: openapi.Response(
                description=str(UnauthorizedChannelAccessException())
            ),
            404: openapi.Response(
                description=str(ChannelNotFoundException(ChannelId(123)))
            ),
        },
    )
    def patch(self, request: Request, pk: ChannelId):
        serializer = ChannelUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dto = UpdateChannelDto(
            name=serializer.validated_data.get('name'),
            description=serializer.validated_data.get('description')
        )

        try:
            updated_channel = ChannelService.update_channel(
                channel_id=pk,
                dto=dto,
                requester=request.user,
            )
        except ChannelNotFoundException as e:
            raise ChannelNotFoundAPIException(detail=str(e))
        except UnauthorizedChannelAccessException as e:
            raise PermissionDeniedAPIException(detail=str(e))

        output_serializer = ChannelSerializer(updated_channel)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Delete a channel",
        operation_description="Delete a channel by its ID",
        tags=["Channels"],
        responses={
            204: openapi.Response(description="Channel deleted successfully"),
            401: openapi.Response(description="Unauthorized - Authentication required"),
            403: openapi.Response(description=str(UnauthorizedChannelAccessException())),
            404: openapi.Response(description=str(ChannelNotFoundException(ChannelId(123)))),
        },
    )
    def delete(self, request: Request, pk: ChannelId):
        try:
            ChannelService.delete_channel(
                channel_id=pk,
                requester=request.user,
            )
        except ChannelNotFoundException as e:
            raise ChannelNotFoundAPIException(detail=str(e))
        except UnauthorizedChannelAccessException as e:
            raise PermissionDeniedAPIException(detail=str(e))

        return Response(status=status.HTTP_204_NO_CONTENT)
