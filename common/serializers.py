from typing import Type

from rest_framework import serializers

from common.constants import Pagination


class PaginationQueryParams(serializers.Serializer):
    limit = serializers.IntegerField(
        required=False,
        min_value=Pagination.MIN_LIMIT,
        max_value=Pagination.MAX_LIMIT,
        default=Pagination.DEFAULT_LIMIT)
    offset = serializers.IntegerField(
        required=False,
        min_value=Pagination.MIN_OFFSET,
        default=Pagination.DEFAULT_OFFSET)

class PaginatedResponseSerializer:
    def __new__(
        cls,
        item_serializer_class: Type[serializers.Serializer] | Type[serializers.ModelSerializer]
    ) -> Type[serializers.Serializer]:
        class _PaginatedSerializer(serializers.Serializer):
            count = serializers.IntegerField()
            next = serializers.CharField(allow_null=True)
            previous = serializers.CharField(allow_null=True)
            results = item_serializer_class(many=True)

        _PaginatedSerializer.__name__ = f"Paginated{item_serializer_class.__name__}Response"
        return _PaginatedSerializer