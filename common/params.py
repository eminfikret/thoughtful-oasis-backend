from dataclasses import dataclass

from common.constants import Pagination


@dataclass
class PaginationParams:
    limit: int = Pagination.DEFAULT_LIMIT
    offset: int = Pagination.DEFAULT_OFFSET
