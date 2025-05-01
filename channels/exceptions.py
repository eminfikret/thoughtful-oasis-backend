from channels.types import ChannelId


class ChannelNotFound(Exception):
    def __init__(self, channel_id: ChannelId):
        self.channel_id = channel_id
        self.message = f"Channel with id {channel_id} not found."
        super().__init__(self.message)

    def __str__(self):
        return self.message
