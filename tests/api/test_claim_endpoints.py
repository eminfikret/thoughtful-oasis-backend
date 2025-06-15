import atexit
import os
import time
import uuid

import requests

API_URL = os.environ.get('BACKEND_API_URL', 'http://localhost:8000/api/v1')

created_users = []
created_channels = []
created_posts = []
created_comments = []

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

def register_test_user():
    """Register a test user and return user data, token, and user_id"""
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
    user_id = login_data["user"]["id"]
    
    created_users.append({"id": user_id, "token": login_data["token"]})
    
    return user_data, login_data["token"], user_id

def create_test_channel(token):
    """Create a test channel and return the channel data"""
    channel_data = {
        "name": f"Test Channel {uuid.uuid4().hex[:8]}",
        "description": "Test channel description for claim tests"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/channels/", json=channel_data, headers=headers)
    
    if response.status_code != 201:
        print(f"Channel creation failed: {response.status_code} - {response.text}")
        return None
    
    created_channels.append({"id": response.json()["id"], "token": token})
    
    return response.json()

def create_test_post(token, channel_id, title=None, content=None):
    """Create a test post with factual claims"""
    if title is None:
        title = f"Test Post {uuid.uuid4().hex[:8]}"
    
    if content is None:
        content = (
            "The Earth is the third planet from the Sun. "
            "Water boils at 100 degrees Celsius at sea level. "
            "An average adult body contains about 5-6 liters of blood."
        )
    
    post_data = {
        "title": title,
        "content": content,
        "channel_id": channel_id
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/posts/create/", json=post_data, headers=headers)
    
    if response.status_code != 201:
        print(f"Post creation failed: {response.status_code} - {response.text}")
        return None
    
    created_posts.append({"id": response.json()["id"], "token": token})
    
    return response.json()

def create_test_comment(token, post_id, content=None):
    """Create a test comment with factual claims"""
    if content is None:
        content = (
            "Mount Everest is the highest mountain on Earth. "
            "The Amazon rainforest produces about 20% of Earth's oxygen."
        )
        
    comment_data = {
        "post_id": post_id,
        "content": content
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/comments/create/", json=comment_data, headers=headers)
    
    if response.status_code != 201:
        print(f"Comment creation failed: {response.status_code} - {response.text}")
        return None
    
    # Track for cleanup
    created_comments.append({"id": response.json()["id"], "token": token})
    
    return response.json()

def setup_test_environment():
    """Setup user, channel, post, comment for testing claims"""
    user_data, token, user_id = register_test_user()
    if token is None:
        return None, None, None, None, None, None
    
    channel = create_test_channel(token)
    if channel is None:
        return user_data, token, user_id, None, None, None
    
    post = create_test_post(token, channel["id"])
    if post is None:
        return user_data, token, user_id, channel, None, None
    
    time.sleep(1)
    
    comment = create_test_comment(token, post["id"])
    if comment is None:
        return user_data, token, user_id, channel, post, None
    
    time.sleep(1)
    
    return user_data, token, user_id, channel, post, comment

def analyze_text(token, text):
    """Analyze text for claims"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_URL}/claims/analyse/",
        json={"text": text},
        headers=headers
    )
    return response

# -------------------------
# Text Analysis Tests
# -------------------------

def test_analyze_text_success():
    """Test successfully analyzing text for claims"""
    _, token, _, _, _, _ = setup_test_environment()
    
    text = "The Earth is round. The Moon orbits the Earth."
    response = analyze_text(token, text)
    
    assert response.status_code == 201, "Should successfully analyze text"
    data = response.json()
    assert "message" in data, "Should contain a message"
    assert "claims_count" in data, "Should include claim count"
    assert "results" in data, "Should include results"
    assert isinstance(data["results"], list), "Results should be a list"
    
    for claim in data["results"]:
        assert "claim" in claim, "Each result should have a claim"
        assert "fact_check" in claim, "Each result should have a fact check"
        assert "verdict" in claim["fact_check"], "Each fact check should have a verdict"

def test_analyze_text_unauthenticated():
    """Test analyzing text without authentication"""
    text = "The Earth is round."
    response = requests.post(f"{API_URL}/claims/analyse/", json={"text": text})
    
    assert response.status_code == 401, "Should require authentication"

def test_analyze_text_empty():
    """Test analyzing empty text"""
    _, token, _, _, _, _ = setup_test_environment()
    
    response = analyze_text(token, "")
    
    assert response.status_code == 400, "Should reject empty text"
    assert "text" in response.text.lower(), "Error should mention text field"

def test_analyze_text_missing_field():
    """Test analyzing with missing text field"""
    _, token, _, _, _, _ = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/claims/analyse/", json={}, headers=headers)
    
    assert response.status_code == 400, "Should reject missing text field"

def test_analyze_text_very_long():
    """Test analyzing very long text"""
    _, token, _, _, _, _ = setup_test_environment()
    
    long_text = "The Earth is round. " * 100
    response = analyze_text(token, long_text)
    
    assert response.status_code in (201, 200), "Should handle long text"

def test_analyze_text_special_characters():
    """Test analyzing text with special characters"""
    _, token, _, _, _, _ = setup_test_environment()
    
    special_text = (
        "The Earth's diameter is 12,742 km. "
        "The symbol # is called a hashtag. "
        "Pi (π) equals 3.14159..."
    )
    response = analyze_text(token, special_text)
    
    assert response.status_code == 201, "Should handle special characters"

# -------------------------
# Claim Detail Tests
# -------------------------


def test_get_claim_details_unauthenticated():
    """Test getting claim details without authentication"""
    _, token, _, _, post, _ = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    post_response = requests.get(f"{API_URL}/posts/{post['id']}/", headers=headers)
    post_data = post_response.json()
    
    if "claims" in post_data and len(post_data["claims"]) > 0:
        claim_id = post_data["claims"][0]["claim"]["id"]
        
        response = requests.get(f"{API_URL}/claims/{claim_id}/")
        
        assert response.status_code == 401, "Should require authentication"
    else:
        print("No claims found in the post, skipping unauthenticated test")

def test_get_nonexistent_claim():
    """Test getting details of a non-existent claim"""
    _, token, _, _, post, _ = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    post_response = requests.get(f"{API_URL}/posts/{post['id']}/", headers=headers)
    post_data = post_response.json()
    
    if "claims" in post_data and len(post_data["claims"]) > 0:
        real_claim_id = post_data["claims"][0]["claim"]["id"]
        nonexistent_id = real_claim_id + 10000
        
        response = requests.get(f"{API_URL}/claims/{nonexistent_id}/", headers=headers)
        
        assert response.status_code == 404, "Should return 404 for non-existent claim"
        assert ("not found" in response.text.lower() or 
                "error" in response.text.lower()), "Error message should indicate not found"
    else:
        print("No claims found in the post, skipping non-existent claim test")

def test_get_claim_details_success():
    """Test getting claim details successfully"""
    _, token, _, _, post, _ = setup_test_environment()
    
    # First analyze text to generate some claims
    text = "The Earth is round. The Moon orbits the Earth."
    analyze_response = analyze_text(token, text)
    assert analyze_response.status_code == 201, "Should successfully analyze text"
    
    claims_data = analyze_response.json()
    if "results" in claims_data and len(claims_data["results"]) > 0:
        claim_id = claims_data["results"][0]["claim"]["id"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/claims/{claim_id}/", headers=headers)
        
        assert response.status_code == 200, (
            f"Should successfully retrieve claim details. Got: {response.text}"
        )
        data = response.json()
        assert "claim" in data, "Response should include claim data"
        assert "id" in data["claim"], "Claim should have an ID"
        assert data["claim"]["id"] == claim_id, "Should return the correct claim"
        
        if "fact_check" in data:
            assert "verdict" in data["fact_check"], "Fact check should include a verdict"
            assert "summary" in data["fact_check"], "Fact check should include a summary"
    else:
        print("No claims found in analysis, skipping claim details test")

# -------------------------
# Delete Claim Tests
# -------------------------

def test_delete_claim_unauthenticated():
    """Test deleting a claim without authentication"""
    _, token, _, _, post, _ = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    post_response = requests.get(f"{API_URL}/posts/{post['id']}/", headers=headers)
    post_data = post_response.json()
    
    if "claims" in post_data and len(post_data["claims"]) > 0:
        claim_id = post_data["claims"][0]["claim"]["id"]
        
        response = requests.delete(f"{API_URL}/claims/{claim_id}/delete")
        
        assert response.status_code == 401, "Should require authentication"
    else:
        print("No claims found in the post, skipping unauthenticated delete test")

def test_delete_nonexistent_claim():
    """Test deleting a non-existent claim"""
    _, token, _, _, post, _ = setup_test_environment()
    
    headers = {"Authorization": f"Bearer {token}"}
    post_response = requests.get(f"{API_URL}/posts/{post['id']}/", headers=headers)
    post_data = post_response.json()
    
    if "claims" in post_data and len(post_data["claims"]) > 0:
        real_claim_id = post_data["claims"][0]["claim"]["id"]
        nonexistent_id = real_claim_id + 10000
        
        response = requests.delete(f"{API_URL}/claims/{nonexistent_id}/delete", headers=headers)
        
        assert response.status_code == 404, "Should return 404 for non-existent claim"
    else:
        print("No claims found in the post, skipping non-existent claim delete test")

def test_delete_other_user_claim():
    """Test deleting another user's claim (should fail)"""

    user1_data, token1, _ = register_test_user()
    channel = create_test_channel(token1)
    post = create_test_post(token1, channel["id"])
    time.sleep(1)  
    headers1 = {"Authorization": f"Bearer {token1}"}
    post_response = requests.get(f"{API_URL}/posts/{post['id']}/", headers=headers1)
    post_data = post_response.json()
    
    if "claims" in post_data and len(post_data["claims"]) > 0:
        claim_id = post_data["claims"][0]["claim"]["id"]
        
        _, token2, _ = register_test_user()
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        response = requests.delete(f"{API_URL}/claims/{claim_id}/delete", headers=headers2)
        
        assert response.status_code in (403, 404), "Should not allow deleting other user's claims"
        if response.status_code == 403:
            assert ("permission" in response.text.lower() or 
                   "forbidden" in response.text.lower()), "Error should mention permissions"
    else:
        print("No claims found in the post, skipping other user delete test")

def test_delete_claim_success():
    """Test deleting a claim successfully"""
    _, token, _, _, _, _ = setup_test_environment()
    
    text = "The Earth is round. The Moon orbits the Earth."
    analyze_response = analyze_text(token, text)
    assert analyze_response.status_code == 201, "Should successfully analyze text"
    
    claims_data = analyze_response.json()
    if "results" in claims_data and len(claims_data["results"]) > 0:
        claim_id = claims_data["results"][0]["claim"]["id"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(f"{API_URL}/claims/{claim_id}/delete", headers=headers)
        
        assert response.status_code == 204, (
            f"Should successfully delete the claim. Got: {response.text}"
        )
        
        verify_response = requests.get(f"{API_URL}/claims/{claim_id}/", headers=headers)
        assert verify_response.status_code == 404, "Claim should be deleted"
    else:
        print("No claims found in analysis, skipping claim deletion test")

# -------------------------
# User Claims Tests
# -------------------------

def test_get_user_claims_success():
    """Test getting current user's claims"""
    _, token, _, _, post, _ = setup_test_environment()
    time.sleep(1)  
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/claims/user/claims", headers=headers)
    
    assert response.status_code == 200, "Should return user claims"
    data = response.json()
    
    assert "claims_count" in data, "Response should include claims count"
    assert "claims" in data, "Response should include claims data"
    assert isinstance(data["claims"], list), "Claims should be a list"

def test_get_user_claims_unauthenticated():
    """Test getting user claims without authentication"""
    response = requests.get(f"{API_URL}/claims/user/claims")
    
    assert response.status_code == 401, "Should require authentication"

def cleanup_test_data():
    """Clean up all test data created during tests"""
    print("\nCleaning up claim test data...")
    
    for comment in created_comments:
        try:
            headers = {"Authorization": f"Bearer {comment['token']}"}
            response = requests.delete(f"{API_URL}/comments/{comment['id']}/delete/", 
                                       headers=headers)
            print(f"Deleted comment {comment['id']}: Status {response.status_code}")
        except Exception as e:
            print(f"Error deleting comment {comment['id']}: {e}")
    
    for post in created_posts:
        try:
            headers = {"Authorization": f"Bearer {post['token']}"}
            response = requests.delete(f"{API_URL}/posts/{post['id']}/delete/", headers=headers)
            print(f"Deleted post {post['id']}: Status {response.status_code}")
        except Exception as e:
            print(f"Error deleting post {post['id']}: {e}")
    
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
    
    created_comments.clear()
    created_posts.clear()
    created_channels.clear()
    created_users.clear()

atexit.register(cleanup_test_data)

def test_zzz_cleanup(): # zzz because pytest will run this last then
    """Run cleanup for all created test data"""
    cleanup_test_data()