import json
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate
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
            
            data = event.get('body', {})
            # check if data is dict - if its a string convert to dict
            while isinstance(data, str):
                data = json.loads(data)
            logger.info(f"Request Data (body): {data}")
            
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
    except Exception as e:
        logger.error(f"Schema validation failed for background check: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'error': str(e)})
    
    try:
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
        
        response = validator.lexisnexis.search_record(lexis_nexis_input)
        if response.status_code >= 500:
            logger.error(f"Received status code: {response.status_code}: {response.json()}")
            return make_response(response.status_code, response.json)
        elif response.status_code >= 400:
            logger.warning(f"Received status code: {response.status_code}: {response.json()}")
            return make_response(response.status_code, response.json)
        else:
            api_result = response.json()
            logger.info(api_result)
            if "error" in api_result:
                if api_result["error"]:
                    return make_response(400, {'message': api_result['error'], 'error': api_result})
            if "success" in api_result:
                if api_result["success"] == False:
                    return make_response(400, {'message': 'Call was not successfull', 'error': api_result['details']})
            if 'data' in api_result:
                lexis_nexis_input['result'] = api_result['data']
                portal.capture_background_check(lexis_nexis_input)
                api_result['data']["message"] = "Background check completed successfully"
                return make_response(200, api_result['data'])
            else:
                return make_response(400, {'message': 'Missing \'data\' field in returned data', 'error': api_result})
    except Exception as e:
        logger.error(f"Error occurred while checking background check (LexisNexis): {e}")
        return make_response(500, {'message': 'LexisNexis backgroundcheck failed', 'error': str(e)})

def make_response(status_code, body):
    """
    Helper function to format responses for API Gateway.
    """
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': 'https://main.d2896e60a8d7f8.amplifyapp.com',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Api-Key, X-Amz-Date, X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': json.dumps(body)
    }
    logger.info(f"Response: {response}")
    return response