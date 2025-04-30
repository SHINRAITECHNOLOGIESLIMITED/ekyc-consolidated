import json


def handler(event, context):
    print(event)
    return {
        'statusCode': 400,
        'body': json.dumps({
            'message': 'Not implemented: kra_validate_id_number'
        })
    }
