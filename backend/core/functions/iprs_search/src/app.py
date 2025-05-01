import json


def handler(event, context):
    print(event)
    return {
        'statusCode': 400,
        'body': json.dumps({
            'message': 'Not implemented: iprs_search'
        })
    }
