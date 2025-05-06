from typing import Any, List

from rest_framework.request import Request
from rest_framework.response import Response

from common.constants import Pagination


class PaginatedResponse(Response):
    def __init__(
            self,
            results: List[Any],
            count: int,
            request: Request,
    ):
        original_query_dict = request.query_params.copy()
        base_url = request.build_absolute_uri(request.path)

        limit = int(original_query_dict.get("limit", Pagination.DEFAULT_LIMIT))
        offset = int(original_query_dict.get("offset", Pagination.DEFAULT_OFFSET))

        next_offset = offset + limit
        previous_offset = max(offset - limit, 0)

        data: dict[str, Any] = {
            "count": count,
            "results": results,
        }

        if next_offset < count:
            next_query_dict = original_query_dict.copy()
            remaining = count - next_offset
            adjusted_limit = min(limit, remaining)

            next_query_dict["limit"] = str(adjusted_limit)
            next_query_dict["offset"] = str(next_offset)

            data["next"] = f"{base_url}?{next_query_dict.urlencode()}"

        if offset > 0:
            previous_query_dict = original_query_dict.copy()
            previous_limit = min(limit, offset)

            previous_query_dict["limit"] = str(previous_limit)
            previous_query_dict["offset"] = str(previous_offset)

            data["previous"] = f"{base_url}?{previous_query_dict.urlencode()}"

        super().__init__(data=data)
