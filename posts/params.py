from dataclasses import dataclass


@dataclass
class PaginationParams:
    limit: int = 10
    offset: int = 0

    @staticmethod
    def from_request(request):
        try:
            limit = int(request.query_params.get('limit', 10))
            offset = int(request.query_params.get('offset', 0))
        except ValueError:
            limit, offset = 10, 0
        return PaginationParams(limit=limit, offset=offset)