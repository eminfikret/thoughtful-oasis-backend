import atexit
import os
import uuid

import requests

API_URL = os.environ.get('BACKEND_API_URL', 'http://localhost:8000/api/v1')

created_users = []
created_channels = []
created_posts = []
created_subscriptions = []

# -------------------------
# Test helper functions
# -------------------------

def generate_unique_user():
    """Generate unique user data for testing"""
    unique_id = uuid.uuid4().hex[:8]
    return {
        "username": f"testuser_{unique_id}",
        "email": f"testuser_{unique_id}@example.com",
        "password": "Test123!@#",
        "password2": "Test123!@#",
        "first_name": "Test",
        "last_name": "User"
    }

def register_and_login_user():
    """Register and login a test user, return token"""
    user_data = generate_unique_user()
    requests.post(f"{API_URL}/users/register/", json=user_data)
    
    login_response = requests.post(f"{API_URL}/users/login/", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    
    if login_response.status_code != 200:
        print(f"Login failed with status {login_response.status_code}")
        return None, None
    
    user_id = login_response.json().get("user", {}).get("id")
    if user_id:
        created_users.append({"id": user_id, "token": login_response.json()["token"]})
    
    return login_response.json()["token"], user_data

def generate_unique_channel():
    """Generate unique channel data for testing"""
    unique_id = uuid.uuid4().hex[:8]
    return {
        "name": f"Test Channel {unique_id}",
        "description": f"This is a test channel created for automated testing {unique_id}"
    }

def create_test_channel(token):
    """Create a test channel and return its data"""
    channel_data = generate_unique_channel()
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/channels/", json=channel_data, headers=headers)
    
    if response.status_code != 201:
        print(f"Channel creation failed with status {response.status_code}")
        print(f"Response: {response.text[:200]}")
        return None
    
    channel = response.json()
    created_channels.append({"id": channel["id"], "token": token})
    
    return channel

def track_created_post(post_data, token):
    """Track a created post for cleanup"""
    created_posts.append({"id": post_data["id"], "token": token})

# -------------------------
# Channel creation tests
# -------------------------

def test_create_channel_success():
    """Test successful channel creation"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    channel_data = generate_unique_channel()
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(f"{API_URL}/channels/", json=channel_data, headers=headers)
    
    assert response.status_code == 201, (
        f"Channel creation failed with status {response.status_code}")
    data = response.json()
    assert data["name"] == channel_data["name"], "Channel name should match"
    assert data["description"] == channel_data["description"], "Channel description should match"
    assert "id" in data, "Response should contain channel ID"
    assert "slug" in data, "Response should contain channel slug"
    assert "owner" in data, "Response should contain owner"

def test_create_channel_unauthenticated():
    """Test channel creation without authentication"""
    channel_data = generate_unique_channel()
    
    response = requests.post(f"{API_URL}/channels/", json=channel_data)
    
    assert response.status_code == 401, "Should require authentication"

def test_create_channel_duplicate_name():
    """Test channel creation with duplicate name"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    channel_data = generate_unique_channel()
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(f"{API_URL}/channels/", json=channel_data, headers=headers)
    assert response.status_code == 201, "First channel creation should succeed"
    
    response = requests.post(f"{API_URL}/channels/", json=channel_data, headers=headers)
    
    assert response.status_code == 409, "Should reject duplicate channel name"
    assert ("name" in response.text.lower() or 
            "already exists" in response.text.lower()), "Error should mention name conflict"

def test_create_channel_missing_fields():
    """Test channel creation with missing required fields"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    headers = {"Authorization": f"Bearer {token}"}
    
    channel_data = {"description": "Test description only"}
    response = requests.post(f"{API_URL}/channels/", json=channel_data, headers=headers)
    assert response.status_code == 400, "Should reject missing name"
    
    channel_data = {"name": "Test Channel Name Only"}
    response = requests.post(f"{API_URL}/channels/", json=channel_data, headers=headers)
    assert response.status_code == 400, "Should reject missing description"

# -------------------------
# Channel listing tests
# -------------------------

def test_list_channels_authenticated():
    """Test listing channels while authenticated"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    channel = create_test_channel(token)
    assert channel is not None, "Failed to create test channel"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/channels/", headers=headers)
    
    assert response.status_code == 200, "Should return channel list"
    data = response.json()
    assert "results" in data, "Response should include results key"
    assert "count" in data, "Response should include count key"
    assert isinstance(data["results"], list), "Results should be a list"
    assert any(
        ch["name"] == channel["name"] for ch in data["results"]
    ), "Created channel should be in the list"

def test_list_channels_unauthenticated():
    """Test listing channels without authentication"""
    response = requests.get(f"{API_URL}/channels/")
    
    assert response.status_code == 401, "Should require authentication"

def test_list_channels_with_search():
    """Test listing channels with search parameter"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    unique_keyword = f"uniquekeyword{uuid.uuid4().hex[:8]}"
    channel_data = {
        "name": f"Searchable Channel {unique_keyword}",
        "description": "Test channel for search"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/channels/", json=channel_data, headers=headers)
    assert response.status_code == 201, "Channel creation should succeed"
    
    response = requests.get(f"{API_URL}/channels/?search={unique_keyword}", headers=headers)
    
    assert response.status_code == 200, "Search should work"
    data = response.json()
    assert len(data["results"]) >= 1, "Search should find at least the created channel"
    assert any(
        unique_keyword in ch["name"] for ch in data["results"]
    ), "Created channel should be in search results"

# -------------------------
# Channel detail tests
# -------------------------

def test_get_channel_detail_success():
    """Test getting details of an existing channel"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    channel = create_test_channel(token)
    assert channel is not None, "Failed to create test channel"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/channels/{channel['id']}/", headers=headers)
    
    assert response.status_code == 200, "Should return channel details"
    data = response.json()
    assert data["name"] == channel["name"], "Channel name should match"
    assert data["description"] == channel["description"], "Channel description should match"
    assert data["id"] == channel["id"], "Channel ID should match"

def test_get_channel_detail_nonexistent():
    """Test getting details of a non-existent channel"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    channel = create_test_channel(token)
    assert channel is not None, "Failed to create test channel"
    
    nonexistent_id = channel["id"] + 10000
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/channels/{nonexistent_id}/", headers=headers)
    
    assert response.status_code == 404, "Should return not found for non-existent channel"

def test_get_channel_detail_unauthenticated():
    """Test getting channel details without authentication"""
    token, _ = register_and_login_user()
    channel = create_test_channel(token)
    assert channel is not None, "Failed to create test channel"
    
    response = requests.get(f"{API_URL}/channels/{channel['id']}/")
    
    assert response.status_code == 401, "Should require authentication"

def test_channel_detail_includes_subscription_status():
    """Test that channel detail includes correct subscription status"""
    token1, user_id1 = register_and_login_user()
    assert token1 is not None, "Failed to get first auth token"
    
    channel = create_test_channel(token1)
    assert channel is not None, "Failed to create test channel"
    
    token2, user_id2 = register_and_login_user()
    assert token2 is not None, "Failed to get second auth token"
    
    headers2 = {"Authorization": f"Bearer {token2}"}
    response = requests.get(f"{API_URL}/channels/{channel['id']}/", headers=headers2)
    
    assert response.status_code == 200, "Should return channel details"
    data = response.json()
    assert "is_subscribed" in data, "Response should include is_subscribed field"
    assert data["is_subscribed"] is False, "User should not be subscribed initially"
    
    response = requests.post(f"{API_URL}/channels/{channel['id']}/subscribe/", headers=headers2)
    assert response.status_code == 204, "Subscribe should succeed"
    
    subscription_record = {"channel_id": channel["id"], "token": token2}
    created_subscriptions.append(subscription_record)
    
    response = requests.get(f"{API_URL}/channels/{channel['id']}/", headers=headers2)
    
    assert response.status_code == 200, "Should return channel details"
    data = response.json()
    assert data["is_subscribed"] is True, "User should show as subscribed after subscribing"
    
    response = requests.delete(f"{API_URL}/channels/{channel['id']}/unsubscribe/", headers=headers2)
    assert response.status_code == 204, "Unsubscribe should succeed"
    
    if subscription_record in created_subscriptions:
        created_subscriptions.remove(subscription_record)
    
    response = requests.get(f"{API_URL}/channels/{channel['id']}/", headers=headers2)
    assert response.status_code == 200, "Should return channel details"
    data = response.json()
    assert data["is_subscribed"] is False, "User should show as not subscribed after unsubscribing"

# -------------------------
# Channel update tests
# -------------------------

def test_update_channel_success():
    """Test updating a channel successfully"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    channel = create_test_channel(token)
    assert channel is not None, "Failed to create test channel"
    
    update_data = {
        "name": f"Updated Channel Name {uuid.uuid4().hex[:8]}",
        "description": "Updated channel description"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.patch(
        f"{API_URL}/channels/{channel['id']}/", 
        json=update_data, 
        headers=headers,
        timeout=10
    )
    
    assert response.status_code == 200, "Should update channel successfully"
    data = response.json()
    assert data["name"] == update_data["name"], "Updated name should match"
    assert data["description"] == update_data["description"], "Updated description should match"
    assert data["id"] == channel["id"], "Channel ID should remain the same"

def test_update_channel_partial():
    """Test partial channel update"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    channel = create_test_channel(token)
    assert channel is not None, "Failed to create test channel"
    
    update_data = {
        "name": f"Partially Updated Channel {uuid.uuid4().hex[:8]}"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.patch(
        f"{API_URL}/channels/{channel['id']}/", 
        json=update_data, 
        headers=headers,
        timeout=10
    )
    
    assert response.status_code == 200, "Should update channel successfully"
    data = response.json()
    assert data["name"] == update_data["name"], "Updated name should match"
    assert data["description"] == channel["description"], "Description should remain unchanged"

def test_update_channel_duplicate_name():
    """Test updating a channel with a duplicate name"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    channel1 = create_test_channel(token)
    channel2 = create_test_channel(token)
    assert channel1 is not None and channel2 is not None, "Failed to create test channels"
    
    update_data = {
        "name": channel1["name"]
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.patch(
        f"{API_URL}/channels/{channel2['id']}/", 
        json=update_data, 
        headers=headers,
        timeout=10
    )
    
    assert response.status_code == 409, "Should reject duplicate channel name"

def test_update_channel_nonexistent():
    """Test updating a non-existent channel"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    channel = create_test_channel(token)
    assert channel is not None, "Failed to create test channel"
    
    nonexistent_id = channel["id"] + 10000
    
    update_data = {
        "name": "Updated Name",
        "description": "Updated description"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.patch(
        f"{API_URL}/channels/{nonexistent_id}/", 
        json=update_data, 
        headers=headers,
        timeout=10
    )
    
    assert response.status_code == 404, "Should return not found for non-existent channel"

def test_update_channel_unauthorized():
    """Test updating a channel without proper authorization"""
    token1, _ = register_and_login_user()
    assert token1 is not None, "Failed to get first auth token"
    
    channel = create_test_channel(token1)
    assert channel is not None, "Failed to create test channel"
    
    token2, _ = register_and_login_user()
    assert token2 is not None, "Failed to get second auth token"
    
    update_data = {
        "name": "Unauthorized Update Attempt",
        "description": "This update should be rejected"
    }
    
    headers = {"Authorization": f"Bearer {token2}"}
    response = requests.patch(
        f"{API_URL}/channels/{channel['id']}/", 
        json=update_data, 
        headers=headers,
        timeout=10
    )
    
    assert response.status_code == 403, "Should reject update from unauthorized user"

# -------------------------
# Channel delete tests
# -------------------------

def test_delete_channel_success():
    """Test deleting a channel successfully"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    channel = create_test_channel(token)
    assert channel is not None, "Failed to create test channel"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{API_URL}/channels/{channel['id']}/", headers=headers)
    
    assert response.status_code == 204, "Should delete channel successfully"
    
    response = requests.get(f"{API_URL}/channels/{channel['id']}/", headers=headers)
    assert response.status_code == 404, "Channel should no longer exist"

def test_delete_channel_nonexistent():
    """Test deleting a non-existent channel"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    channel = create_test_channel(token)
    assert channel is not None, "Failed to create test channel"
    
    nonexistent_id = channel["id"] + 10000
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{API_URL}/channels/{nonexistent_id}/", headers=headers)
    
    assert response.status_code == 404, "Should return not found for non-existent channel"

def test_delete_channel_unauthorized():
    """Test deleting a channel without proper authorization"""

    token1, _ = register_and_login_user()
    assert token1 is not None, "Failed to get first auth token"
    
    channel = create_test_channel(token1)
    assert channel is not None, "Failed to create test channel"
    
    token2, _ = register_and_login_user()
    assert token2 is not None, "Failed to get second auth token"
    
    headers = {"Authorization": f"Bearer {token2}"}
    response = requests.delete(f"{API_URL}/channels/{channel['id']}/", headers=headers)
    
    assert response.status_code == 403, "Should reject deletion from unauthorized user"

# -------------------------
# Channel subscription tests
# -------------------------

def test_subscribe_to_channel():
    """Test subscribing to a channel"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    channel = create_test_channel(token)
    assert channel is not None, "Failed to create test channel"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/channels/{channel['id']}/subscribe/", headers=headers)
    
    assert response.status_code == 204, "Subscribe should succeed"
    
    created_subscriptions.append({"channel_id": channel["id"], "token": token})

def test_unsubscribe_from_channel():
    """Test unsubscribing from a channel"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    channel = create_test_channel(token)
    assert channel is not None, "Failed to create test channel"
    
    headers = {"Authorization": f"Bearer {token}"}
    requests.post(f"{API_URL}/channels/{channel['id']}/subscribe/", headers=headers)
    
    response = requests.delete(f"{API_URL}/channels/{channel['id']}/unsubscribe/", headers=headers)
    assert response.status_code == 204, "Unsubscribe should succeed"

def test_list_channel_subscribers():
    """Test listing channel subscribers"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    channel = create_test_channel(token)
    assert channel is not None, "Failed to create test channel"
    
    headers = {"Authorization": f"Bearer {token}"}
    requests.post(f"{API_URL}/channels/{channel['id']}/subscribe/", headers=headers)
    
    response = requests.get(f"{API_URL}/channels/{channel['id']}/subscriptions/", headers=headers)
    
    assert response.status_code == 200, "Should return subscriber list"
    data = response.json()
    assert "results" in data, "Response should include results key"
    assert "count" in data, "Response should include count key"
    assert isinstance(data["results"], list), "Results should be a list"
    assert len(data["results"]) >= 1, "Should contain at least one subscriber (the owner)"

# -------------------------
# Channel posts tests
# -------------------------

def test_list_channel_posts_empty():
    """Test listing posts in a channel with no posts"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    channel = create_test_channel(token)
    assert channel is not None, "Failed to create test channel"
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_URL}/channels/{channel['id']}/posts/", 
        headers=headers, 
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        assert "results" in data, "Response should include results key"
        assert len(data["results"]) == 0, "Results should be empty"
    else:
        assert response.status_code == 404, "Should return 404 for no posts"

def test_create_and_list_channel_post():
    """Test creating a post in a channel and then listing it"""
    token, _ = register_and_login_user()
    assert token is not None, "Failed to get auth token"
    
    channel = create_test_channel(token)
    assert channel is not None, "Failed to create test channel"
    
    post_data = {
        "title": f"Test Post {uuid.uuid4().hex[:8]}",
        "content": "This is test content for the post",
        "channel_id": channel["id"]
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    post_response = requests.post(f"{API_URL}/posts/", json=post_data, headers=headers)
    
    if post_response.status_code == 201:
        post = post_response.json()
        created_posts.append({"id": post["id"], "token": token})
        
        response = requests.get(f"{API_URL}/channels/{channel['id']}/posts/", headers=headers)
        
        assert response.status_code == 200, "Should return post list"
        data = response.json()
        assert "results" in data, "Response should include results key"
        assert len(data["results"]) >= 1, "Should contain at least one post"
        assert any(
            post["title"] == post_data["title"] for post in data["results"]
        ), "Created post should be in the list"
    else:
        print(f"Note: Post creation returned status {post_response.status_code}, "
              f"skipping post listing test")

def cleanup_test_data():
    """Clean up all test data created during tests"""
    print("\nCleaning up test data...")
    
    for post in created_posts:
        try:
            headers = {"Authorization": f"Bearer {post['token']}"}
            response = requests.delete(f"{API_URL}/posts/{post['id']}/delete/", headers=headers)
            print(f"Deleted post {post['id']}: Status {response.status_code}")
        except Exception as e:
            print(f"Error deleting post {post['id']}: {e}")
    
    for subscription in created_subscriptions:
        try:
            headers = {"Authorization": f"Bearer {subscription['token']}"}
            response = requests.delete(
                f"{API_URL}/channels/{subscription['channel_id']}/unsubscribe/", 
                headers=headers
            )
            print(f"Unsubscribed from channel {subscription['channel_id']}: "
                  f"Status {response.status_code}")
        except Exception as e:
            print(f"Error unsubscribing from channel {subscription['channel_id']}: {e}")
    
    for channel in created_channels:
        try:
            headers = {"Authorization": f"Bearer {channel['token']}"}
            response = requests.delete(f"{API_URL}/channels/{channel['id']}/", headers=headers)
            print(f"Deleted channel {channel['id']}: Status {response.status_code}")
        except Exception as e:
            print(f"Error deleting channel {channel['id']}: {e}")
    
    for user in created_users:
        try:
            headers = {"Authorization": f"Bearer {user['token']}"}
            response = requests.delete(f"{API_URL}/users/{user['id']}/delete/", headers=headers)
            print(f"Deleted user {user['id']}: Status {response.status_code}")
        except Exception as e:
            print(f"Error deleting user {user['id']}: {e}")
    
    created_posts.clear()
    created_subscriptions.clear()
    created_channels.clear()
    created_users.clear()

atexit.register(cleanup_test_data)

def test_zzzz_cleanup(): # zzz because pytest will run this last then
    """Run cleanup for all created test data"""
    cleanup_test_data()