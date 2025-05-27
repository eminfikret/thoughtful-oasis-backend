from dataclasses import dataclass
from typing import Optional

@dataclass
class PostsParams:
    page: Optional[int] = None
    page_size: Optional[int] = None
    ordering: Optional[str] = None