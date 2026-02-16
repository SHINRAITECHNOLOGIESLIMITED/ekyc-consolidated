import json
import os
import time
import io
from collections import defaultdict

import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_xray_sdk.core import xray_recorder
from aws_lambda_powertools.utilities.validation import validate


from portal import Portal

KYCDOCUMENTSBUCKET_NAME = os.environ.get('KYCDOCUMENTSBUCKET_NAME', None)
assert KYCDOCUMENTSBUCKET_NAME is not None, "KYCDOCUMENTSBUCKET_NAME is not set"


logger = Logger()
tracer = Tracer()

textract_client = boto3.client('textract')
s3_client = boto3.client('s3')
portal = Portal()


def _get_kv_map_async(s3_path: str):
    """
    Extract key-value pairs from a document using Textract async API.
    
    Uses StartDocumentAnalysis which supports all PDF formats from S3.
    Polls for completion and returns results.
    
    Args:
        s3_path: S3 key of the document
        
    Returns:
        Tuple of (key_map, value_map, block_map, blocks)
    """
    current_segment = xray_recorder.current_segment()
    trace_id = current_segment.trace_id if current_segment else None
    start_time = time.time() * 1000
    
    # Start async document analysis
    logger.info(f"Starting async Textract analysis for: {s3_path}")
    start_response = textract_client.start_document_analysis(
        DocumentLocation={
            'S3Object': {
                'Bucket': KYCDOCUMENTSBUCKET_NAME,
                'Name': s3_path
            }
        },
        FeatureTypes=["FORMS", "TABLES", "LAYOUT"]
    )
    
    job_id = start_response['JobId']
    logger.info(f"Textract job started: {job_id}")
    
    # Poll for completion
    max_attempts = 30
    poll_interval = 2  # seconds
    
    for attempt in range(max_attempts):
        response = textract_client.get_document_analysis(JobId=job_id)
        status = response['JobStatus']
        
        if status == 'SUCCEEDED':
            logger.info(f"Textract job completed after {attempt + 1} polls")
            break
        elif status == 'FAILED':
            error_msg = response.get('StatusMessage', 'Unknown error')
            logger.error(f"Textract job failed: {error_msg}")
            raise Exception(f"Textract analysis failed: {error_msg}")
        elif status == 'IN_PROGRESS':
            time.sleep(poll_interval)
        else:
            logger.warning(f"Unknown Textract status: {status}")
            time.sleep(poll_interval)
    else:
        raise Exception(f"Textract job timed out after {max_attempts * poll_interval} seconds")
    
    # Collect all blocks (handle pagination)
    blocks = response.get('Blocks', [])
    next_token = response.get('NextToken')
    
    while next_token:
        response = textract_client.get_document_analysis(JobId=job_id, NextToken=next_token)
        blocks.extend(response.get('Blocks', []))
        next_token = response.get('NextToken')
    
    duration_ms = round(time.time() * 1000 - start_time)
    portal.log_api_call(None, api_name="textract", api_method="extract_async", duration_ms=duration_ms,
                        trace_id=trace_id, capture_data=True)
    
    logger.info(f"Textract extracted {len(blocks)} blocks")
    
    # Build key/value maps
    key_map = {}
    value_map = {}
    block_map = {}
    
    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == "KEY_VALUE_SET":
            if 'KEY' in block.get('EntityTypes', []):
                key_map[block_id] = block
            else:
                value_map[block_id] = block
    
    return key_map, value_map, block_map, blocks


def _get_kv_map(s3Path: str):
    """
    Extract key-value pairs from a document using Textract.
    
    For PDFs, uses async API (StartDocumentAnalysis) which supports all formats.
    For images, uses sync API (AnalyzeDocument).
    
    Args:
        s3Path: S3 key of the document
        
    Returns:
        Tuple of (key_map, value_map, block_map, blocks)
    """
    current_segment = xray_recorder.current_segment()
    trace_id = current_segment.trace_id if current_segment else None
    start_time = time.time() * 1000
    
    # Use async API for PDFs (supports all PDF formats)
    if s3Path.lower().endswith('.pdf'):
        return _get_kv_map_async(s3Path)
    
    # Use sync API for images
    try:
        response = textract_client.analyze_document(
            Document={'S3Object': {'Bucket': KYCDOCUMENTSBUCKET_NAME, 'Name': s3Path}},
            FeatureTypes=["FORMS", "TABLES", "LAYOUT"]
        )
    except textract_client.exceptions.UnsupportedDocumentException as e:
        # Fallback to async API if sync fails
        logger.warning(f"Sync Textract failed, trying async: {e}")
        return _get_kv_map_async(s3Path)
    
    duration_ms = round(time.time() * 1000 - start_time)
    portal.log_api_call(None, api_name="textract", api_method="extract", duration_ms=duration_ms,
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
            if 'KEY' in block.get('EntityTypes', []):
                key_map[block_id] = block
            else:
                value_map[block_id] = block

    return key_map, value_map, block_map, blocks
    # with adapter
    # return key_map, value_map, block_map, blocks, response


def _get_text(result, blocks_map):
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


def _get_kv_relationship(key_map, value_map, block_map):
    kvs = defaultdict(list)
    for block_id, key_block in key_map.items():
        value_block = _find_value_block(key_block, value_map)
        key = _get_text(key_block, block_map)
        val = _get_text(value_block, block_map) if value_block else ""
        key_confidence = key_block.get('Confidence', 0)
        value_confidence = value_block.get('Confidence', 0) if value_block else 0
        kvs[key].append({
            'value': val,
            'confidence': (value_confidence + key_confidence)/2
        })
    return kvs

def _extract_query_answers(response):
    answers = {}
    for block in response.get('Blocks', []):
        if block['BlockType'] == 'QUERY':
            alias = block.get('Query', {}).get('Alias')
            answer_block = None
            for rel in block.get('Relationships', []):
                if rel['Type'] == 'ANSWER':
                    answer_block = next((b for b in response['Blocks'] if b['Id'] in rel['Ids']), None)
            if alias and answer_block:
                answers[alias] = {
                    'value': answer_block.get('Text'),
                    'confidence': answer_block.get('Confidence', 0)
                }
    return answers


def _find_value_block(key_block, value_map):
    for relationship in key_block['Relationships']:
        if relationship['Type'] == 'VALUE':
            for value_id in relationship['Ids']:
                value_block = value_map[value_id]
                return value_block
    return None

def _clean_up_label(text_in:str):
    return text_in.replace(":","").replace("'","").replace('"','').replace("  "," ").strip().replace(" ","_").upper()


def _extract_text_phrases(blocks):
    """
    Extract text in phrase form (sentences and paragraphs) from Textract blocks.
    """
    phrases = []
    for block in blocks:
        if block['BlockType'] in ['LINE', 'PARAGRAPH']:
            if 'Text' in block:
                confidence = block.get('Confidence', 0)
                phrases.append({
                    'text': block['Text'],
                    'confidence': confidence
                })
    return phrases


def extract(s3Path: str):
    try:
        #textract
        key_map, value_map, block_map, blocks = _get_kv_map(s3Path)
        
        # append extracted key value pairs to event and pass all parameters along
        extractedForm = _get_kv_relationship(key_map, value_map, block_map)

        #cleaning up
        extractedForm = {_clean_up_label(k):v[0] for k,v in extractedForm.items()}

        # Extract text phrases
        text_phrases = _extract_text_phrases(blocks)
        extractedData = dict(form = extractedForm, phrases = text_phrases)
        
        return extractedData
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise Exception(e)

def query(s3Path: str, queriesConfig, adaptersConfig=None):
    """
    Extract document fields using Textract Queries.
    
    Args:
        s3Path: S3 key of the document
        queriesConfig: Textract queries configuration
        adaptersConfig: Optional adapter configuration (can be None or empty)
    
    Returns:
        Dictionary of query aliases to extracted values with confidence scores
    """
    try:
        current_segment = xray_recorder.current_segment()
        trace_id = current_segment.trace_id if current_segment else None
        start_time = time.time() * 1000
        
        # Build request parameters
        request_params = {
            'Document': {'S3Object': {'Bucket': KYCDOCUMENTSBUCKET_NAME, 'Name': s3Path}},
            'FeatureTypes': ["QUERIES"],
            'QueriesConfig': queriesConfig
        }
        
        # Only include AdaptersConfig if it has adapters
        if adaptersConfig and adaptersConfig.get('Adapters'):
            request_params['AdaptersConfig'] = adaptersConfig
        
        logger.info(f"Textract query request params: {json.dumps(request_params, default=str)}")
        
        response = textract_client.analyze_document(**request_params)
        
        duration_ms = round(time.time() * 1000 - start_time)
        portal.log_api_call(None, api_name="textract", api_method="query", duration_ms=duration_ms,
                            trace_id=trace_id, capture_data=True)
        
        # Log raw response block types for debugging
        block_types = {}
        for block in response.get('Blocks', []):
            bt = block.get('BlockType', 'UNKNOWN')
            block_types[bt] = block_types.get(bt, 0) + 1
        logger.info(f"Textract response block types: {block_types}")
        
        # Log QUERY blocks specifically
        query_blocks = [b for b in response.get('Blocks', []) if b.get('BlockType') == 'QUERY']
        logger.info(f"Found {len(query_blocks)} QUERY blocks")
        for qb in query_blocks:
            alias = qb.get('Query', {}).get('Alias', 'NO_ALIAS')
            has_answer = any(r.get('Type') == 'ANSWER' for r in qb.get('Relationships', []))
            logger.info(f"Query '{alias}': has_answer={has_answer}")
        
        query_answers = _extract_query_answers(response)
        return query_answers
    except Exception as e:
        logger.error(f"Textract query error: {str(e)}")
        raise Exception(e)
