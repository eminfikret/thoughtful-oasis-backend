import os
import uuid

import requests

API_URL = os.environ.get('BACKEND_API_URL', 'http://localhost:8000/api/v1')

# -------------------------
# Utility Functions
# -------------------------

def generate_unique_user():
    """Generate unique user data for testing"""
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    return {
        "username": username,
        "email": f"{username}@example.com",
        "password": "TestPassword123!",
        "password2": "TestPassword123!"
    }

def register_test_user():
    """Register a test user and return user data, token, and user_id"""
    user_data = generate_unique_user()
    register_response = requests.post(f"{API_URL}/users/register/", json=user_data)
    assert register_response.status_code == 201, (
        f"User registration failed: {register_response.text}")
    
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    login_response = requests.post(f"{API_URL}/users/login/", json=login_data)
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    
    login_data = login_response.json()
    token = login_data["token"] 
    user_id = register_response.json()["id"]
    
    return user_data, token, user_id

def create_test_channel(token):
    """Create a test channel and return the channel data"""
    channel_data = {
        "name": f"Test Channel {uuid.uuid4().hex[:8]}",
        "description": "Test channel description",
        "slug": f"test-channel-{uuid.uuid4().hex[:8]}"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/channels/", json=channel_data, headers=headers)
    
    assert response.status_code == 201, f"Channel creation failed: {response.text}"
    return response.json()

def create_test_post(token, channel_id, title=None, content=None):
    """Create a test post and return the post data"""
    if title is None:
        title = f"Test Post {uuid.uuid4().hex[:8]}"
    if content is None:
        content = f"Test content {uuid.uuid4().hex[:8]}"
        
    post_data = {
        "title": title,
        "content": content,
        "channel_id": channel_id
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/posts/create/", json=post_data, headers=headers)
    
    assert response.status_code == 201, f"Post creation failed: {response.text}"
    return response.json()

def create_test_comment(token, post_id, content=None):
    """Create a test comment and return the comment data"""
    if content is None:
        content = f"Test comment {uuid.uuid4().hex[:8]}"
        
    comment_data = {
        "post_id": post_id,
        "content": content
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/comments/create/", json=comment_data, headers=headers)
    
    assert response.status_code == 201, f"Comment creation failed: {response.text}"
    return response.json()

def create_test_reply(token, parent_comment_id, content=None):
    """Create a test reply and return the reply data"""
    if content is None:
        content = f"Test reply {uuid.uuid4().hex[:8]}"
        
    reply_data = {
        "parent_comment_id": parent_comment_id,
        "content": content
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/comments/reply/", json=reply_data, headers=headers)
    
    assert response.status_code == 201, f"Reply creation failed: {response.text}"
    return response.json()

def setup_test_environment():
    """Setup user, channel, post, comment for testing"""
    user_data, token, user_id = register_test_user()
    channel = create_test_channel(token)
    post = create_test_post(token, channel["id"])
    comment = create_test_comment(token, post["id"])
    
    return user_data, token, user_id, channel, post, comment

# -------------------------
# Create Comment Tests
# -------------------------

def test_create_comment_success():
    """Test successfully creating a comment on a post"""
    user_data, token, user_id, channel, post, _ = setup_test_environment()
    
    content = f"New comment {uuid.uuid4().hex[:8]}"
    comment_data = {
        "post_id": post["id"],
        "content": content
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/comments/create/", json=comment_data, headers=headers)
    
    assert response.status_code == 201, "Should create comment successfully"
    data = response.json()
    assert data["content"] == content, "Comment content should match"
    assert data["post_id"] == post["id"], "Post ID should match"
    assert "author" in data, "Author data should be included"
    assert data["author"]["username"] == user_data["username"], "Author username should match"
    assert "votes" in data, "Vote data should be included"
    assert "claims" in data, "Claims data should be included"
    assert "reply_count" in data, "Reply count should be included"

def test_create_comment_unauthenticated():
    """Test creating a comment without authentication"""
    _, _, _, _, post, _ = setup_test_environment()
    
    comment_data = {
        "post_id": post["id"],
        "content": "This comment should not be created"
    }
    
    response = requests.post(f"{API_URL}/comments/create/", json=comment_data)
    
    assert response.status_code == 401, "Should require authentication"

def test_create_comment_nonexistent_post():
    """Test creating a comment on a non-existent post"""
    _, token, _, _, post, _ = setup_test_environment()
    
    nonexistent_post_id = post["id"] + 10000
    
    comment_data = {
        "post_id": nonexistent_post_id,
        "content": "This comment should not be created"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/comments/create/", json=comment_data, headers=headers)
    
    assert response.status_code == 404, "Should return 404 for non-existent post"

def test_create_comment_missing_fields():
    """Test creating a comment with missing required fields"""
    _, token, _, _, _, _ = setup_test_environment()
    
    comment_data = {
        "content": "This comment should not be created"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/comments/create/", json=comment_data, headers=headers)
    
    assert response.status_code == 400, "Should require post_id"

    _, _, _, _, post, _ = setup_test_environment()
    comment_data = {
        "post_id": post["id"]
    }
    
    response = requests.post(f"{API_URL}/comments/create/", json=comment_data, headers=headers)
    
    assert response.status_code == 400, "Should require content"

# -------------------------
# Create Reply Tests
# -------------------------

def test_create_reply_success():
    """Test successfully creating a reply to a comment"""
    _, token, _, _, _, comment = setup_test_environment()
    
    content = f"New reply {uuid.uuid4().hex[:8]}"
    reply_data = {
        "parent_comment_id": comment["id"],
        "content": content
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/comments/reply/", json=reply_data, headers=headers)
    
    assert response.status_code == 201, "Should create reply successfully"
    data = response.json()
    assert data["content"] == content, "Reply content should match"
    assert data["parent_id"] == comment["id"], "Parent comment ID should match"
    assert "author" in data, "Author data should be included"
    assert "votes" in data, "Vote data should be included"
    assert "post_id" in data, "Post ID should be included"

def test_create_reply_unauthenticated():
    """Test creating a reply without authentication"""
    _, _, _, _, _, comment = setup_test_environment()
    
    reply_data = {
        "parent_comment_id": comment["id"],
        "content": "This reply should not be created"
    }
    
    response = requests.post(f"{API_URL}/comments/reply/", json=reply_data)
    
    assert response.status_code == 401, "Should require authentication"

def test_create_reply_nonexistent_comment():
    """Test creating a reply to a non-existent comment"""
    _, token, _, _, _, comment = setup_test_environment()
    
    nonexistent_comment_id = comment["id"] + 10000
    
    reply_data = {
        "parent_comment_id": nonexistent_comment_id,
        "content": "This reply should not be created"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/comments/reply/", json=reply_data, headers=headers)
    
    assert response.status_code == 404, "Should return 404 for non-existent comment"

def test_create_reply_missing_fields():
    """Test creating a reply with missing required fields"""
    _, token, _, _, _, _ = setup_test_environment()
    
    reply_data = {
        "content": "This reply should not be created"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/comments/reply/", json=reply_data, headers=headers)
    
    assert response.status_code == 400, "Should require parent_comment_id"
    
    _, _, _, _, _, comment = setup_test_environment()
    reply_data = {
        "parent_comment_id": comment["id"]
    }
    
    response = requests.post(f"{API_URL}/comments/reply/", json=reply_data, headers=headers)
    
    assert response.status_code == 400, "Should require content"

# -------------------------
# Get Post Comments Tests
# -------------------------

def test_get_post_comments_success():
    """Test getting comments for a specific post"""
    _, token, _, _, post, comment = setup_test_environment()
    
    create_test_comment(token, post["id"])
    create_test_comment(token, post["id"])
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/comments/?post_id={post['id']}", headers=headers)
    
    assert response.status_code == 200, "Should return comments successfully"
    data = response.json()
    assert len(data) >= 3, "Should return at least 3 comments"
    
    for comment in data:
        assert "id" in comment, "Comment should have ID"
        assert "content" in comment, "Comment should have content"
        assert "author" in comment, "Comment should have author info"
        assert "votes" in comment, "Comment should have vote info"
        assert "created_at" in comment, "Comment should have timestamp"

def test_get_post_comments_empty():
    """Test getting comments for a post with no comments"""
    _, token, _, channel, _, _ = setup_test_environment() 
    
    new_post = create_test_post(token, channel["id"])
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/comments/?post_id={new_post['id']}", headers=headers)
    
    assert response.status_code == 200, "Should return successfully"
    data = response.json()
    assert len(data) == 0, "Should return empty list"

def test_get_post_comments_missing_post_id():
    """Test getting comments without providing post_id"""
    _, token, _, _, _, _ = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/comments/", headers=headers)
    
    assert response.status_code == 400, "Should require post_id parameter"

def test_get_post_comments_nonexistent_post():
    """Test getting comments for a non-existent post"""
    _, token, _, _, post, _ = setup_test_environment()
    
    nonexistent_post_id = post["id"] + 10000
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/comments/?post_id={nonexistent_post_id}", headers=headers)
    
    assert response.status_code == 404, "Should return 404 for non-existent post"

# -------------------------
# Get Comment Replies Tests
# -------------------------

def test_get_comment_replies_success():
    """Test getting replies for a specific comment"""
    _, token, _, _, _, comment = setup_test_environment()
    
    reply1 = create_test_reply(token, comment["id"])
    reply2 = create_test_reply(token, comment["id"])
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/comments/{comment['id']}/replies/", headers=headers)
    
    assert response.status_code == 200, "Should return replies successfully"
    data = response.json()
    assert len(data) >= 2, "Should return at least 2 replies"
    
    reply_ids = [reply["id"] for reply in data]
    assert reply1["id"] in reply_ids, "First reply should be in results"
    assert reply2["id"] in reply_ids, "Second reply should be in results"

def test_get_comment_replies_empty():
    """Test getting replies for a comment with no replies"""
    _, token, _, _, _, comment = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/comments/{comment['id']}/replies/", headers=headers)
    
    assert response.status_code == 200, "Should return successfully"
    data = response.json()
    assert len(data) == 0, "Should return empty list"

def test_get_comment_replies_nonexistent_comment():
    """Test getting replies for a non-existent comment"""
    _, token, _, _, _, comment = setup_test_environment()
    
    nonexistent_comment_id = comment["id"] + 10000
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/comments/{nonexistent_comment_id}/replies/", 
                            headers=headers)
    
    assert response.status_code == 404, "Should return 404 for non-existent comment"

# -------------------------
# Update Comment Tests
# -------------------------

def test_update_comment_success():
    """Test successfully updating a comment"""
    user_data, token, _, _, _, comment = setup_test_environment()
    
    updated_content = f"Updated content {uuid.uuid4().hex[:8]}"
    update_data = {
        "content": updated_content
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(
        f"{API_URL}/comments/{comment['id']}/update/", 
        json=update_data, 
        headers=headers
    )
    
    assert response.status_code == 200, "Should update comment successfully"
    data = response.json()
    assert data["content"] == updated_content, "Content should be updated"
    assert data["id"] == comment["id"], "Comment ID should remain the same"
    assert data["author"]["username"] == user_data["username"], "Author should remain the same"

def test_update_comment_unauthenticated():
    """Test updating a comment without authentication"""
    _, _, _, _, _, comment = setup_test_environment()
    
    update_data = {
        "content": "This update should fail"
    }
    
    response = requests.put(f"{API_URL}/comments/{comment['id']}/update/", json=update_data)
    
    assert response.status_code == 401, "Should require authentication"

def test_update_other_user_comment():
    """Test updating another user's comment (should fail)"""
    _, _, _, _, _, comment = setup_test_environment()
    
    _, token2, _ = register_test_user()
    
    update_data = {
        "content": "This update should fail"
    }
    
    headers = {"Authorization": f"Bearer {token2}"}
    response = requests.put(
        f"{API_URL}/comments/{comment['id']}/update/", 
        json=update_data, 
        headers=headers
    )
    
    assert response.status_code == 403, "Should forbid updating another user's comment"
    assert "forbidden" in response.text.lower() or "own" in response.text.lower(), \
        "Error should mention forbidden or ownership"

def test_update_nonexistent_comment():
    """Test updating a non-existent comment"""
    _, token, _, _, _, comment = setup_test_environment()
    
    nonexistent_comment_id = comment["id"] + 10000
    
    update_data = {
        "content": "This update should fail"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(
        f"{API_URL}/comments/{nonexistent_comment_id}/update/", 
        json=update_data, 
        headers=headers
    )
    
    assert response.status_code == 404, "Should return 404 for non-existent comment"

def test_update_comment_missing_content():
    """Test updating a comment without providing content"""
    _, token, _, _, _, comment = setup_test_environment()
    
    update_data = {}  
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(
        f"{API_URL}/comments/{comment['id']}/update/", 
        json=update_data, 
        headers=headers
    )
    
    assert response.status_code == 400, "Should require content field"

# -------------------------
# User Comments Tests
# -------------------------

def test_get_user_comments_success():
    """Test getting comments by a specific user"""
    _, token, user_id, _, post, comment = setup_test_environment()
    
    create_test_comment(token, post["id"])
    create_test_comment(token, post["id"])
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/comments/user/?user_id={user_id}", headers=headers)
    
    assert response.status_code == 200, "Should return user comments successfully"
    data = response.json()
    assert "results" in data, "Response should include results"
    assert "count" in data, "Response should include count"
    assert len(data["results"]) >= 3, "Should return at least 3 comments"
    
    for comment in data["results"]:
        assert comment["author"]["id"] == user_id, "All comments should belong to the user"

def test_get_user_comments_unauthenticated():
    """Test getting user comments without authentication"""
    _, _, user_id, _, _, _ = setup_test_environment()
    
    response = requests.get(f"{API_URL}/comments/user/?user_id={user_id}")
    
    assert response.status_code == 401, "Should require authentication"

def test_get_user_comments_pagination():
    """Test pagination when listing user comments"""
    _, token, user_id, _, post, _ = setup_test_environment()
    
    for _ in range(5):
        create_test_comment(token, post["id"])
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{API_URL}/comments/user/?user_id={user_id}&limit=3", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 3, "Should return only three comments"
    
    response = requests.get(f"{API_URL}/comments/user/?user_id={user_id}&offset=2&limit=2", 
                           headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2, "Should return exactly two comments"
    
    response = requests.get(f"{API_URL}/comments/user/?user_id={user_id}&offset=100", 
                           headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 0, "Should return empty list for large offset"

def test_get_user_comments_missing_user_id():
    """Test getting comments without providing user_id"""
    _, token, _, _, _, _ = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/comments/user/", headers=headers)
    
    assert response.status_code == 400, "Should require user_id parameter"

def test_get_user_comments_nonexistent_user():
    """Test getting comments for a non-existent user"""
    _, token, user_id, _, _, _ = setup_test_environment()
    
    nonexistent_user_id = user_id + 10000
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/comments/user/?user_id={nonexistent_user_id}",
                             headers=headers)
    
    assert response.status_code == 404, "Should return 404 for non-existent user"

def test_get_other_user_comments():
    """Test getting another user's comments"""

    _, token1, user_id1, _, post, _ = setup_test_environment()
    create_test_comment(token1, post["id"])
    
    _, token2, _ = register_test_user()
    
    headers2 = {"Authorization": f"Bearer {token2}"}
    response = requests.get(f"{API_URL}/comments/user/?user_id={user_id1}", headers=headers2)
    
    assert response.status_code == 200, "Should be allowed to view other user's comments"
    data = response.json()
    assert "results" in data, "Response should include results"
    for comment in data["results"]:
        assert comment["author"]["id"] == user_id1, "All comments should belong to "
        "the requested user"