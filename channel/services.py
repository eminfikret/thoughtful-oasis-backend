from .repositories import ChannelRepository


class ChannelService:
    def __init__(self):
        self.channel_repository = ChannelRepository()
    
    def get_all_channels(self):
        return self.channel_repository.get_all()
    
    def get_channel_by_id(self, channel_id):
        return self.channel_repository.get_by_id(channel_id)
    
    def create_channel(self, user, name, description):
        channel_data = {
            'name': name,
            'description': description,
            'created_by': user
        }
        return self.channel_repository.create(channel_data)