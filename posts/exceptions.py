class PostNotFoundException(Exception):
    def __init__(self, post_id):
        super().__init__(f"Post {post_id} not found")

class UnauthorizedPostAccessException(Exception):
    def __init__(self, post_id):
        super().__init__(f"Unauthorized access to post {post_id}")
