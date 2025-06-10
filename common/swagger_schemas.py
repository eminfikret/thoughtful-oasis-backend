from drf_yasg import openapi

def error_response(message="An error occurred", example="Error details"):
    """Generate a standard error response schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'error': openapi.Schema(
                type=openapi.TYPE_STRING,
                example=example
            )
        }
    )

def unauthorized_response():
    """401 Unauthorized response schema"""
    return openapi.Response(
        description="Unauthorized - Authentication required",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="Authentication credentials were not provided."
                )
            }
        )
    )

def permission_denied_response(message="You don't have permission to perform this action."):
    """403 Permission Denied response schema"""
    return openapi.Response(
        description="Permission denied",
        schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'detail': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example=message
                )
            }
        )
    )

def not_found_response(example="Not found"):
    """404 Not Found response schema"""
    return openapi.Response(
        description="Not found",
        schema=error_response("Not found", example)
    )

def conflict_response(example="A resource with this name already exists"):
    """409 Conflict response schema"""
    return openapi.Response(
        description="Conflict",
        schema=error_response("Conflict", example)
    )

def pagination_parameters():
    """Common pagination parameters"""
    return [
        openapi.Parameter(
            name="limit",
            in_=openapi.IN_QUERY,
            description="Number of results to return per page",
            type=openapi.TYPE_INTEGER,
            default=10
        ),
        openapi.Parameter(
            name="offset",
            in_=openapi.IN_QUERY,
            description="The initial index from which to return the results",
            type=openapi.TYPE_INTEGER,
            default=0
        )
    ]

def search_parameter():
    """Common search parameter"""
    return openapi.Parameter(
        name="search",
        in_=openapi.IN_QUERY,
        description="A search term for filtering results",
        type=openapi.TYPE_STRING
    )

def channel_example_response():
    """Example channel response"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'name': openapi.Schema(type=openapi.TYPE_STRING, example="Technology"),
            'slug': openapi.Schema(type=openapi.TYPE_STRING, example="technology"),
            'description': openapi.Schema(
                type=openapi.TYPE_STRING, 
                example="Discussion about the latest in technology and innovations"
            ),
            'owner': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                    'username': openapi.Schema(type=openapi.TYPE_STRING, example="admin"),
                    'email': openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="admin@example.com"
                    )
                }
            ),
            'created_at': openapi.Schema(
                type=openapi.TYPE_STRING, 
                format=openapi.FORMAT_DATETIME,
                example="2023-06-10T14:30:45Z"
            ),
            'updated_at': openapi.Schema(
                type=openapi.TYPE_STRING, 
                format=openapi.FORMAT_DATETIME,
                example="2023-06-15T09:12:37Z"
            )
        }
    )

def paginated_response_schema(item_schema):
    """Generate a standard paginated response schema for any item schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'count': openapi.Schema(type=openapi.TYPE_INTEGER, example=15),
            'next': openapi.Schema(
                type=openapi.TYPE_STRING, 
                example="http://api.example.org/items/?offset=10&limit=10",
                nullable=True
            ),
            'previous': openapi.Schema(
                type=openapi.TYPE_STRING, 
                nullable=True,
                example=None
            ),
            'results': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=item_schema
            )
        }
    )

def claim_example_response():
    """Example claim response"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'extracted_claim': openapi.Schema(
                type=openapi.TYPE_STRING, 
                example="The Amazon rainforest produces 20% of the world's oxygen"
            ),
            'claim_index': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'source_type': openapi.Schema(type=openapi.TYPE_STRING, example="raw"),
            'post_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=None, nullable=True),
            'comment_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=None, nullable=True),
            'source_text': openapi.Schema(
                type=openapi.TYPE_STRING, 
                example="The Amazon rainforest produces 20% of the world's oxygen.",
                nullable=True
            ),
            'created_at': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                example="2025-06-10T14:30:45Z"
            )
        }
    )

def source_example():
    """Example fact check source"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'url': openapi.Schema(
                type=openapi.TYPE_STRING,
                example="https://en.wikipedia.org/wiki/Amazon_rainforest"
            ),
            'title': openapi.Schema(type=openapi.TYPE_STRING, example="Amazon rainforest"),
            'description': openapi.Schema(
                type=openapi.TYPE_STRING,
                example="The Amazon rainforest produces approximately 6-9% of the world's oxygen."
            )
        }
    )

def fact_check_example_response():
    """Example fact check response"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'verdict': openapi.Schema(
                type=openapi.TYPE_STRING, 
                enum=["supported", "contradicted", "not_found"],
                example="contradicted"
            ),
            'summary': openapi.Schema(
                type=openapi.TYPE_STRING, 
                example="The claim is contradicted by available evidence." \
                " According to wikipedia, the Amazon rainforest produces approximately 6-9% of the world's oxygen, not 20%."
            ),
            'sources': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=source_example()
            ),
            'created_at': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                example="2025-06-10T14:30:45Z"
            )
        }
    )

def claim_with_fact_check_example():
    """Example claim with fact check response"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'claim': claim_example_response(),
            'fact_check': fact_check_example_response()
        }
    )

def comment_author_schema():
    """Example comment author schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'username': openapi.Schema(type=openapi.TYPE_STRING, example="username123")
        }
    )

def comment_votes_schema():
    """Example comment votes schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'upvotes': openapi.Schema(type=openapi.TYPE_INTEGER, example=5),
            'downvotes': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'score': openapi.Schema(type=openapi.TYPE_INTEGER, example=4),
        }
    )

def comment_example_response():
    """Example comment response schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'content': openapi.Schema(type=openapi.TYPE_STRING, 
                                      example="This is a comment on the post."),
            'post_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=42),
            'author': comment_author_schema(),
            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME,
                                          example="2025-06-10T15:30:45Z"),
            'votes': comment_votes_schema(),
            'parent_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=None, nullable=True),
            'reply_count': openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
            'claims': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_OBJECT),
                example=[
                    {
                        "claim": {
                            "id": 1,
                            "extracted_claim": "The Earth orbits the Sun",
                        },
                        "fact_check": {
                            "verdict": "supported",
                            "summary": "The evidence supports the claim that"
                            " the Earth orbits the Sun.",
                        }
                    }
                ]
            )
        }
    )

def comment_reply_example_response():
    """Example comment reply response schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
            'content': openapi.Schema(type=openapi.TYPE_STRING,
                                       example="This is a reply to the comment."),
            'post_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=42),
            'author': comment_author_schema(),
            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, 
                                         example="2025-06-10T16:15:22Z"),
            'votes': comment_votes_schema(),
            'parent_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'reply_count': openapi.Schema(type=openapi.TYPE_INTEGER, example=0),
            'claims': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_OBJECT),
                example=[]
            )
        }
    )

def comments_paginated_response():
    """Example paginated comments response"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'count': openapi.Schema(type=openapi.TYPE_INTEGER, example=25),
            'next': openapi.Schema(
                type=openapi.TYPE_STRING,
                example="http://api.example.org/comments/user/?user_id=1&offset=10&limit=10",
                nullable=True
            ),
            'previous': openapi.Schema(
                type=openapi.TYPE_STRING,
                example=None,
                nullable=True
            ),
            'results': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=comment_example_response()
            )
        }
    )

def post_author_schema():
    """Example post author schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'username': openapi.Schema(type=openapi.TYPE_STRING, example="user123")
        }
    )

def post_channel_schema():
    """Example post channel schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'name': openapi.Schema(type=openapi.TYPE_STRING, example="Technology")
        }
    )

def post_votes_schema():
    """Example post votes schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'upvotes': openapi.Schema(type=openapi.TYPE_INTEGER, example=15),
            'downvotes': openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
            'score': openapi.Schema(type=openapi.TYPE_INTEGER, example=12),
            'voted': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
            'is_upvote': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True)
        }
    )

def post_example_response():
    """Example post response schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'title': openapi.Schema(type=openapi.TYPE_STRING, example="The Amazon rainforest produces 20% of the world's oxygen."),
            'content': openapi.Schema(
                type=openapi.TYPE_STRING, 
                example="It is a vital part of our ecosystem and plays a crucial role in regulating the Earth's climate."
            ),
            'channel': post_channel_schema(),
            'author': post_author_schema(),
            'created_at': openapi.Schema(
                type=openapi.TYPE_STRING, 
                format=openapi.FORMAT_DATETIME,
                example="2025-06-05T14:30:45Z"
            ),
            'updated_at': openapi.Schema(
                type=openapi.TYPE_STRING, 
                format=openapi.FORMAT_DATETIME,
                example="2025-06-05T14:30:45Z"
            ),
            'votes': post_votes_schema(),
            'comment_count': openapi.Schema(type=openapi.TYPE_INTEGER, example=8),
            'claims': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=claim_with_fact_check_example()
            )
        }
    )

def posts_paginated_response():
    """Example paginated posts response"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'count': openapi.Schema(type=openapi.TYPE_INTEGER, example=42),
            'next': openapi.Schema(
                type=openapi.TYPE_STRING,
                example="http://api.example.org/posts/?offset=10&limit=10",
                nullable=True
            ),
            'previous': openapi.Schema(
                type=openapi.TYPE_STRING,
                example=None,
                nullable=True
            ),
            'results': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=post_example_response()
            )
        }
    )

def user_summary_schema():
    """Example user summary schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'username': openapi.Schema(type=openapi.TYPE_STRING, example="user123"),
            'created_at': openapi.Schema(
                type=openapi.TYPE_STRING, 
                format=openapi.FORMAT_DATETIME,
                example="2025-05-15T10:30:45Z"
            )
        }
    )

def channel_summary_schema():
    """Example channel summary schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'name': openapi.Schema(type=openapi.TYPE_STRING, example="Technology"),
            'created_at': openapi.Schema(
                type=openapi.TYPE_STRING, 
                format=openapi.FORMAT_DATETIME,
                example="2025-05-10T14:30:45Z"
            )
        }
    )

def subscriber_example_schema():
    """Example subscriber schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'subscriber': user_summary_schema(),
            'subscribed_at': openapi.Schema(
                type=openapi.TYPE_STRING, 
                format=openapi.FORMAT_DATETIME,
                example="2025-06-09T16:45:22Z"
            )
        }
    )

def subscription_example_schema():
    """Example subscription schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'channel': channel_summary_schema(),
            'subscribed_at': openapi.Schema(
                type=openapi.TYPE_STRING, 
                format=openapi.FORMAT_DATETIME,
                example="2025-06-09T16:45:22Z"
            )
        }
    )

def subscribers_paginated_response():
    """Example paginated subscribers response"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'count': openapi.Schema(type=openapi.TYPE_INTEGER, example=15),
            'next': openapi.Schema(
                type=openapi.TYPE_STRING,
                example="http://api.example.org/channels/1/subscriptions/?offset=10&limit=10",
                nullable=True
            ),
            'previous': openapi.Schema(
                type=openapi.TYPE_STRING,
                example=None,
                nullable=True
            ),
            'results': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=subscriber_example_schema()
            )
        }
    )

def subscriptions_paginated_response():
    """Example paginated subscriptions response"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'count': openapi.Schema(type=openapi.TYPE_INTEGER, example=8),
            'next': openapi.Schema(
                type=openapi.TYPE_STRING,
                example="http://api.example.org/users/1/subscriptions/?offset=10&limit=10",
                nullable=True
            ),
            'previous': openapi.Schema(
                type=openapi.TYPE_STRING,
                example=None,
                nullable=True
            ),
            'results': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=subscription_example_schema()
            )
        }
    )

def user_profile_schema():
    """Example user profile schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'bio': openapi.Schema(type=openapi.TYPE_STRING, example="Software engineer with 5 years of experience in Python"),
            'profile_picture': openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/media/profile_pictures/avatar.jpg", nullable=True),
            'website': openapi.Schema(type=openapi.TYPE_STRING, example="https://example.com", nullable=True),
            'reputation': openapi.Schema(type=openapi.TYPE_INTEGER, example=42),
            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, example="2025-05-10T14:30:45Z"),
            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, example="2025-05-15T09:45:12Z")
        }
    )

def user_detail_schema():
    """Example user detail schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'username': openapi.Schema(type=openapi.TYPE_STRING, example="user123"),
            'email': openapi.Schema(type=openapi.TYPE_STRING, example="user123@example.com"),
            'first_name': openapi.Schema(type=openapi.TYPE_STRING, example="John"),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING, example="Doe"),
            'profile': user_profile_schema(),
            'date_joined': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, example="2025-05-10T14:30:45Z"),
            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True)
        }
    )

def login_response_schema():
    """Example login response schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'user': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                    'username': openapi.Schema(type=openapi.TYPE_STRING, example="user123"),
                    'email': openapi.Schema(type=openapi.TYPE_STRING, example="user123@example.com"),
                    'first_name': openapi.Schema(type=openapi.TYPE_STRING, example="John"),
                    'last_name': openapi.Schema(type=openapi.TYPE_STRING, example="Doe"),
                    'profile': user_profile_schema()
                }
            ),
            'token': openapi.Schema(type=openapi.TYPE_STRING, example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."),
            'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        }
    )

def register_response_schema():
    """Example register response schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
            'username': openapi.Schema(type=openapi.TYPE_STRING, example="user123"),
            'email': openapi.Schema(type=openapi.TYPE_STRING, example="user123@example.com"),
            'first_name': openapi.Schema(type=openapi.TYPE_STRING, example="John"),
            'last_name': openapi.Schema(type=openapi.TYPE_STRING, example="Doe")
        }
    )

def username_email_check_schema():
    """Example username/email check response schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username_exists': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
            'email_exists': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False)
        }
    )

def token_refresh_schema():
    """Example token refresh response schema"""
    return openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'access_token': openapi.Schema(type=openapi.TYPE_STRING, example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        }
    )