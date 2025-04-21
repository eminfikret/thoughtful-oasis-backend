from .models import Channel


class ChannelRepository:
    def get_all(self):
        return Channel.objects.all()
    
    def get_by_id(self, channel_id):
        try:
            return Channel.objects.get(id=channel_id)
        except Channel.DoesNotExist:
            return None
    
    def create(self, data):
        return Channel.objects.create(**data)