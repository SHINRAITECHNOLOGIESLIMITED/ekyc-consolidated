import json
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate
from aws_lambda_powertools.utilities.validation.exceptions import SchemaValidationError
from jubilee_esb_api import JubileeESBAPI
from portal import Portal

from portal import Portal
logger = Logger()
tracer = Tracer()
portal = Portal()

validator = JubileeESBAPI(portal)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    """
    Lambda handler perfomating background checks against lexis nexis.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    http_method = event.get('httpMethod')
    
    if http_method == 'POST':
        try:
            data = json.loads(event.get('body', '{}'))
            return handle_background_check(data)
        except json.JSONDecodeError:
            logger.error("Error decoding JSON body")
            return make_response(400, {'message': 'Invalid JSON body'})
        except Exception as e:
            logger.error(f"An unexpected error occurred in lambda_handler: {e}")
            return make_response(500, {'message': 'Internal Server Error'})
    else:
        logger.error('Method Not Allowed - received {http_method}')
        return make_response(405, {'message': 'Method Not Allowed'})

def handle_background_check(data):
    """
    Validates schema.
    """
    schema = {
        "type": "object",
        "properties": {
            "firstName": {"type": "string"},
            "middleName": {"type": "string"},
            "lastName": {"type": "string"},
            "gender": {"type": "string"},
            "dateOfBirth": {"type": "string", "format": "date"},
            "nationalIdentificationNumber": {"type": "string"}
        },
        "required": ["firstName", "lastName","gender", "dateOfBirth","nationalIdentificationNumber"],
        "additionalProperties": False
    }
    
    try:
        validate(schema=schema,event=data)
        
        firstName = data["firstName"]
        if "middleName" in data:
            middleName = data["middleName"]
        else:
            middleName = ""
        lastName = data["lastName"]
        gender = data["gender"]
        dob = data["dateOfBirth"]
        nationalIdentificationNumber = data["nationalIdentificationNumber"]
        countryCode = "KEN"
        entityType = "Individual"
        sourceName = "Portals"
        
        lexis_nexis_input = dict(firstName=firstName,
                                                middleName=middleName,
                                                lastName=lastName,
                                                gender=gender,
                                                dob=dob,
                                                nationalIdentificationNumber=nationalIdentificationNumber,
                                                countryCode=countryCode,
                                                entityType=entityType,
                                                sourceName=sourceName)

        lexis_nexis_result = validator.lexisnexis.search_record(lexis_nexis_input)                        
        logger.info(lexis_nexis_result)
        
        return make_response(200, lexis_nexis_result)

    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for background check: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred while checking background check: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


def make_response(status_code, body):
    """
    Helper function to format responses for API Gateway.
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }
