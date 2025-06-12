import atexit
import os
import uuid

import requests

API_URL = os.environ.get('BACKEND_API_URL', 'http://localhost:8000/api/v1')

created_users = []

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

def register_test_user():
    """Register a test user and return user data and tokens"""
    user_data = generate_unique_user()
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
    token = login_data["token"]
    user_id = login_data["user"]["id"]
    
    created_users.append({"id": user_id, "token": token})
    
    return user_data, token, login_data["refresh_token"]

def track_registered_user(username, password):
    """Track a registered user for cleanup"""
    login_response = requests.post(f"{API_URL}/users/login/", json={
        "username": username,
        "password": password
    })
    
    if login_response.status_code != 200:
        print(f"Login failed for tracking user {username}: {login_response.status_code}")
        return
    
    login_data = login_response.json()
    token = login_data["token"]
    user_id = login_data["user"]["id"]
    
    created_users.append({"id": user_id, "token": token})

def cleanup_created_users():
    for user in created_users:
        try:
            requests.delete(f"{API_URL}/users/{user['id']}/delete/", headers={
                "Authorization": f"Bearer {user['token']}"
            })
        except Exception as e:
            print(f"Error cleaning up user {user['id']}: {e}")

atexit.register(cleanup_created_users)

# -------------------------
# Registration tests
# -------------------------

def test_register_user_success():
    """Test successful user registration"""
    user_data = generate_unique_user()
    
    response = requests.post(f"{API_URL}/users/register/", json=user_data)
    
    assert response.status_code == 201, f"Registration failed with status {response.status_code}"
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    
    track_registered_user(user_data["username"], user_data["password"])

def test_register_duplicate_username():
    """Test registration with duplicate username"""

    user_data = generate_unique_user()
    response = requests.post(f"{API_URL}/users/register/", json=user_data)
    
    if response.status_code == 201:
        track_registered_user(user_data["username"], user_data["password"])
    
    duplicate_user = user_data.copy()
    duplicate_user["email"] = f"different_{uuid.uuid4().hex[:8]}@example.com"
    
    response = requests.post(f"{API_URL}/users/register/", json=duplicate_user)
    
    assert response.status_code == 400, "Should reject duplicate username"
    assert "username" in response.text.lower(), "Error should mention username"

def test_register_duplicate_email():
    """Test registration with duplicate email"""
    user_data = generate_unique_user()
    response = requests.post(f"{API_URL}/users/register/", json=user_data)
    
    if response.status_code == 201:
        track_registered_user(user_data["username"], user_data["password"])
    
    duplicate_user = user_data.copy()
    duplicate_user["username"] = f"different_{uuid.uuid4().hex[:8]}"
    
    response = requests.post(f"{API_URL}/users/register/", json=duplicate_user)
    
    assert response.status_code == 400, "Should reject duplicate email"
    assert "email" in response.text.lower(), "Error should mention email"

def test_register_password_mismatch():
    """Test registration with mismatched passwords"""
    user_data = generate_unique_user()
    user_data["password2"] = "DifferentPassword123!@#"
    
    response = requests.post(f"{API_URL}/users/register/", json=user_data)
    
    assert response.status_code == 400, "Should reject mismatched passwords"
    assert "password" in response.text.lower(), "Error should mention password"

def test_register_missing_fields():
    """Test registration with missing required fields"""
    user_data = generate_unique_user()
    del user_data["username"]
    
    response = requests.post(f"{API_URL}/users/register/", json=user_data)
    assert response.status_code == 400, (
        f"Should reject missing username, got {response.status_code}"
    )

    user_data = generate_unique_user()
    del user_data["email"]
    
    response = requests.post(f"{API_URL}/users/register/", json=user_data)
    assert response.status_code == 400, f"Should reject missing email, got {response.status_code}" 
    
    user_data = generate_unique_user()
    del user_data["password"]
    
    response = requests.post(f"{API_URL}/users/register/", json=user_data)
    assert response.status_code == 400, (
        f"Should reject missing password, got {response.status_code}"
    )

def test_register_weak_password():
    """Test registration with weak password"""
    user_data = generate_unique_user()
    user_data["password"] = "weak"
    user_data["password2"] = "weak"
    
    response = requests.post(f"{API_URL}/users/register/", json=user_data)
    
    assert response.status_code == 400, "Should reject weak password"
    assert "password" in response.text.lower(), "Error should mention password"

# -------------------------
# Login tests
# -------------------------

def test_login_success():
    """Test successful login"""
    user_data = generate_unique_user()
    register_response = requests.post(f"{API_URL}/users/register/", json=user_data)
    assert register_response.status_code == 201, "Registration failed" 

    track_registered_user(user_data["username"], user_data["password"])

    login_payload = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    
    response = requests.post(f"{API_URL}/users/login/", json=login_payload)
    
    assert response.status_code == 200, "Login should succeed"
    data = response.json()
    assert "token" in data, "Response should contain a token"
    assert "refresh_token" in data, "Response should contain a refresh token"
    assert "user" in data, "Response should contain user data"
    assert data["user"]["username"] == user_data["username"]

def test_login_invalid_credentials():
    """Test login with invalid credentials"""
    login_payload = {
        "username": f"nonexistent_user_{uuid.uuid4().hex[:8]}",
        "password": "wrong_password"
    }
    
    response = requests.post(f"{API_URL}/users/login/", json=login_payload)
    
    assert response.status_code == 401, "Login with invalid credentials should fail"

def test_login_missing_credentials():
    """Test login with missing credentials"""
    response = requests.post(f"{API_URL}/users/login/", json={"password": "password123"})
    assert response.status_code == 400, "Should reject missing username"

    response = requests.post(f"{API_URL}/users/login/", json={"username": "someuser"})
    assert response.status_code == 400, "Should reject missing password"

def test_login_case_insensitive_username():
    """Test that login is case-insensitive for username"""
    user_data = generate_unique_user()
    response = requests.post(f"{API_URL}/users/register/", json=user_data)
    
    if response.status_code == 201:
        track_registered_user(user_data["username"], user_data["password"])
    
    login_payload = {
        "username": user_data["username"].upper(),
        "password": user_data["password"]
    }
    
    response = requests.post(f"{API_URL}/users/login/", json=login_payload)
    
    if response.status_code == 200:
        data = response.json()
        assert "token" in data, "Response should contain a token"
        assert data["user"]["username"].lower() == user_data["username"].lower()
    else:
        print("Note: Server appears to use case-sensitive usernames")

# -------------------------
# Token refresh tests
# -------------------------

def test_token_refresh_success():
    """Test successful token refresh"""
    user_data, token, refresh_token = register_test_user()
    assert refresh_token is not None, "Failed to get refresh token"
    
    refresh_payload = {
        "refresh_token": refresh_token
    }
    
    response = requests.post(f"{API_URL}/users/tokenRefresh/", json=refresh_payload)
    
    assert response.status_code == 200, "Token refresh should succeed"
    data = response.json()
    assert "access_token" in data, "Response should contain a new access token"

def test_token_refresh_invalid_token():
    """Test token refresh with invalid token"""
    refresh_payload = {
        "refresh_token": "invalid_token_here"
    }
    
    response = requests.post(f"{API_URL}/users/tokenRefresh/", json=refresh_payload)
    
    assert response.status_code == 401, "Should reject invalid refresh token"

def test_token_refresh_missing_token():
    """Test token refresh with missing token"""
    response = requests.post(f"{API_URL}/users/tokenRefresh/", json={})
    
    assert response.status_code == 400, "Should reject missing refresh token"

def test_token_expired():
    """Test using an expired token"""
    headers = {
        "Authorization": "Bearer "
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MTYyMzkwMjIsInVzZXJfaWQiOjF9.invalid_signature"
    }
    
    response = requests.get(f"{API_URL}/users/", headers=headers)
    
    assert response.status_code == 401, "Should reject invalid/expired token"

# -------------------------
# User list tests
# -------------------------

def test_get_users_authenticated():
    """Test getting user list while authenticated"""
    user_data, token, _ = register_test_user()
    assert token is not None, "Failed to get auth token"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    login_response = requests.post(f"{API_URL}/users/login/", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    assert login_response.status_code == 200, "Login failed to confirm user exists"
    login_response.json()["user"]["id"]
    
    response = requests.get(f"{API_URL}/users/?search={user_data['username']}", headers=headers)
    
    assert response.status_code == 200, "Should return user list for authenticated users"
    data = response.json()
    assert "results" in data, "Response should include results field for pagination"
    assert "count" in data, "Response should include total count"
    assert isinstance(data["results"], list), "Results should be a list of users"
    
    assert data["count"] > 0, "Search should return at least one result"
    assert any(
        user["username"] == user_data["username"] for user in data["results"]
    ), "Created user should be found by search"

def test_get_users_with_pagination():
    """Test user list pagination"""
    tokens = []
    usernames = []
    for _ in range(3):
        user_data, token, _ = register_test_user()
        if token:
            tokens.append(token)
            usernames.append(user_data["username"])
    
    assert tokens, "Failed to create test users"
    
    headers = {"Authorization": f"Bearer {tokens[0]}"}
    
    response = requests.get(f"{API_URL}/users/?limit=2&offset=0", headers=headers)
    assert response.status_code == 200, "Should return paginated results"
    data = response.json()
    
    assert "results" in data, "Response should include results field"
    assert "count" in data, "Response should include total count"
    assert "next" in data, "Response should include next page URL"
    assert len(data["results"]) <= 2, "Should respect the limit parameter"
    
    if data.get("next"):
        response = requests.get(data["next"], headers=headers)
        assert response.status_code == 200, "Should fetch second page"
        page2_data = response.json()
        assert "results" in page2_data, "Second page should include results"
        assert "previous" in page2_data, "Second page should include previous page URL"
        
        page1_ids = [user["id"] for user in data["results"]]
        page2_ids = [user["id"] for user in page2_data["results"]]
        assert not any(id in page2_ids for id in page1_ids), "Pages should contain different users"

def test_get_users_with_search():
    """Test searching users"""

    unique_id = uuid.uuid4().hex[:8]
    search_username = f"searchable_user_{unique_id}"
    
    user_data = generate_unique_user()
    user_data["username"] = search_username
    
    register_response = requests.post(f"{API_URL}/users/register/", json=user_data)
    assert register_response.status_code == 201, "Failed to create searchable user"
    
    login_response = requests.post(f"{API_URL}/users/login/", json={
        "username": search_username,
        "password": user_data["password"]
    })
    token = login_response.json()["token"]
    user_id = login_response.json()["user"]["id"]
    created_users.append({"id": user_id, "token": token})
    
    headers = {"Authorization": f"Bearer {token}"}
    search_term = "searchable"
    response = requests.get(f"{API_URL}/users/?search={search_term}", headers=headers)
    
    assert response.status_code == 200, "Search should work"
    data = response.json()
    
    assert "results" in data, "Response should include results field"
    assert "count" in data, "Response should include count field"
    assert len(data["results"]) > 0, "Should find at least the created user"
    assert any(
        search_term in user["username"].lower() for user in data["results"]
    ), "Search should find username match"

# -------------------------
# User detail tests
# -------------------------

def test_get_user_detail_existing():
    """Test getting details of an existing user"""

    user_data, token, _ = register_test_user()
    assert token is not None, "Failed to get auth token"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    login_response = requests.post(f"{API_URL}/users/login/", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    user_id = login_response.json()["user"]["id"]
    
    response = requests.get(f"{API_URL}/users/{user_id}/", headers=headers)
    
    assert response.status_code == 200, "Should return user details"
    data = response.json()
    assert data["username"] == user_data["username"], "Username should match"
    assert data["email"] == user_data["email"], "Email should match"

def test_get_user_detail_nonexistent():
    """Test getting details of a non-existent user"""
    _, token, _ = register_test_user()
    assert token is not None, "Failed to get auth token"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    users_response = requests.get(f"{API_URL}/users/", headers=headers)
    assert users_response.status_code == 200, "Should get users list"
    
    data = users_response.json()
    max_id = 0
    
    if "results" in data and isinstance(data["results"], list):
        for user in data["results"]:
            if isinstance(user, dict) and isinstance(user.get("id"), int) and user["id"] > max_id:
                max_id = user["id"]
    
    nonexistent_id = max_id + 10000
    
    response = requests.get(f"{API_URL}/users/{nonexistent_id}/", headers=headers)
    
    assert response.status_code == 404, "Should return not found for non-existent user"

def test_get_user_detail_unauthorized():
    """Test getting user details without authentication"""
    user_data, _, _ = register_test_user()
    
    login_response = requests.post(f"{API_URL}/users/login/", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    user_id = login_response.json()["user"]["id"]
    
    response = requests.get(f"{API_URL}/users/{user_id}/")
    
    assert response.status_code == 401, "Should require authentication"

# -------------------------
# Check availability tests
# -------------------------

def test_check_availability():
    """Test checking username and email availability"""
    user_data = generate_unique_user()
    register_response = requests.post(f"{API_URL}/users/register/", json=user_data)
    assert register_response.status_code == 201, "Registration failed"
    
    track_registered_user(user_data["username"], user_data["password"])
    
    response = requests.get(f"{API_URL}/users/check-availability/?username={user_data['username']}")
    assert response.status_code == 200, "Check availability should work"
    data = response.json()
    assert data.get("username_exists") is True, "Username should exist"
    
    available_username = f"available_{uuid.uuid4().hex[:8]}"
    response = requests.get(f"{API_URL}/users/check-availability/?username={available_username}")
    assert response.status_code == 200, "Check availability should work"
    data = response.json()
    assert data.get("username_exists") is False, "Username should not exist"
    
    response = requests.get(f"{API_URL}/users/check-availability/?email={user_data['email']}")
    assert response.status_code == 200, "Check availability should work"
    data = response.json()
    assert data.get("email_exists") is True, "Email should exist"
    
    available_email = f"available_{uuid.uuid4().hex[:8]}@example.com"
    response = requests.get(f"{API_URL}/users/check-availability/?email={available_email}")
    assert response.status_code == 200, "Check availability should work"
    data = response.json()
    assert data.get("email_exists") is False, "Email should not exist"

# -------------------------
# User subscriptions tests
# -------------------------

def test_get_own_subscriptions():
    """Test getting your own subscriptions"""
    user_data, token, _ = register_test_user()
    assert token is not None, "Failed to get auth token"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    login_response = requests.post(f"{API_URL}/users/login/", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    user_id = login_response.json()["user"]["id"]
    
    response = requests.get(f"{API_URL}/users/{user_id}/subscriptions/", headers=headers)
    
    assert response.status_code == 200, "Should get subscriptions successfully"
    data = response.json()
    assert "results" in data, "Should return pagination structure"
    assert "count" in data, "Should include count in response"

def test_get_other_user_subscriptions():
    """Test getting another user's subscriptions (expect forbidden)"""
    user1_data, token1, _ = register_test_user()
    user2_data, token2, _ = register_test_user()
    
    assert token1 is not None, "Failed to get first auth token"
    
    requests.post(f"{API_URL}/users/login/", json={
        "username": user1_data["username"],
        "password": user1_data["password"]
    })

    
    login2_response = requests.post(f"{API_URL}/users/login/", json={
        "username": user2_data["username"],
        "password": user2_data["password"]
    })
    user2_id = login2_response.json()["user"]["id"]
    
    headers = {
        "Authorization": f"Bearer {token1}"
    }
    
    response = requests.get(f"{API_URL}/users/{user2_id}/subscriptions/", headers=headers)

    assert response.status_code == 403, "Should forbid access to another user's subscriptions"

# -------------------------
# User delete tests
# -------------------------

def test_delete_own_account():
    """Test deleting your own account"""
    user_data, token, _ = register_test_user()
    assert token is not None, "Failed to get auth token"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    login_response = requests.post(f"{API_URL}/users/login/", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    user_id = login_response.json()["user"]["id"]
    
    response = requests.delete(f"{API_URL}/users/{user_id}/delete/", headers=headers)
    
    assert response.status_code == 204, "Should delete account successfully"
    
    login_response = requests.post(f"{API_URL}/users/login/", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    assert login_response.status_code == 401, "Should not be able to login with deleted account"

def test_delete_other_user_account():
    """Test deleting another user's account (should fail)"""

    user1_data, token1, _ = register_test_user()
    user2_data, token2, _ = register_test_user()
    
    assert token1 is not None, "Failed to get first auth token"
    assert token2 is not None, "Failed to get second auth token"
    
    requests.post(f"{API_URL}/users/login/", json={
        "username": user1_data["username"],
        "password": user1_data["password"]
    })
    
    login2_response = requests.post(f"{API_URL}/users/login/", json={
        "username": user2_data["username"],
        "password": user2_data["password"]
    })
    user2_id = login2_response.json()["user"]["id"]
    
    headers = {
        "Authorization": f"Bearer {token1}"
    }
    
    response = requests.delete(f"{API_URL}/users/{user2_id}/delete/", headers=headers)
    
    assert response.status_code == 403, "Should reject deleting another user's account"
    
    login_response = requests.post(f"{API_URL}/users/login/", json={
        "username": user2_data["username"],
        "password": user2_data["password"]
    })
    assert login_response.status_code == 200, "User2 should still be able to login"

def cleanup_test_data():
    """Clean up all test data created during tests"""
    print("\nCleaning up user test data...")
    
    try:
        if created_users and len(created_users) > 0:
            admin_token = created_users[0]['token']
            headers = {"Authorization": f"Bearer {admin_token}"}
            
            users_response = requests.get(f"{API_URL}/users/", headers=headers)
            if users_response.status_code == 200:
                users = users_response.json()
                test_users = [u for u in users if u.get('username', '').startswith('testuser_')]
                
                tracked_ids = [u['id'] for u in created_users]
                for user in test_users:
                    if user['id'] not in tracked_ids:
                        print(f"Found untracked test user: {user['username']}")
    
    except Exception as e:
        print(f"Error looking for additional test users: {e}")
    
    for user in created_users:
        try:
            headers = {"Authorization": f"Bearer {user['token']}"
            }
            response = requests.delete(f"{API_URL}/users/{user['id']}/delete/", headers=headers)
            print(f"Deleted user {user['id']}: Status {response.status_code}")
        except Exception as e:
            print(f"Error deleting user {user['id']}: {e}")
    
    created_users.clear()

atexit.register(cleanup_test_data)

def test_zzz_cleanup():
    """Run cleanup for all created test data"""
    cleanup_test_data()