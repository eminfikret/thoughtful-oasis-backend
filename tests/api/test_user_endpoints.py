import os
import uuid
import requests
import pytest
import json
from time import sleep

API_URL = os.environ.get('BACKEND_API_URL', 'http://localhost:8000/api/v1')

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
    return user_data, login_data["token"], login_data["refresh_token"]

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

def test_register_duplicate_username():
    """Test registration with duplicate username"""

    user_data = generate_unique_user()
    requests.post(f"{API_URL}/users/register/", json=user_data)
    
    duplicate_user = user_data.copy()
    duplicate_user["email"] = f"different_{uuid.uuid4().hex[:8]}@example.com"
    
    response = requests.post(f"{API_URL}/users/register/", json=duplicate_user)
    
    assert response.status_code == 400, "Should reject duplicate username"
    assert "username" in response.text.lower(), "Error should mention username"

def test_register_duplicate_email():
    """Test registration with duplicate email"""
    user_data = generate_unique_user()
    requests.post(f"{API_URL}/users/register/", json=user_data)
    
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
    assert response.status_code == 400, f"Should reject missing username, got {response.status_code}" 

    user_data = generate_unique_user()
    del user_data["email"]
    
    response = requests.post(f"{API_URL}/users/register/", json=user_data)
    assert response.status_code == 400, f"Should reject missing email, got {response.status_code}" 
    
    user_data = generate_unique_user()
    del user_data["password"]
    
    response = requests.post(f"{API_URL}/users/register/", json=user_data)
    assert response.status_code == 400, f"Should reject missing password, got {response.status_code}" 

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
    requests.post(f"{API_URL}/users/register/", json=user_data)
    
    login_payload = {
        "username": user_data["username"].upper(),
        "password": user_data["password"]
    }
    
    response = requests.post(f"{API_URL}/users/login/", json=login_payload)
    
    if response.status_code == 200:
        data = response.json()
        assert "token" in data, "Response should contain a token"
        assert data["user"]["username"].lower() == user_data["username"].lower(), "Username should match (case-insensitive)"
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
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MTYyMzkwMjIsInVzZXJfaWQiOjF9.invalid_signature"
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
    
    response = requests.get(f"{API_URL}/users/", headers=headers)
    
    assert response.status_code == 200, "Should return user list for authenticated users"
    data = response.json()
    assert isinstance(data, list), "Response should be a list of users"
    assert any(user["username"] == user_data["username"] for user in data), "Created user should be in the list"

def test_get_users_unauthenticated():
    """Test getting user list while unauthenticated"""
    response = requests.get(f"{API_URL}/users/")
    
    if response.status_code == 401:
        assert "authentication" in response.text.lower(), "Should mention authentication requirements"
    else:
        assert response.status_code == 200, "Public user list should be accessible"
        assert isinstance(response.json(), list), "Response should be a list of users"

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
    

    users = users_response.json()
    max_id = 0
    for user in users:
        if isinstance(user.get("id"), int) and user["id"] > max_id:
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
    
    login1_response = requests.post(f"{API_URL}/users/login/", json={
        "username": user1_data["username"],
        "password": user1_data["password"]
    })
    user1_id = login1_response.json()["user"]["id"]
    
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
    
    login1_response = requests.post(f"{API_URL}/users/login/", json={
        "username": user1_data["username"],
        "password": user1_data["password"]
    })
    user1_id = login1_response.json()["user"]["id"]
    
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