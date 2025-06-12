from dataclasses import dataclass
from typing import Optional

from common.params import PaginationParams


@dataclass
class UsersParams(PaginationParams):
    search: Optional[str] = None