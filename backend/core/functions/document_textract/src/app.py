import json
import os
import time
from collections import defaultdict

import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_xray_sdk.core import xray_recorder
from aws_lambda_powertools.utilities.validation import validate

from portal import Portal

KYCDOCUMENTSBUCKET_NAME = os.environ.get('KYCDOCUMENTSBUCKET_NAME', None)
assert KYCDOCUMENTSBUCKET_NAME is not None, "KYCDOCUMENTSBUCKET_NAME is not set"

PORTAL_GRAPHQL_SECRET_ARN = os.getenv('PORTAL_GRAPHQL_SECRET_ARN', None)
assert PORTAL_GRAPHQL_SECRET_ARN, "PORTAL_GRAPHQL_SECRET_ARN environment variable is not set"

logger = Logger()
tracer = Tracer()

client = boto3.client('textract')
lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')
portal = Portal()


def get_kv_map(s3Path):
    current_segment = xray_recorder.current_segment()
    trace_id = current_segment.trace_id if current_segment else None
    start_time = time.time() * 1000
    response = client.analyze_document(
        Document={'S3Object': {'Bucket': KYCDOCUMENTSBUCKET_NAME, 'Name': s3Path}},
        FeatureTypes=["FORMS"]
    )
    duration_ms = round(time.time() * 1000 - start_time)
    portal.log_api_call(response, api_name="textract", api_method="analyze_document", duration_ms=duration_ms,
                        trace_id=trace_id, capture_data=True)

    # Get the text blocks
    blocks = response['Blocks']

    # get key and value maps
    key_map = {}
    value_map = {}
    block_map = {}
    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == "KEY_VALUE_SET":
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
            else:
                value_map[block_id] = block

    return key_map, value_map, block_map


def get_text(result, blocks_map):
    text = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        text += word['Text'] + ' '
                    if word['BlockType'] == 'SELECTION_ELEMENT':
                        if word['SelectionStatus'] == 'SELECTED':
                            text += 'X '

    return text.strip()


def get_kv_relationship(key_map, value_map, block_map):
    kvs = defaultdict(list)
    for block_id, key_block in key_map.items():
        value_block = find_value_block(key_block, value_map)
        key = get_text(key_block, block_map)
        val = get_text(value_block, block_map)
        kvs[key].append(val)
    return kvs


def find_value_block(key_block, value_map):
    for relationship in key_block['Relationships']:
        if relationship['Type'] == 'VALUE':
            for value_id in relationship['Ids']:
                value_block = value_map[value_id]
                return value_block
    return None

def clean_up_label(text_in:str):
    return text_in.replace(":","").replace("'","").replace('"','').replace("  "," ").strip().replace(" ","_").upper()
    
@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    schema = {
                "type": "object",
                "properties": {
                            "s3Path": {
                                "type": "string",
                                "description": "S3 path to the document"
                            },
                            "documentType": {
                                "type": "string",
                                "description": "Type of document being uploaded"
                            },
                            "customerId": {
                                "type": "string",
                                "description": "Customer identifier"
                            },
                            "invocation_number": {
                                "type": "integer",
                                "description": "Invocation level of the event"
                            }
                        },
                        "required": ["s3Path", "documentType", "customerId","invocation_number"],
                        "description": "Event containing document metadata and invocation info"
                    
            }
    validate(event=event, schema=schema)
    assert event['invocation_number']==0,"Expected textract to be the first invocation"
    try:
        s3Path = event['s3Path']
        
        #textract
        key_map, value_map, block_map = get_kv_map(s3Path)

        # append extracted key value pairs to event and pass all parameters along
        extractedData = get_kv_relationship(key_map, value_map, block_map)
        extractedData = {clean_up_label(k):v[0] for k,v in extractedData.items()}
        event['extractedData'] = extractedData
        event["document"]["documentStatus"] = 'EXTRACTED'
        event["document"]["extractedData"] = json.dumps(extractedData)
        portal.update_kyc_document(event["document"])
        logger.info(f"Extracted key value pairs")
        event['invocation_number'] += 1
        return event
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise Exception(e)
