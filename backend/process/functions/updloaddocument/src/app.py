import json


def handler(event, context):
    print(event)
    headers = {
        'Access-Control-Allow-Origin': 'https://main.d2896e60a8d7f8.amplifyapp.com',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    try:
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'Document uploaded successfully'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,  # Important: Include CORS headers even in error responses
            'body': json.dumps({'error': str(e)})
        }
