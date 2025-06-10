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