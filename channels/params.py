from dataclasses import dataclass
from typing import Optional

from common.params import PaginationParams


@dataclass
class ChannelsParams(PaginationParams):
    search: Optional[str] = None
    pass