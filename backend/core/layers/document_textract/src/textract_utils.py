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


logger = Logger()
tracer = Tracer()

textract_client = boto3.client('textract')
portal = Portal()


def _get_kv_map(s3Path):
    current_segment = xray_recorder.current_segment()
    trace_id = current_segment.trace_id if current_segment else None
    start_time = time.time() * 1000
    response = textract_client.analyze_document(
        Document={'S3Object': {'Bucket': KYCDOCUMENTSBUCKET_NAME, 'Name': s3Path}},
        FeatureTypes=["FORMS","TABLES", "LAYOUT"]
    )
    duration_ms = round(time.time() * 1000 - start_time)
    portal.log_api_call(None, api_name="textract", api_method="analyze_document", duration_ms=duration_ms,
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

def query(s3Path: str,queriesConfig,adaptersConfig):
    try:
        response = textract_client.analyze_document(
            Document={'S3Object': {'Bucket': KYCDOCUMENTSBUCKET_NAME, 'Name': s3Path}},
            FeatureTypes=["QUERIES"], 
            QueriesConfig=queriesConfig,
            AdaptersConfig=adaptersConfig
        )
        query_answers = _extract_query_answers(response)
        return query_answers
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise Exception(e)
