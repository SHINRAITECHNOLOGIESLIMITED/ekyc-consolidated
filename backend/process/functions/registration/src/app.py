import json
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate
import os
import boto3
from portal import Portal

CUSTOMERREGISTRATIONSM_ARN = os.environ.get('CUSTOMERREGISTRATIONSM_ARN', None)
assert CUSTOMERREGISTRATIONSM_ARN is not None, "CUSTOMERREGISTRATIONSM_ARN is not set"

AGENTREGISTRATIONSM_ARN = os.environ.get('AGENTREGISTRATIONSM_ARN', None)
assert AGENTREGISTRATIONSM_ARN is not None, "AGENTREGISTRATIONSM_ARN is not set"

logger = Logger()
tracer = Tracer()
portal = Portal()
sfn_client = boto3.client('stepfunctions')

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):

    logger.info(f"Received event: {json.dumps(event)}")

    http_method = event.get('httpMethod')
    path = event.get('path')
    if http_method == 'POST':
        try:
            data = event.get('body', {})

            while isinstance(data, str):
                data = json.loads(data)
            logger.info(f"Request Data (body): {data}")

            match path:
                case '/agent-registration':
                    return register_agent(data)
                case '/customer-registration':
                    return register_customer(data)
                case _:
                    logger.error(f"Path Not Found: {path}")
                    return make_response(404, {'message': 'Path Not Found'})

        except json.JSONDecodeError:
            logger.error("Error decoding JSON body")
            return make_response(400, {'message': 'Invalid JSON body'})
        except Exception as e:
            logger.error(f"An unexpected error occurred in lambda_handler: {e}")
            return make_response(500, {'message': 'Internal Server Error', 'details': str(e)})
    else:
        logger.error(f'Method Not Allowed - received {http_method}')
        return make_response(405, {'message': 'Method Not Allowed'})

def register_agent(event_data):
    schema = {
        "type": "object",
        "properties": {
            "agentType": {"type": "string"},
            "name": {"type": "string"},
            "pinNumber": {"type": "string"},
            "idNumber": {"type": "string"},
            "passportPhotoUrl": {"type": "string"},
            "nationalIdCardUrl": {"type": "string"},
            "companyCertificateUrl": {"type": "string"},
            "dateOfBirth": {"type": "string"},
            "businessNumber": {"type": "string"}
        },
        "required": ["agentType", "name", "pinNumber", "passportPhotoUrl"],
        "additionalProperties": True
    }

    try:
        validate(schema=schema, event=event_data)
        if not("idNumber" in event_data or "businessNumber" in event_data):
            logger.error(f"Schema validation failed for Agent: {e}")
            return make_response(400, {'message': 'Request body validation failed either idNumber or businessNumber should be supplied', 'details': str(e)})    
    except Exception as e:
        logger.error(f"Schema validation failed for Agent: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    try:    
        # Call portal to capture agent registration
        event_data["kycStatus"] = "New"
        portal.capture_agent_registration(event_data)
        
        # Launch the step-function to execute the process
        sfn_response = sfn_client.start_execution(
            stateMachineArn=AGENTREGISTRATIONSM_ARN,
            input=json.dumps(event_data)
        )
        
        return make_response(200, {
            'message': 'Agent registration accepted',
            'executionArn': sfn_response['executionArn']
        })
    except Exception as e:
        logger.error(f"Error in registering agent: {e}")
        return make_response(500, {'message': 'Error in registering agent', 'details': str(e)})
    
                
def register_customer(event_data):
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "pinNumber": {"type": "string"},
            "idNumber": {"type": "string"},
            "passportNumber": {"type": "string"},
            "gender": {"type": "string"},
            "dateOfBirth": {"type": "string"},
            "passportPhotoUrl": {"type": "string"},
            "nationalIdCardUrl": {"type": "string"},
            "passportUrl": {"type": "string"},
            "kraPinCardUrl": {"type": "string"}
        },
        "required": ["name", "pinNumber", "idNumber", "gender", "dateOfBirth", "passportPhotoUrl", 
                    "nationalIdCardUrl", "kraPinCardUrl"],
        "additionalProperties": True
    }

    try:
        validate(schema=schema, event=event_data)
    except Exception as e:
        logger.error(f"Schema validation failed for Customer: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    try:    
        event_data["kycStatus"] = "New"
        portal.capture_customer_registration(event_data)
        
        # Launch the step-function to execute the process
        sfn_client = boto3.client('stepfunctions')
        sfn_response = sfn_client.start_execution(
            stateMachineArn=CUSTOMERREGISTRATIONSM_ARN,
            input=json.dumps(event_data)
        )
        
        return make_response(200, {
            'message': 'Customer registration accepted',
            'executionArn': sfn_response['executionArn']
        })
    except Exception as e:
        logger.error(f"Error in registering customer: {e}")
        return make_response(500, {'message': 'Error in registering customer', 'details': str(e)})
    
                
def make_response(status_code, body):
    """
    Helper function to format responses for API Gateway.
    """
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }
    logger.info(f"Response: {response}")
    return response
