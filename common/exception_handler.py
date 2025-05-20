from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):

    response = exception_handler(exc, context)
    
    if response is not None:

        new_data = {}
        

        if isinstance(response.data, dict) and 'detail' in response.data:
            new_data['error'] = response.data['detail']

            for key, value in response.data.items():
                if key != 'detail':
                    new_data[key] = value

        elif not isinstance(response.data, dict):
            new_data['error'] = response.data

        else:
            new_data = response.data
            
        response.data = new_data
    
    return response