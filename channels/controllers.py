from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from channels.dtos import CreateChannelDto, UpdateChannelDto
from channels.exceptions import ChannelNotFound
from channels.params import ChannelsParams
from channels.serializers import (
    ChannelCreateSerializer,
    ChannelSerializer,
    ChannelsQueryParamsSerializer,
    ChannelUpdateSerializer,
)
from channels.services import ChannelService
from channels.types import ChannelId
from common.responses import PaginatedResponse
from common.serializers import PaginatedResponseSerializer


class ChannelListController(APIView):
    @swagger_auto_schema(
        operation_summary="List all channels",
        operation_description="Get a list of all channels",
        query_serializer=ChannelsQueryParamsSerializer(),
        responses={
            200: PaginatedResponseSerializer(ChannelSerializer),
            400: ChannelsQueryParamsSerializer()
        },
    )
    def get(self, request):
        query_serializer = ChannelsQueryParamsSerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        channels_params = ChannelsParams(**query_serializer.validated_data)

        channels = ChannelService.get_all_channels(channels_params)
        serializer = ChannelSerializer(channels, many=True)

        count = ChannelService.get_channels_count()

        return PaginatedResponse(
            results=serializer.data,
            count=count,
            request=request,
        )

    @swagger_auto_schema(
        operation_summary="Create a new channel",
        operation_description="Create a new channel",
        request_body=ChannelCreateSerializer,
        responses={
            201: ChannelSerializer(),
            400: ChannelCreateSerializer(),
        },
    )
    def post(self, request):
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
    @swagger_auto_schema(
        operation_summary="Retrieve a single channel",
        operation_description="Get a channel by its ID",
        responses={
            200: ChannelSerializer(),
            404: str(ChannelNotFound(ChannelId(123))),
        }
    )
    def get(self, request, pk: ChannelId):
        try:
            channel = ChannelService.get_channel_by_id(pk)
        except ChannelNotFound as e:
            raise NotFound(detail=str(e))
        serializer = ChannelSerializer(channel)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Partially update a channel",
        operation_description="Update a channel's name and/or description",
        request_body=ChannelUpdateSerializer,
        responses={
            200: ChannelSerializer(),
            400: ChannelUpdateSerializer(),
            404: str(ChannelNotFound(ChannelId(123))),
        },
    )
    def patch(self, request, pk: ChannelId):
        serializer = ChannelUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dto = UpdateChannelDto(
            name=serializer.validated_data.get('name'),
            description=serializer.validated_data.get('description')
        )

        try:
            updated_channel = ChannelService.update_channel(
                channel_id=pk,
                dto=dto
            )
        except ChannelNotFound as e:
            raise NotFound(detail=str(e))

        output_serializer = ChannelSerializer(updated_channel)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Delete a channel",
        operation_description="Delete a channel by its ID",
        responses={
            204: "No Content",
            404: str(ChannelNotFound(ChannelId(123))),
        },
    )
    def delete(self, request, pk: ChannelId):
        try:
            ChannelService.delete_channel(pk)
        except ChannelNotFound as e:
            raise NotFound(detail=str(e))

        return Response(status=status.HTTP_204_NO_CONTENT)
