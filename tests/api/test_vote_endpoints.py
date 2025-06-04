# # ruff: noqa

# import os
# import unittest.mock as mock
# import uuid

# import pytest
# import requests
# from django.db.models.signals import post_save

# from claims.signals import process_post_fact_checking
# from common.test_utils import disable_fact_checking_signals
# from posts.models import Post


# # More robust patching approach
# @pytest.fixture(autouse=True, scope="module")
# def patch_external_apis():
#     """Patch all external API calls for the entire test module"""
#     # First disconnect the signal handler completely
#     post_save.disconnect(process_post_fact_checking, sender=Post)
    
#     # Then patch all the LLM and Wikipedia related functions
#     with mock.patch('claims.utils.call_llm', return_value="Mocked LLM response"), \
#          mock.patch('claims.utils.extract_claims_from_text', return_value=["Test mock claim"]), \
#          mock.patch('claims.utils.check_claim_with_wikipedia', return_value={
#              "evidence": ["Mock evidence"],
#              "sources": [{
#                  "url": "https://en.wikipedia.org/wiki/Mock",
#                  "title": "Mock - Wikipedia",
#                  "description": "This is a mock Wikipedia result",
#                  "relevance_score": 0.95
#              }]
#          }), \
#          mock.patch('claims.utils.get_verdict_and_summary', return_value={
#              "verdict": "supported", 
#              "summary": "This is a mock summary that supports the claim"
#          }), \
#          mock.patch('claims.signals.claim_service.extract_claims_from_text', return_value=["Test mock claim"]), \
#          mock.patch('claims.signals.claim_service.process_content_for_claims', return_value=["Test mock claim"]), \
#          mock.patch('claims.signals.claim_service.call_llm', return_value="Mocked LLM response"):
        
#         yield
    
#     # Reconnect the signal handler after tests are done
#     post_save.connect(process_post_fact_checking, sender=Post)

# API_URL = os.environ.get('BACKEND_API_URL', 'http://localhost:8000/api/v1')

# # -------------------------
# # Utility Functions
# # -------------------------

# def register_test_user():
#     """Register a new test user and return user data, token, and user_id"""
#     username = f"testuser_{uuid.uuid4().hex[:8]}"
#     user_data = {
#         "username": username,
#         "email": f"{username}@example.com",
#         "password": "TestPassword123!",
#         "password2": "TestPassword123!"
#     }
#     register_response = requests.post(f"{API_URL}/users/register/", json=user_data)
#     assert register_response.status_code == 201, f"User registration failed: {register_response.text}"
    
#     login_data = {
#         "username": user_data["username"],
#         "password": user_data["password"]
#     }
#     login_response = requests.post(f"{API_URL}/users/login/", json=login_data)
#     assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    
#     token = login_response.json()["token"]
#     user_id = register_response.json()["id"]
    
#     return user_data, token, user_id

# def create_test_channel(token):
#     """Create a test channel and return the channel data"""
#     channel_data = {
#         "name": f"Test Channel {uuid.uuid4().hex[:8]}",
#         "description": "A test channel for voting tests",
#         "slug": f"test-channel-{uuid.uuid4().hex[:8]}"
#     }
#     headers = {"Authorization": f"Bearer {token}"}
#     with disable_fact_checking_signals():
#         channel_response = requests.post(f"{API_URL}/channels/", json=channel_data, headers=headers)
#     assert channel_response.status_code == 201, f"Channel creation failed: {channel_response.text}"
#     return channel_response.json()

# def create_test_post(token, channel_id):
#     """Create a test post and return the post data"""
#     headers = {"Authorization": f"Bearer {token}"}
#     post_data = {
#         "title": f"Test Post {uuid.uuid4().hex[:8]}",
#         "content": "This is a test post for voting tests",
#         "channel_id": channel_id
#     }
#     with disable_fact_checking_signals():
#         post_response = requests.post(f"{API_URL}/posts/create/", json=post_data, headers=headers)
#     assert post_response.status_code == 201, f"Post creation failed: {post_response.text}"
#     return post_response.json()

# def create_test_comment(token, post_id):
#     """Create a test comment and return the comment data"""
#     headers = {"Authorization": f"Bearer {token}"}
#     comment_data = {
#         "post_id": post_id,
#         "content": f"Test comment {uuid.uuid4().hex[:8]}"
#     }
#     with disable_fact_checking_signals():
#         comment_response = requests.post(f"{API_URL}/comments/create/", json=comment_data, headers=headers)
#     assert comment_response.status_code == 201, f"Comment creation failed: {comment_response.text}"
#     return comment_response.json()

# def setup_test_objects():
#     """Setup user, channel, post, and comment for testing"""
#     user_data, token, user_id = register_test_user()
#     channel = create_test_channel(token)
#     post = create_test_post(token, channel["id"])
#     comment = create_test_comment(token, post["id"])
#     return user_data, token, user_id, post, comment

# # -------------------------
# # Post Vote Tests
# # -------------------------

# def test_upvote_post_authenticated():
#     """Test upvoting a post as an authenticated user"""
#     user_data, token, user_id, post, _ = setup_test_objects()
    
#     headers = {"Authorization": f"Bearer {token}"}
#     response = requests.post(f"{API_URL}/votes/posts/{post['id']}/upvote/", headers=headers)
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["post_id"] == post["id"]
#     assert data["action"] == "added"
#     assert data["vote_type"] == "upvote"
#     assert data["upvotes"] == 1
#     assert data["downvotes"] == 0
#     assert data["score"] == 1

# def test_upvote_post_unauthenticated():
#     """Test upvoting a post without authentication"""
#     _, _, _, post, _ = setup_test_objects()
    
#     response = requests.post(f"{API_URL}/votes/posts/{post['id']}/upvote/")
    
#     assert response.status_code == 401, "Should require authentication"

# def test_downvote_post_authenticated():
#     """Test downvoting a post as an authenticated user"""
#     user_data, token, user_id, post, _ = setup_test_objects()
    
#     headers = {"Authorization": f"Bearer {token}"}
#     response = requests.post(f"{API_URL}/votes/posts/{post['id']}/downvote/", headers=headers)
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["post_id"] == post["id"]
#     assert data["action"] == "added"
#     assert data["vote_type"] == "downvote"
#     assert data["upvotes"] == 0
#     assert data["downvotes"] == 1
#     assert data["score"] == -1

# def test_upvote_post_toggle():
#     """Test toggling off an upvote by upvoting twice"""
#     user_data, token, user_id, post, _ = setup_test_objects()
#     headers = {"Authorization": f"Bearer {token}"}
    
#     requests.post(f"{API_URL}/votes/posts/{post['id']}/upvote/", headers=headers)
    
#     response = requests.post(f"{API_URL}/votes/posts/{post['id']}/upvote/", headers=headers)
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["action"] == "removed"
#     assert data["upvotes"] == 0

# def test_change_post_vote_type():
#     """Test changing vote from upvote to downvote"""
#     user_data, token, user_id, post, _ = setup_test_objects()
#     headers = {"Authorization": f"Bearer {token}"}
    
#     requests.post(f"{API_URL}/votes/posts/{post['id']}/upvote/", headers=headers)
    
#     response = requests.post(f"{API_URL}/votes/posts/{post['id']}/downvote/", headers=headers)
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["action"] == "changed"
#     assert data["vote_type"] == "downvote"
#     assert data["upvotes"] == 0
#     assert data["downvotes"] == 1

# def test_get_post_votes_authenticated():
#     """Test getting vote counts for a post as an authenticated user"""
#     user_data, token, user_id, post, _ = setup_test_objects()
#     headers = {"Authorization": f"Bearer {token}"}
    
#     requests.post(f"{API_URL}/votes/posts/{post['id']}/upvote/", headers=headers)
    
#     response = requests.get(f"{API_URL}/votes/posts/{post['id']}/votes/", headers=headers)
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["upvotes"] == 1
#     assert data["downvotes"] == 0
#     assert data["score"] == 1
#     assert data["voted"] == True
#     assert data["is_upvote"] == True

# def test_get_post_votes_unauthenticated():
#     """Test getting vote counts for a post without authentication"""
#     user_data, token, user_id, post, _ = setup_test_objects()
#     headers = {"Authorization": f"Bearer {token}"}
    
#     requests.post(f"{API_URL}/votes/posts/{post['id']}/upvote/", headers=headers)
    
#     response = requests.get(f"{API_URL}/votes/posts/{post['id']}/votes/")
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["upvotes"] == 1
#     assert data["downvotes"] == 0
#     assert data["score"] == 1
#     assert "voted" not in data
#     assert "is_upvote" not in data

# def test_nonexistent_post():
#     """Test operations on non-existent post"""
#     user_data, token, user_id, post, _ = setup_test_objects()
#     headers = {"Authorization": f"Bearer {token}"}
    
#     # Simply use the existing post ID + 10000
#     post_id = post["id"] + 10000
#     print(f"Testing with non-existent post ID: {post_id}")
    
#     upvote_response = requests.post(f"{API_URL}/votes/posts/{post_id}/upvote/", headers=headers)
#     assert upvote_response.status_code == 404
    
#     downvote_response = requests.post(f"{API_URL}/votes/posts/{post_id}/downvote/", headers=headers)
#     assert downvote_response.status_code == 404
    
#     votes_response = requests.get(f"{API_URL}/votes/posts/{post_id}/votes/", headers=headers)
#     assert votes_response.status_code == 404

# def test_multiple_users_post_voting():
#     """Test multiple users voting on the same post"""
#     user1_data, token1, user1_id, post, _ = setup_test_objects()
#     headers1 = {"Authorization": f"Bearer {token1}"}
#     requests.post(f"{API_URL}/votes/posts/{post['id']}/upvote/", headers=headers1)
    
#     user2_data, token2, user2_id = register_test_user()
#     headers2 = {"Authorization": f"Bearer {token2}"}
#     requests.post(f"{API_URL}/votes/posts/{post['id']}/downvote/", headers=headers2)
    
#     response = requests.get(f"{API_URL}/votes/posts/{post['id']}/votes/")
#     data = response.json()
    
#     assert data["upvotes"] == 1
#     assert data["downvotes"] == 1
#     assert data["score"] == 0

# # -------------------------
# # Comment Vote Tests
# # -------------------------

# def test_upvote_comment_authenticated():
#     """Test upvoting a comment as an authenticated user"""
#     user_data, token, user_id, _, comment = setup_test_objects()
    
#     headers = {"Authorization": f"Bearer {token}"}
#     response = requests.post(f"{API_URL}/votes/comments/{comment['id']}/upvote/", headers=headers)
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["comment_id"] == comment["id"]
#     assert data["action"] == "added"
#     assert data["vote_type"] == "upvote"
#     assert data["upvotes"] == 1
#     assert data["downvotes"] == 0
#     assert data["score"] == 1

# def test_upvote_comment_unauthenticated():
#     """Test upvoting a comment without authentication"""
#     _, _, _, _, comment = setup_test_objects()
    
#     response = requests.post(f"{API_URL}/votes/comments/{comment['id']}/upvote/")
    
#     assert response.status_code == 401, "Should require authentication"

# def test_downvote_comment_authenticated():
#     """Test downvoting a comment as an authenticated user"""
#     user_data, token, user_id, _, comment = setup_test_objects()
    
#     headers = {"Authorization": f"Bearer {token}"}
#     response = requests.post(f"{API_URL}/votes/comments/{comment['id']}/downvote/", headers=headers)
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["comment_id"] == comment["id"]
#     assert data["action"] == "added"
#     assert data["vote_type"] == "downvote"
#     assert data["upvotes"] == 0
#     assert data["downvotes"] == 1
#     assert data["score"] == -1

# def test_upvote_comment_toggle():
#     """Test toggling off an upvote by upvoting twice"""
#     user_data, token, user_id, _, comment = setup_test_objects()
#     headers = {"Authorization": f"Bearer {token}"}
    
#     requests.post(f"{API_URL}/votes/comments/{comment['id']}/upvote/", headers=headers)
    
#     response = requests.post(f"{API_URL}/votes/comments/{comment['id']}/upvote/", headers=headers)
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["action"] == "removed"
#     assert data["upvotes"] == 0

# def test_change_comment_vote_type():
#     """Test changing vote from upvote to downvote"""
#     user_data, token, user_id, _, comment = setup_test_objects()
#     headers = {"Authorization": f"Bearer {token}"}
    
#     requests.post(f"{API_URL}/votes/comments/{comment['id']}/upvote/", headers=headers)
    
#     response = requests.post(f"{API_URL}/votes/comments/{comment['id']}/downvote/", headers=headers)
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["action"] == "changed"
#     assert data["vote_type"] == "downvote"
#     assert data["upvotes"] == 0
#     assert data["downvotes"] == 1

# def test_get_comment_votes_authenticated():
#     """Test getting vote counts for a comment as an authenticated user"""
#     user_data, token, user_id, _, comment = setup_test_objects()
#     headers = {"Authorization": f"Bearer {token}"}
    
#     requests.post(f"{API_URL}/votes/comments/{comment['id']}/upvote/", headers=headers)
    
#     response = requests.get(f"{API_URL}/votes/comments/{comment['id']}/votes/", headers=headers)
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["upvotes"] == 1
#     assert data["downvotes"] == 0
#     assert data["score"] == 1
#     assert data["voted"] == True
#     assert data["is_upvote"] == True

# def test_get_comment_votes_unauthenticated():
#     """Test getting vote counts for a comment without authentication"""
#     user_data, token, user_id, _, comment = setup_test_objects()
#     headers = {"Authorization": f"Bearer {token}"}
    
#     requests.post(f"{API_URL}/votes/comments/{comment['id']}/upvote/", headers=headers)
    
#     response = requests.get(f"{API_URL}/votes/comments/{comment['id']}/votes/")
    
#     assert response.status_code == 200
#     data = response.json()
#     assert data["upvotes"] == 1
#     assert data["downvotes"] == 0
#     assert data["score"] == 1
#     assert "voted" not in data
#     assert "is_upvote" not in data

# def test_nonexistent_comment():
#     """Test operations on non-existent comment"""
#     user_data, token, user_id, _, comment = setup_test_objects()
#     headers = {"Authorization": f"Bearer {token}"}
    
#     comment_id = comment["id"] + 10000
#     print(f"Testing with non-existent comment ID: {comment_id}")
    
#     upvote_response = requests.post(f"{API_URL}/votes/comments/{comment_id}/upvote/", headers=headers)
#     assert upvote_response.status_code == 404
    
#     downvote_response = requests.post(f"{API_URL}/votes/comments/{comment_id}/downvote/", headers=headers)
#     assert downvote_response.status_code == 404
    
#     votes_response = requests.get(f"{API_URL}/votes/comments/{comment_id}/votes/", headers=headers)
#     assert votes_response.status_code == 404

# def test_multiple_users_comment_voting():
#     """Test multiple users voting on the same comment"""

#     user1_data, token1, user1_id, _, comment = setup_test_objects()
#     headers1 = {"Authorization": f"Bearer {token1}"}
#     requests.post(f"{API_URL}/votes/comments/{comment['id']}/upvote/", headers=headers1)
    
#     user2_data, token2, user2_id = register_test_user()
#     headers2 = {"Authorization": f"Bearer {token2}"}
#     requests.post(f"{API_URL}/votes/comments/{comment['id']}/downvote/", headers=headers2)
    
#     response = requests.get(f"{API_URL}/votes/comments/{comment['id']}/votes/")
#     data = response.json()
    
#     assert data["upvotes"] == 1
#     assert data["downvotes"] == 1
#     assert data["score"] == 0

# # -------------------------
# # Full Flow Tests
# # -------------------------

# def test_full_upvote_flow():
#     """Test the complete flow of creating and upvoting a post"""
#     username = f"testuser_{uuid.uuid4().hex[:8]}"
#     user_data = {
#         "username": username,
#         "email": f"{username}@example.com",
#         "password": "TestPassword123!",
#         "password2": "TestPassword123!" 
#     }
#     register_response = requests.post(f"{API_URL}/users/register/", json=user_data)
#     assert register_response.status_code == 201, f"User registration failed: {register_response.text}"
#     print(f"User registered successfully: {username}")
    
#     login_data = {
#         "username": user_data["username"],
#         "password": user_data["password"]
#     }
#     login_response = requests.post(f"{API_URL}/users/login/", json=login_data)
#     assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    
#     token = login_response.json()["token"]
#     headers = {"Authorization": f"Bearer {token}"}
    
#     channel_data = {
#         "name": f"Test Channel {uuid.uuid4().hex[:8]}",
#         "description": "A test channel for upvote testing",
#         "slug": f"test-channel-{uuid.uuid4().hex[:8]}"
#     }
#     with disable_fact_checking_signals():
#         channel_response = requests.post(f"{API_URL}/channels/", json=channel_data, headers=headers)
#     assert channel_response.status_code == 201, f"Channel creation failed: {channel_response.text}"
#     channel = channel_response.json()
    
#     post_data = {
#         "title": f"Test Post {uuid.uuid4().hex[:8]}",
#         "content": "This is a test post for upvoting",
#         "channel_id": channel["id"]
#     }
#     with disable_fact_checking_signals():
#         post_response = requests.post(f"{API_URL}/posts/create/", json=post_data, headers=headers)
#     assert post_response.status_code == 201, f"Post creation failed: {post_response.text}"
#     post = post_response.json()
#     post_id = post["id"]
#     print(f"Post created successfully with ID: {post_id}")
    
#     upvote_response = requests.post(f"{API_URL}/votes/posts/{post_id}/upvote/", headers=headers)
#     assert upvote_response.status_code == 200, f"Upvote failed: {upvote_response.status_code} - {upvote_response.text}"
#     upvote_data = upvote_response.json()
    
#     assert upvote_data["post_id"] == post_id
#     assert upvote_data["action"] == "added"
#     assert upvote_data["vote_type"] == "upvote"
#     assert upvote_data["upvotes"] == 1
#     assert upvote_data["downvotes"] == 0
#     assert upvote_data["score"] == 1
    
#     votes_response = requests.get(f"{API_URL}/votes/posts/{post_id}/votes/", headers=headers)
#     assert votes_response.status_code == 200
#     votes_data = votes_response.json()
    
#     assert votes_data["upvotes"] == 1
#     assert votes_data["downvotes"] == 0
#     assert votes_data["score"] == 1
#     assert votes_data["voted"] == True
#     assert votes_data["is_upvote"] == True
    
#     print("Upvote test completed successfully")

# def test_full_comment_upvote_flow():
#     """Test the complete flow of creating and upvoting a comment"""
#     username = f"testuser_{uuid.uuid4().hex[:8]}"
#     user_data = {
#         "username": username,
#         "email": f"{username}@example.com",
#         "password": "TestPassword123!",
#         "password2": "TestPassword123!" 
#     }
#     register_response = requests.post(f"{API_URL}/users/register/", json=user_data)
#     assert register_response.status_code == 201, f"User registration failed: {register_response.text}"
#     print(f"User registered successfully: {username}")
    
#     login_data = {
#         "username": user_data["username"],
#         "password": user_data["password"]
#     }
#     login_response = requests.post(f"{API_URL}/users/login/", json=login_data)
#     assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    
#     token = login_response.json()["token"]
#     headers = {"Authorization": f"Bearer {token}"}
    
#     channel_data = {
#         "name": f"Test Channel {uuid.uuid4().hex[:8]}",
#         "description": "A test channel for comment upvoting",
#         "slug": f"test-channel-{uuid.uuid4().hex[:8]}"
#     }
#     with disable_fact_checking_signals():
#         channel_response = requests.post(f"{API_URL}/channels/", json=channel_data, headers=headers)
#     assert channel_response.status_code == 201, f"Channel creation failed: {channel_response.text}"
#     channel = channel_response.json()
    
#     post_data = {
#         "title": f"Test Post {uuid.uuid4().hex[:8]}",
#         "content": "This is a test post for commenting",
#         "channel_id": channel["id"]
#     }
#     with disable_fact_checking_signals():
#         post_response = requests.post(f"{API_URL}/posts/create/", json=post_data, headers=headers)
#     assert post_response.status_code == 201, f"Post creation failed: {post_response.text}"
#     post = post_response.json()
#     post_id = post["id"]
#     print(f"Post created successfully with ID: {post_id}")
    
#     comment_data = {
#         "post_id": post_id,
#         "content": f"Test comment {uuid.uuid4().hex[:8]}"
#     }
#     with disable_fact_checking_signals():
#         comment_response = requests.post(f"{API_URL}/comments/create/", json=comment_data, headers=headers)
#     assert comment_response.status_code == 201, f"Comment creation failed: {comment_response.text}"
#     comment = comment_response.json()
#     comment_id = comment["id"]
#     print(f"Comment created successfully with ID: {comment_id}")
    
#     upvote_response = requests.post(f"{API_URL}/votes/comments/{comment_id}/upvote/", headers=headers)
#     assert upvote_response.status_code == 200, f"Upvote failed: {upvote_response.status_code} - {upvote_response.text}"
#     upvote_data = upvote_response.json()
    
#     assert upvote_data["comment_id"] == comment_id
#     assert upvote_data["action"] == "added"
#     assert upvote_data["vote_type"] == "upvote"
#     assert upvote_data["upvotes"] == 1
#     assert upvote_data["downvotes"] == 0
#     assert upvote_data["score"] == 1
    
#     votes_response = requests.get(f"{API_URL}/votes/comments/{comment_id}/votes/", headers=headers)
#     assert votes_response.status_code == 200
#     votes_data = votes_response.json()
    
#     assert votes_data["upvotes"] == 1
#     assert votes_data["downvotes"] == 0
#     assert votes_data["score"] == 1
#     assert votes_data["voted"] == True
#     assert votes_data["is_upvote"] == True
    
#     print("Comment upvote test completed successfully")