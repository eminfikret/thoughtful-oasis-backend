from typing import Optional

from channels.types import ChannelId
from common.exceptions import ConflictException, NotFoundException, PermissionDeniedException


class ChannelNotFoundException(NotFoundException):
    def __init__(self, channel_id: ChannelId):
        self.channel_id = channel_id
        self.error = f"Channel with id {channel_id} not found."
        super().__init__(self.error)

class ChannelPermissionDeniedException(PermissionDeniedException):
    def __init__(self, error: Optional[str] = "You are not allowed to access this channel."):
        super().__init__(error)

class ChannelNameAlreadyExistsException(ConflictException):
    def __init__(self, name: str):
        super().__init__(f"A channel with name '{name}' already exists.")