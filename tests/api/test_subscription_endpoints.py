import atexit
import os
import uuid

import requests

API_URL = os.environ.get('BACKEND_API_URL', 'http://localhost:8000/api/v1')

created_users = []
created_channels = []
created_subscriptions = []

# -------------------------
# Utility Functions
# -------------------------

def generate_unique_user():
    """Generate unique user data for testing"""
    unique_id = uuid.uuid4().hex[:8]
    return {
        "username": f"test_user_{unique_id}",
        "email": f"test_{unique_id}@example.com",
        "password": "SecurePass123!",
        "password2": "SecurePass123!",
        "first_name": "Test",
        "last_name": "User"
    }

def register_test_user(is_admin=False):
    """Register a test user and return user data, token, and user_id"""
    user_data = generate_unique_user()
    if is_admin:
        user_data["username"] = f"admin_{user_data['username']}"
    
    response = requests.post(f"{API_URL}/users/register/", json=user_data)
    
    if response.status_code != 201:  
        print(f"Registration failed with status {response.status_code}")
        print(f"Response: {response.text[:200]}")
        return None, None, None

    login_response = requests.post(f"{API_URL}/users/login/", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    
    if login_response.status_code != 200:
        print(f"Login failed with status {login_response.status_code}")
        return user_data, None, None
    
    login_data = login_response.json()
    user_id = login_data["user"]["id"]
    
    created_users.append({"id": user_id, "token": login_data["token"]})
    
    return user_data, login_data["token"], user_id

def create_test_channel(token, name=None, description=None):
    """Create a test channel and return the channel data"""
    if name is None:
        name = f"Test Channel {uuid.uuid4().hex[:8]}"
    
    if description is None:
        description = "Test channel description for subscription tests"
    
    channel_data = {
        "name": name,
        "description": description
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/channels/", json=channel_data, headers=headers)
    
    if response.status_code != 201:
        print(f"Channel creation failed: {response.status_code} - {response.text}")
        return None
    
    channel = response.json()

    created_channels.append({"id": channel["id"], "token": token})
    
    return channel

def subscribe_to_channel(token, channel_id):
    """Subscribe to a channel and return response"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/channels/{channel_id}/subscribe/", headers=headers)
    
    if response.status_code == 204:
        created_subscriptions.append({"channel_id": channel_id, "token": token})
    
    return response

def setup_test_environment():
    """Setup one user, one admin and one channel for testing subscriptions"""
    user_data, token, user_id = register_test_user()
    admin_data, admin_token, admin_id = register_test_user(is_admin=True)
    
    if token is None or admin_token is None:
        return None, None, None, None, None, None
    
    channel = create_test_channel(token)
    
    if channel is None:
        return user_data, token, user_id, admin_data, admin_token, None
    
    return user_data, token, user_id, admin_data, admin_token, channel

# -------------------------
# Subscribe Tests
# -------------------------

def test_subscribe_success():
    """Test successfully subscribing to a channel"""
    user_data, token, _, _, _, channel = setup_test_environment()
    
    response = subscribe_to_channel(token, channel["id"])
    
    assert response.status_code == 204, "Should successfully subscribe to channel"

def test_subscribe_unauthenticated():
    """Test subscribing without authentication"""
    _, _, _, _, _, channel = setup_test_environment()
    
    response = requests.post(f"{API_URL}/channels/{channel['id']}/subscribe/")
    
    assert response.status_code == 401, "Should require authentication"

def test_subscribe_nonexistent_channel():
    """Test subscribing to a channel that doesn't exist"""
    _, token, _, _, _, channel = setup_test_environment()
    
    nonexistent_id = channel["id"] + 10000
    
    response = subscribe_to_channel(token, nonexistent_id)
    
    assert response.status_code == 404, "Should return 404 for non-existent channel"
    assert "not found" in response.text.lower(), "Error message should indicate channel not found"

def test_subscribe_idempotence():
    """Test subscribing to a channel twice (should be idempotent)"""
    _, token, _, _, _, channel = setup_test_environment()
    
    first_response = subscribe_to_channel(token, channel["id"])
    assert first_response.status_code == 204
    
    second_response = subscribe_to_channel(token, channel["id"])
    assert second_response.status_code == 204, "Second subscription should also succeed"

# -------------------------
# Unsubscribe Tests
# -------------------------

def test_unsubscribe_success():
    """Test successfully unsubscribing from a channel"""
    _, token, _, _, _, channel = setup_test_environment()
    
    subscribe_response = subscribe_to_channel(token, channel["id"])
    assert subscribe_response.status_code == 204
    
    headers = {"Authorization": f"Bearer {token}"}
    unsubscribe_response = requests.delete(f"{API_URL}/channels/{channel['id']}/unsubscribe/", 
                                           headers=headers)
    
    assert unsubscribe_response.status_code == 204, "Should successfully unsubscribe"

def test_unsubscribe_not_subscribed():
    """Test unsubscribing from a channel not subscribed to"""
    _, token, _, _, _, channel = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    unsubscribe_response = requests.delete(f"{API_URL}/channels/{channel['id']}/unsubscribe/",
                                            headers=headers)
    
    assert unsubscribe_response.status_code == 204, "Unsubscribe should be idempotent"

def test_unsubscribe_unauthenticated():
    """Test unsubscribing without authentication"""
    _, _, _, _, _, channel = setup_test_environment()
    
    response = requests.delete(f"{API_URL}/channels/{channel['id']}/unsubscribe/")
    
    assert response.status_code == 401, "Should require authentication"

def test_unsubscribe_nonexistent_channel():
    """Test unsubscribing from a non-existent channel"""
    _, token, _, _, _, channel = setup_test_environment()
    
    nonexistent_id = channel["id"] + 10000
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{API_URL}/channels/{nonexistent_id}/unsubscribe/", headers=headers)
    
    assert response.status_code == 404, "Should return 404 for non-existent channel"

# -------------------------
# List Channel Subscribers Tests
# -------------------------

def test_list_subscribers_as_owner():
    """Test listing channel subscribers as owner"""
    _, token, _, _, _, channel = setup_test_environment()
    
    subscribe_to_channel(token, channel["id"])
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/channels/{channel['id']}/subscriptions/", headers=headers)
    
    assert response.status_code == 200, "Channel owner should be able to list subscribers"
    data = response.json()
    assert "results" in data, "Response should include results field"
    assert "count" in data, "Response should include count field"
    assert isinstance(data["results"], list), "Results should be a list"
    assert len(data["results"]) > 0, "Should contain at least one subscriber"

def test_list_subscribers_unauthenticated():
    """Test listing channel subscribers without authentication"""
    _, _, _, _, _, channel = setup_test_environment()
    
    response = requests.get(f"{API_URL}/channels/{channel['id']}/subscriptions/")
    
    assert response.status_code == 401, "Should require authentication"

def test_list_subscribers_nonexistent_channel():
    """Test listing subscribers for a non-existent channel"""
    _, token, _, _, _, channel = setup_test_environment()
    
    nonexistent_id = channel["id"] + 10000
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/channels/{nonexistent_id}/subscriptions/", headers=headers)
    
    assert response.status_code == 404, "Should return 404 for non-existent channel"

def test_list_subscribers_not_owner():
    """Test listing subscribers without being channel owner"""
    owner_data, owner_token, _ = register_test_user()
    channel = create_test_channel(owner_token)
    
    user_data, user_token, _ = register_test_user()
    
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{API_URL}/channels/{channel['id']}/subscriptions/", headers=headers)
    
    assert response.status_code == 403, "Only channel owner or admin should access subscribers"

def test_list_subscribers_pagination():
    """Test pagination works correctly for channel subscribers"""
    user_data, token, _, _, _, channel = setup_test_environment()
    
    subscribe_to_channel(token, channel["id"])
    
    for i in range(3):
        additional_data, additional_token, _ = register_test_user()
        subscribe_to_channel(additional_token, channel["id"])
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_URL}/channels/{channel['id']}/subscriptions/?limit=2&offset=0", 
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 2, "Should respect limit parameter"
    
    response = requests.get(
        f"{API_URL}/channels/{channel['id']}/subscriptions/?limit=2&offset=2", 
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "next" in data or "previous" in data, "Should include pagination links"

# -------------------------
# List User Subscriptions Tests
# -------------------------

def test_list_own_subscriptions():
    """Test user listing their own subscriptions"""
    user_data, token, user_id, _, _, channel = setup_test_environment()
    
    subscribe_to_channel(token, channel["id"])
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/users/{user_id}/subscriptions/", headers=headers)
    
    assert response.status_code == 200, "User should be able to list their own subscriptions"
    data = response.json()
    assert "results" in data, "Response should include results field"
    assert "count" in data, "Response should include count field"
    assert isinstance(data["results"], list), "Results should be a list"
    assert len(data["results"]) > 0, "Should contain at least one subscription"

def test_list_other_user_subscriptions():
    """Test listing another user's subscriptions (should be forbidden)"""

    user1_data, token1, user1_id = register_test_user()
    
    user2_data, token2, user2_id = register_test_user()
    
    headers = {"Authorization": f"Bearer {token1}"}
    response = requests.get(f"{API_URL}/users/{user2_id}/subscriptions/", headers=headers)
    
    assert response.status_code == 403, "Should forbid access to another user's subscriptions"

def test_list_subscriptions_unauthenticated():
    """Test listing subscriptions without authentication"""
    _, _, user_id, _, _, _ = setup_test_environment()
    
    response = requests.get(f"{API_URL}/users/{user_id}/subscriptions/")
    
    assert response.status_code == 401, "Should require authentication"

def test_list_subscriptions_nonexistent_user():
    """Test listing subscriptions for a non-existent user"""
    _, token, user_id, _, _, _ = setup_test_environment()
    
    nonexistent_id = user_id + 10000
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/users/{nonexistent_id}/subscriptions/", headers=headers)
    
    assert response.status_code == 404, "Should return 404 for non-existent user"

def test_list_subscriptions_pagination():
    """Test pagination works correctly for user subscriptions"""
    user_data, token, user_id, _, _, _ = setup_test_environment()
    
    for i in range(5):
        channel = create_test_channel(token)
        subscribe_to_channel(token, channel["id"])
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/users/{user_id}/subscriptions/?limit=2&offset=0", 
                            headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 2, "Should respect limit parameter"
    
    response = requests.get(f"{API_URL}/users/{user_id}/subscriptions/?limit=2&offset=2", 
                            headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "next" in data or "previous" in data, "Should include pagination links"

def test_admin_list_user_subscriptions():
    """Test admin listing another user's subscriptions"""
    user_data, token, user_id, admin_data, admin_token, channel = setup_test_environment()
    
    subscribe_to_channel(token, channel["id"])
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{API_URL}/users/{user_id}/subscriptions/", headers=headers)
    
    assert response.status_code in (200, 403), "Admin either has access or is properly denied"
    
    if response.status_code == 200:
        data = response.json()
        assert "results" in data, "Response should include results field"

def cleanup_test_data():
    """Clean up all test data created during tests"""
    print("\nCleaning up subscription test data...")
    
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
    
    created_subscriptions.clear()
    created_channels.clear()
    created_users.clear()

atexit.register(cleanup_test_data)

def test_zzz_cleanup():
    """Run cleanup for all created test data"""
    cleanup_test_data()
