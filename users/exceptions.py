from common.exceptions import NotFoundException
from users.types import UserId


class UserNotFoundException(NotFoundException):
    def __init__(self, user_id: UserId):
        self.user_id = user_id
        self.error = f"User with id {user_id} not found."
        super().__init__(self.error)