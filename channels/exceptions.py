from typing import Optional

from channels.types import ChannelId
from common.exceptions import UnauthorizedAccessException


class ChannelNotFoundException(Exception):
    def __init__(self, channel_id: ChannelId):
        self.channel_id = channel_id
        self.message = f"Channel with id {channel_id} not found."
        super().__init__(self.message)

    def __str__(self):
        return self.message

class UnauthorizedChannelAccessException(UnauthorizedAccessException):
    def __init__(self, message: Optional[str] = "You are not allowed to access this channel."):
        super().__init__(message)