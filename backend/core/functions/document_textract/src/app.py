import json

from text_extract import TextractProcessor

def handler(event, context):
    processor = TextractProcessor()

    # Get document details from the event
    try:
        bucket = event.get('bucket')
        key = event.get('key')
        doc_type = event.get('documentType')

        if not all([bucket, key, doc_type]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'Missing required parameters: bucket, key, or documentType'
                })
            }

        # Process the document
        result = processor.process_document(bucket, key, doc_type)

        if result:
            return {
                'statusCode': 200,
                'body': json.dumps(result)
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'Failed to process document'
                })
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Error: {str(e)}'
            })
        }

