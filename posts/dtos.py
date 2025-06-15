from dataclasses import dataclass
from typing import Optional


@dataclass
class CreatePostDto:
    channel_id: int
    title: str
    content: str


@dataclass
class UpdatePostDto:
    title: Optional[str] = None
    content: Optional[str] = None