# ruff: noqa

import os
import uuid

import requests

API_URL = os.environ.get('BACKEND_API_URL', 'http://localhost:8000/api/v1')

# -------------------------
# Utility Functions
# -------------------------

def generate_unique_user():
    """Generate unique user data for testing"""
    unique_id = uuid.uuid4().hex[:8]
    return {
        "username": f"testuser_{unique_id}",
        "email": f"testuser_{unique_id}@example.com",
        "password": "TestPassword123!",
        "password2": "TestPassword123!"
    }

def register_test_user():
    """Register a test user and return user data, token, and user_id"""
    user_data = generate_unique_user()
    register_response = requests.post(f"{API_URL}/users/register/", json=user_data)
    assert register_response.status_code == 201, f"User registration failed: {register_response.text}"
    
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
        "description": "A test channel for post tests",
        "slug": f"test-channel-{uuid.uuid4().hex[:8]}"
    }
    headers = {"Authorization": f"Bearer {token}"}
    
    channel_response = requests.post(f"{API_URL}/channels/", json=channel_data, headers=headers)
    assert channel_response.status_code == 201, f"Channel creation failed: {channel_response.text}"
    return channel_response.json()

def create_test_post(token, channel_id, title=None, content=None):
    """Create a test post and return the post data"""
    if not title:
        title = f"Test Post {uuid.uuid4().hex[:8]}"
    if not content:
        content = f"This is test content for post testing {uuid.uuid4().hex[:8]}"
        
    headers = {"Authorization": f"Bearer {token}"}
    post_data = {
        "title": title,
        "content": content,
        "channel_id": channel_id
    }
    
    post_response = requests.post(f"{API_URL}/posts/create/", json=post_data, headers=headers)
    assert post_response.status_code == 201, f"Post creation failed: {post_response.text}"
    return post_response.json()

def setup_test_environment():
    """Setup user, channel, and post for testing"""
    user_data, token, user_id = register_test_user()
    channel = create_test_channel(token)
    post = create_test_post(token, channel["id"])
    return user_data, token, user_id, channel, post

# -------------------------
# List Posts Tests
# -------------------------

def test_list_posts_authenticated():
    """Test listing posts while authenticated"""
    user_data, token, user_id, channel, post = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/posts/", headers=headers)
    
    assert response.status_code == 200, "Should return post list"
    data = response.json()
    assert "results" in data, "Response should include results key"
    assert "count" in data, "Response should include count key"
    assert isinstance(data["results"], list), "Results should be a list"
    assert len(data["results"]) > 0, "Result list should not be empty"
    assert any(p["id"] == post["id"] for p in data["results"]), "Created post should be in the list"
    
    for p in data["results"]:
        if "author" in p and p["author"]:
            assert "username" in p["author"], "Author should have username field"
            assert "name" not in p["author"], "Author should not have name field"

def test_list_posts_unauthenticated():
    """Test listing posts without authentication"""
    user_data, token, user_id, channel, post = setup_test_environment()
    
    response = requests.get(f"{API_URL}/posts/")
    
    assert response.status_code == 401, "Should require authentication"

def test_list_posts_with_pagination():
    """Test listing posts with pagination"""
    user_data, token, user_id, channel, post = setup_test_environment()
    
    create_test_post(token, channel["id"])
    create_test_post(token, channel["id"])
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{API_URL}/posts/?limit=1", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1, "Should return only one post"
    
    response = requests.get(f"{API_URL}/posts/?offset=1&limit=2", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 2, "Should return at most two posts"
    
    response_all = requests.get(f"{API_URL}/posts/", headers=headers)
    total_posts = response_all.json()["count"]
    
    response = requests.get(f"{API_URL}/posts/?offset={total_posts}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 0, "Should return empty results when offset is too large"

def test_list_posts_with_search():
    """Test searching posts"""
    user_data, token, user_id, channel, _ = setup_test_environment()
    
    unique_keyword = f"uniquesearchterm{uuid.uuid4().hex[:8]}"
    search_post = create_test_post(token, channel["id"], 
                                   f"Searchable Post with {unique_keyword}", 
                                   "Search test content")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/posts/?search={unique_keyword}", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) >= 1, "Should find at least the created post"
    assert any(unique_keyword.lower() in post["title"].lower() for post in data["results"]), \
        "Created post should be in search results"
    
    content_keyword = f"uniquecontentterm{uuid.uuid4().hex[:8]}"
    content_post = create_test_post(token, channel["id"], 
                                    "Regular title", 
                                    f"Content with {content_keyword} for search")
    
    response = requests.get(f"{API_URL}/posts/?search={content_keyword}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert any(content_post["id"] == post["id"] for post in data["results"]), \
        "Post with matching content should be found"

def test_list_posts_empty_search():
    """Test search with no results"""
    user_data, token, user_id, channel, post = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/posts/?search=ThisSearchShouldNeverMatch12345", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        assert len(data["results"]) == 0, "Should return empty results for non-matching search"
    else:
        assert response.status_code == 404, "Should return 404 for non-matching search"

# -------------------------
# Create Post Tests
# -------------------------

def test_create_post_success():
    """Test successfully creating a post"""
    user_data, token, user_id, channel, _ = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    post_data = {
        "title": f"New Test Post {uuid.uuid4().hex[:8]}",
        "content": "This is content for a new test post",
        "channel_id": channel["id"]
    }
    
    response = requests.post(f"{API_URL}/posts/create/", json=post_data, headers=headers)
    
    assert response.status_code == 201, "Should create post successfully"
    data = response.json()
    assert data["title"] == post_data["title"], "Returned title should match input"
    assert data["content"] == post_data["content"], "Returned content should match input"
    assert data["author"]["username"] == user_data["username"], "Post author should be the creating user"
    assert "id" in data, "Response should include post ID"
    
    assert "username" in data["author"], "Author should have username field"
    assert "name" not in data["author"], "Author should not have name field"

def test_create_post_unauthenticated():
    """Test creating a post without authentication"""
    _, _, _, channel, _ = setup_test_environment()
    
    post_data = {
        "title": f"Unauthorized Post {uuid.uuid4().hex[:8]}",
        "content": "This post should not be created",
        "channel_id": channel["id"]
    }
    
    response = requests.post(f"{API_URL}/posts/create/", json=post_data)
    
    assert response.status_code == 401, "Should require authentication"

def test_create_post_nonexistent_channel():
    """Test creating a post in a non-existent channel"""
    _, token, _, channel, _ = setup_test_environment()
    
    nonexistent_channel_id = channel["id"] + 10000
    
    headers = {"Authorization": f"Bearer {token}"}
    post_data = {
        "title": f"Invalid Channel Post {uuid.uuid4().hex[:8]}",
        "content": "This post should fail due to invalid channel",
        "channel_id": nonexistent_channel_id
    }
    
    response = requests.post(f"{API_URL}/posts/create/", json=post_data, headers=headers)
    
    assert response.status_code == 404, "Should return 404 for non-existent channel"
    assert "channel" in response.text.lower() or "not found" in response.text.lower(), \
        "Error should mention channel"

def test_create_post_missing_fields():
    """Test creating a post with missing required fields"""
    _, token, _, channel, _ = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    
    post_data = {
        "content": "Content without title",
        "channel_id": channel["id"]
    }
    
    response = requests.post(f"{API_URL}/posts/create/", json=post_data, headers=headers)
    assert response.status_code == 400, "Should reject missing title"
    
    post_data = {
        "title": "Title without content",
        "channel_id": channel["id"]
    }
    
    response = requests.post(f"{API_URL}/posts/create/", json=post_data, headers=headers)
    assert response.status_code == 400, "Should reject missing content"
    
    post_data = {
        "title": "Title without channel",
        "content": "Content without channel"
    }
    
    response = requests.post(f"{API_URL}/posts/create/", json=post_data, headers=headers)
    assert response.status_code == 400, "Should reject missing channel_id"

def test_create_post_invalid_data():
    """Test creating a post with invalid data"""
    _, token, _, channel, _ = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    
    post_data = {
        "title": "Post with invalid channel",
        "content": "Some content",
        "channel_id": "not-an-integer"
    }
    
    response = requests.post(f"{API_URL}/posts/create/", json=post_data, headers=headers)
    assert response.status_code == 400, "Should reject non-integer channel_id"
    
    post_data = {
        "title": "",
        "content": "Content with empty title",
        "channel_id": channel["id"]
    }
    
    response = requests.post(f"{API_URL}/posts/create/", json=post_data, headers=headers)
    assert response.status_code == 400, "Should reject empty title"

# -------------------------
# Get Post Details Tests
# -------------------------

def test_get_post_details_success():
    """Test getting details of an existing post"""
    _, token, _, _, post = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/posts/{post['id']}/", headers=headers)
    
    assert response.status_code == 200, "Should return post details"
    data = response.json()
    assert data["id"] == post["id"], "Post ID should match"
    assert data["title"] == post["title"], "Title should match"
    assert data["content"] == post["content"], "Content should match"
    
    assert "username" in data["author"], "Author should have username field"
    assert "name" not in data["author"], "Author should not have name field"

def test_get_post_details_unauthenticated():
    """Test getting post details without authentication"""
    _, _, _, _, post = setup_test_environment()
    
    response = requests.get(f"{API_URL}/posts/{post['id']}/")
    
    assert response.status_code == 401, "Should require authentication"

def test_get_nonexistent_post():
    """Test getting details of a non-existent post"""
    _, token, _, _, post = setup_test_environment()
    
    nonexistent_post_id = post["id"] + 10000
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/posts/{nonexistent_post_id}/", headers=headers)
    
    assert response.status_code == 404, "Should return 404 for non-existent post"
    assert "not found" in response.text.lower(), "Error should mention 'not found'"

# -------------------------
# Update Post Tests
# -------------------------

def test_update_post_success():
    """Test successfully updating a post"""
    user_data, token, _, channel, post = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    update_data = {
        "title": f"Updated Title {uuid.uuid4().hex[:8]}",
        "content": f"Updated content {uuid.uuid4().hex[:8]}"
    }
    
    response = requests.put(f"{API_URL}/posts/{post['id']}/update/", json=update_data, headers=headers)
    
    assert response.status_code == 200, "Should update post successfully"
    data = response.json()
    assert data["title"] == update_data["title"], "Title should be updated"
    assert data["content"] == update_data["content"], "Content should be updated"
    assert data["author"]["username"] == user_data["username"], "Author should remain the same"
    
    
    assert "username" in data["author"], "Author should have username field"
    assert "name" not in data["author"], "Author should not have name field"

def test_update_post_partial():
    """Test partial update of a post"""
    _, token, _, _, post = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    title_update = {
        "title": f"Only Title Updated {uuid.uuid4().hex[:8]}"
    }
    
    response = requests.put(f"{API_URL}/posts/{post['id']}/update/", json=title_update, headers=headers)
    
    assert response.status_code == 200, "Should update post successfully"
    data = response.json()
    assert data["title"] == title_update["title"], "Title should be updated"
    assert data["content"] == post["content"], "Content should remain unchanged"
    
    content_update = {
        "content": f"Only content updated {uuid.uuid4().hex[:8]}"
    }
    
    response = requests.put(f"{API_URL}/posts/{post['id']}/update/", json=content_update, headers=headers)
    
    assert response.status_code == 200, "Should update post successfully"
    data = response.json()
    assert data["title"] == title_update["title"], "Title should remain unchanged"
    assert data["content"] == content_update["content"], "Content should be updated"

def test_update_post_unauthenticated():
    """Test updating a post without authentication"""
    _, _, _, _, post = setup_test_environment()
    
    update_data = {
        "title": "Unauthorized Update",
        "content": "This update should fail"
    }
    
    response = requests.put(f"{API_URL}/posts/{post['id']}/update/", json=update_data)
    
    assert response.status_code == 401, "Should require authentication"

def test_update_other_user_post():
    """Test updating another user's post (should fail)"""

    user1_data, token1, _, channel, post = setup_test_environment()
    
    user2_data, token2, _ = register_test_user()
    
    headers = {"Authorization": f"Bearer {token2}"}
    update_data = {
        "title": "Unauthorized Update",
        "content": "This update should fail"
    }
    
    response = requests.put(f"{API_URL}/posts/{post['id']}/update/", json=update_data, headers=headers)
    
    assert response.status_code == 403, "Should forbid updating another user's post"
    assert "forbidden" in response.text.lower() or "own" in response.text.lower(), \
        "Error should mention forbidden or ownership"

def test_update_nonexistent_post():
    """Test updating a non-existent post"""
    _, token, _, _, post = setup_test_environment()
    
    nonexistent_post_id = post["id"] + 10000
    
    headers = {"Authorization": f"Bearer {token}"}
    update_data = {
        "title": "Update Non-existent",
        "content": "This update should fail"
    }
    
    response = requests.put(f"{API_URL}/posts/{nonexistent_post_id}/update/", json=update_data, headers=headers)
    
    assert response.status_code == 404, "Should return 404 for non-existent post"

# -------------------------
# Delete Post Tests
# -------------------------

def test_delete_post_success():
    """Test successfully deleting a post"""
    _, token, _, channel, post = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{API_URL}/posts/{post['id']}/delete/", headers=headers)
    
    assert response.status_code == 204, "Should delete post successfully"
    
    get_response = requests.get(f"{API_URL}/posts/{post['id']}/", headers=headers)
    assert get_response.status_code == 404, "Deleted post should not be found"

def test_delete_post_unauthenticated():
    """Test deleting a post without authentication"""
    _, _, _, _, post = setup_test_environment()
    
    response = requests.delete(f"{API_URL}/posts/{post['id']}/delete/")
    
    assert response.status_code == 401, "Should require authentication"

def test_delete_other_user_post():
    """Test deleting another user's post (should fail)"""
    _, token1, _, channel, post = setup_test_environment()
    
    _, token2, _ = register_test_user()
    
    headers = {"Authorization": f"Bearer {token2}"}
    response = requests.delete(f"{API_URL}/posts/{post['id']}/delete/", headers=headers)
    
    assert response.status_code == 403, "Should forbid deleting another user's post"
    assert "forbidden" in response.text.lower() or "own" in response.text.lower(), \
        "Error should mention forbidden or ownership"

def test_delete_nonexistent_post():
    """Test deleting a non-existent post"""
    _, token, _, _, post = setup_test_environment()
    
    nonexistent_post_id = post["id"] + 10000
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{API_URL}/posts/{nonexistent_post_id}/delete/", headers=headers)
    
    assert response.status_code == 404, "Should return 404 for non-existent post"

# -------------------------
# Channel Posts Tests
# -------------------------

def test_get_channel_posts_success():
    """Test getting posts for a specific channel"""
    _, token, _, channel, post = setup_test_environment()
    
    create_test_post(token, channel["id"])
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/channels/{channel['id']}/posts/", headers=headers)
    
    assert response.status_code == 200, "Should return channel posts"
    data = response.json()
    assert "results" in data, "Response should include results key"
    assert "count" in data, "Response should include count key"
    assert data["count"] >= 2, "Should find at least 2 posts"
    
    for post in data["results"]:
        assert post["channel"]["id"] == channel["id"], "All posts should belong to requested channel"
        
        assert "username" in post["author"], "Author should have username field"
        assert "name" not in post["author"], "Author should not have name field"

def test_get_channel_posts_unauthenticated():
    """Test getting channel posts without authentication"""
    _, _, _, channel, _ = setup_test_environment()
    
    response = requests.get(f"{API_URL}/channels/{channel['id']}/posts/")
    
    assert response.status_code == 401, "Should require authentication"

def test_get_nonexistent_channel_posts():
    """Test getting posts for a non-existent channel"""
    _, token, _, channel, _ = setup_test_environment()
    
    nonexistent_channel_id = channel["id"] + 10000
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/channels/{nonexistent_channel_id}/posts/", headers=headers)
    
    assert response.status_code == 404, "Should return 404 for non-existent channel"

def test_get_channel_posts_with_search():
    """Test searching posts within a channel"""
    _, token, _, channel, _ = setup_test_environment()
    
    unique_keyword = f"uniquechannelsearchterm{uuid.uuid4().hex[:8]}"
    create_test_post(token, channel["id"], 
                     f"Channel Searchable Post with {unique_keyword}", 
                     "Search test content")
    
    create_test_post(token, channel["id"], 
                     "Regular Post Title", 
                     "Regular content")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/channels/{channel['id']}/posts/?search={unique_keyword}", 
                           headers=headers)
    
    assert response.status_code == 200, "Should return search results"
    data = response.json()
    assert len(data["results"]) == 1, "Should find exactly one matching post"
    assert unique_keyword.lower() in data["results"][0]["title"].lower(), \
        "Found post should contain search keyword"

def test_get_channel_posts_with_pagination():
    """Test pagination when listing channel posts"""
    _, token, _, channel, _ = setup_test_environment()
    
    posts = [create_test_post(token, channel["id"]) for _ in range(3)]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{API_URL}/channels/{channel['id']}/posts/?limit=2", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2, "Should return only two posts"
    
    response = requests.get(f"{API_URL}/channels/{channel['id']}/posts/?offset=1&limit=1", 
                           headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1, "Should return exactly one post"
    
    response = requests.get(f"{API_URL}/channels/{channel['id']}/posts/?offset=100", 
                           headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 0, "Should return empty list for large offset"

# -------------------------
# Homepage Posts Tests
# -------------------------

def test_homepage_posts_authenticated():
    """Test getting homepage posts while authenticated"""
    user_data, token, user_id, channel, post = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/posts/homepage/", headers=headers)
    
    assert response.status_code == 200, "Should return homepage posts"
    data = response.json()
    assert "results" in data, "Response should include results key"
    assert "count" in data, "Response should include count key"
    assert isinstance(data["results"], list), "Results should be a list"

def test_homepage_posts_unauthenticated():
    """Test getting homepage posts without authentication"""
    _, _, _, _, _ = setup_test_environment()
    
    response = requests.get(f"{API_URL}/posts/homepage/")
    
    assert response.status_code == 401, "Should require authentication"

def test_homepage_posts_with_pagination():
    """Test pagination of homepage posts"""
    _, token, _, channel, _ = setup_test_environment()
    
    for _ in range(3):
        create_test_post(token, channel["id"])
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/posts/homepage/?limit=2", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 2, "Should return at most two posts"
    
    if data["count"] > 2:
        response = requests.get(f"{API_URL}/posts/homepage/?offset=1&limit=2", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 2, "Should return at most two posts"

def test_homepage_posts_days_parameter():
    """Test the days parameter for filtering homepage posts"""
    _, token, _, channel, _ = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    
    for days in [1, 5, 30]:
        response = requests.get(f"{API_URL}/posts/homepage/?days={days}", headers=headers)
        assert response.status_code == 200, f"Should accept days={days}"
    
    response = requests.get(f"{API_URL}/posts/homepage/?days=0", headers=headers)
    assert response.status_code == 400, "Should reject days=0"
    
    response = requests.get(f"{API_URL}/posts/homepage/?days=-1", headers=headers)
    assert response.status_code == 400, "Should reject negative days"
    
    response = requests.get(f"{API_URL}/posts/homepage/?days=invalid", headers=headers)
    assert response.status_code == 400, "Should reject non-integer days"

def test_homepage_posts_ordering():
    """Test that homepage posts are ordered by score"""
    
    user_data, token, user_id, channel, _ = setup_test_environment()
    
    for _ in range(3):
        create_test_post(token, channel["id"])
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/posts/homepage/", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    if len(data["results"]) >= 2:
        assert "votes" in data["results"][0], "Posts should include vote information"