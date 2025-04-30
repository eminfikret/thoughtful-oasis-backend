from dataclasses import dataclass
from typing import Optional


@dataclass
class CreateChannelDto:
    name: str
    description: str

@dataclass
class UpdateChannelDto:
    name: Optional[str] = None
    description: Optional[str] = None
