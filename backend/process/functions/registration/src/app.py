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
                    return make_response(404, {'message': 'Path Not Found', 'error': 'Invalid path'})
        except json.JSONDecodeError:
            logger.error("Error decoding JSON body")
            return make_response(400, {'message': 'Invalid JSON body'})
        except Exception as e:
            logger.error(
                f"An unexpected error occurred in lambda_handler: {e}")
            return make_response(500, {'message': 'Internal Server Error', 'error': str(e)})
    else:
        logger.error(f'Method Not Allowed - received {http_method}')
        return make_response(405, {'message': 'Method Not Allowed', 'error': 'Invalid HTTP method'})


def register_agent(event_data):
    schema = {
        "type": "object",
        "properties": {
            "agentType": {"type": "string"},
            "name": {"type": "string"},
            "pinNumber": {"type": "string"},
            "idNumber": {"type": "string"},
            "gender": {"type": "string"},
            "passportPhotoUrl": {"type": "string"},
            "nationalIdCardUrl": {"type": "string"},
            "companyCertificateUrl": {"type": "string"},
            "dateOfBirth": {"type": "string"},
            "businessNumber": {"type": "string"}
        },
        "required": ["agentType", "name", "pinNumber"],
        "additionalProperties": True
    }
    try:
        validate(schema=schema, event=event_data)
        match event_data["agentType"]:
            case "Individual":
                if not ("idNumber" in event_data):
                    raise Exception(
                        "idNumber should be supplied for Individual")
                if "businessNumber" in event_data:
                    raise Exception(
                        "businessNumber should not be supplied for Individual")
                if not ("gender" in event_data):
                    raise Exception(
                        "gender should be supplied for Individual")
                if not ("passportPhotoUrl" in event_data):
                    raise Exception(
                        "passportPhotoUrl should be supplied for Individual")

                if not ("nationalIdCardUrl" in event_data):
                    raise Exception(
                        "nationalIdCardUrl should be supplied for Individual")
                if "companyCertificateUrl" in event_data:
                    raise Exception(
                        "companyCertificateUrl should not be supplied for Individual")
                if not ("dateOfBirth" in event_data):
                    raise Exception(
                        "dateOfBirth should be supplied for Individual")
            case "Business":
                if not ("businessNumber" in event_data):
                    raise Exception(
                        "businessNumber should be supplied for Business")
                if "idNumber" in event_data:
                    raise Exception(
                        "idNumber should not be supplied for Business")
                if "gender" in event_data:
                    raise Exception(
                        "gender should not be supplied for Business")

                if "passportPhotoUrl" in event_data:
                    raise Exception(
                        "passportPhotoUrl should not be supplied for Business")
                if "nationalIdCardUrl" in event_data:
                    raise Exception(
                        "nationalIdCardUrl should not be supplied for Business")
                if not ("companyCertificateUrl" in event_data):
                    raise Exception(
                        "companyCertificateUrl should be supplied for Business")
                if "dateOfBirth" in event_data:
                    raise Exception(
                        "dateOfBirth should not be supplied for Business")
            case _:
                raise Exception(
                    f"agentType should be either Individual or Business not {event_data['agentType']}")
    except Exception as e:
        logger.error(f"Schema validation failed for Agent: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'error': str(e)})
    try:
        # Call portal to capture agent registration
        event_data["kycStatus"] = "New"
        agent = portal.capture_agent_registration(event_data)
        agentId = agent['agentId']
        event_data['agentId'] = agentId
        logger.info(f"Agent: {agentId} registration process started")
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
        return make_response(500, {'message': 'Error in registering agent', 'error': str(e)})


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
        return make_response(400, {'message': 'Request body validation failed', 'error': str(e)})
    try:
        event_data["kycStatus"] = "New"
        customer = portal.capture_customer_registration(event_data)
        customerId = customer['customerId']
        event_data['customerId'] = customerId
        logger.info(f"Customer: {customerId} registration process started")
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
        return make_response(500, {'message': 'Error in registering customer', 'error': str(e)})


def make_response(status_code, body):
    """
    Helper function to format responses for API Gateway.
    """
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Api-Key, X-Amz-Date, X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': json.dumps(body)
    }
    logger.info(f"Response: {response}")
    return response
