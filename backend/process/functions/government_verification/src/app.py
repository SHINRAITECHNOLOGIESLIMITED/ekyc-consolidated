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

govermentValidator = JubileeESBAPI(portal)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context):
    """
    Lambda handler for government verification endpoints (IPRS).
    Handles POST requests to various /government/* paths.
    Routes requests to specific handlers which perform schema validation.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    http_method = event.get('httpMethod')
    path = event.get('path')

    if http_method == 'POST':
        try:
            data = json.loads(event.get('body', '{}'))
            
            match path:
                case '/government/nationalid-verification':
                    return handle_nationalid_verification(data)
                case '/government/passport-verification':
                    return handle_passport_verification(data)
                case '/government/kra-verification':
                    return handle_kra_verification(data)
                case '/government/company-verification':
                    return handle_company_verification(data)
                case _:
                    return make_response(404, {'message': 'Path Not Found'})

        except json.JSONDecodeError:
            logger.error("Error decoding JSON body")
            return make_response(400, {'message': 'Invalid JSON body'})
        except Exception as e:
            logger.error(f"An unexpected error occurred in lambda_handler: {e}")
            return make_response(500, {'message': 'Internal Server Error'})
    else:
        logger.error('Method Not Allowed - received {http_method}')
        return make_response(405, {'message': 'Method Not Allowed'})

def handle_nationalid_verification(data):
    """
    Validates schema and indicates not implemented for National ID verification.
    """
    schema = {
        "type": "object",
        "properties": {
            "idNumber": {"type": "string"},
            "fullNames": {"type": "string"},
            "dateOfBirth": {"type": "string", "format": "date"}
        },
        "required": ["idNumber", "fullNames", "dateOfBirth"],
        "additionalProperties": False
    }
    
    try:
        validate(schema=schema,event=data)
        idNumber = data["idNumber"]
        iprs_result = govermentValidator.iprs.search_generic(dict(identifier="ID_NUMBER", value=idNumber))
        logger.info(iprs_result)
        
        
        idNumberValid = False,"Not processed"
        namesValid = False,"Not processed"
        dobValid = False,"Not processed"
        
        
        #check if id number was found
        if "error" in iprs_result: #TODO: Rewrite according to actual behaviour of IPRS
            idNumberValid = False,"Error calling Identity Services"
        elif "missing" in iprs_result: #TODO: Rewrite according to actual behaviour of IPRS
            idNumberValid = False,"ID Number not found"
        else:
            idNumberValid = True,"Exists"
            
        #Effie to continue
        
        
        if dobValid[0] and idNumberValid[0] and namesValid[0]:
            status="Valid"
        else:
            status="Invalid"
        matchDetails = dict(idNumber = dict(valid=idNumberValid[0],reason=idNumberValid[1]),
                          names = dict(valid=namesValid[0],reason=namesValid[1]),
                          dob = dict(valid=dobValid[0],reason=dobValid[1]),)
        validation = dict(matchDetails=matchDetails,extractedData=iprs_result,status=status)
        return make_response(200, validation)

    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for National ID verification: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in handle_nationalid_verification: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


def handle_passport_verification(data):
    """
    Validates schema (defined inline and locally) and indicates not implemented for Passport verification.
    """
    schema = {
        "type": "object",
        "properties": {
            "passportNumber": {"type": "string"},
            "fullNames": {"type": "string"},
            "dateOfBirth": {"type": "string", "format": "date"}
        },
        "required": ["passportNumber", "fullNames", "dateOfBirth"],
        "additionalProperties": False
    }
    
    try:
        validate(schema=schema,event=data)
        
        # --- Business Logic Placeholder ---
        # Call external ESB service for Passport verification, process response, etc.
        # --- End Business Logic Placeholder ---

        return make_response(501, {'message': 'Passport verification endpoint not implemented'})

    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for Passport verification: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in handle_passport_verification: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


def handle_kra_verification(data):
    """
    Validates schema (defined inline and locally) and indicates not implemented for KRA verification.
    """
    schema = {
        "type": "object",
        "properties": {
            "kraPin": {"type": "string"},
            "fullNames": {"type": "string"},
            "idNumber": {"type": "string"} # Could be National ID or Passport number
        },
        "required": ["kraPin", "fullNames", "idNumber"],
        "additionalProperties": False
    }
    
    try:
        validate(schema=schema,event=data)
        
        # --- Business Logic Placeholder ---
        # Call external ESB service for KRA verification, process response, etc.
        # --- End Business Logic Placeholder ---

        return make_response(501, {'message': 'KRA verification endpoint not implemented'})

    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for KRA verification: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in handle_kra_verification: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


def handle_company_verification(data):
    """
    Validates schema (defined inline and locally) and indicates not implemented for Company verification.
    """
    schema = {
        "type": "object",
        "properties": {
            "businessNumber": {"type": "string"},
            "fullNames": {"type": "string"} # Maps to Registered Company Name
        },
        "required": ["businessNumber", "fullNames"],
        "additionalProperties": False
    }
    
    try:
        validate(schema=schema,event=data)
        
        # --- Business Logic Placeholder ---
        # Call external ESB service for Company verification, process response, etc.
        # --- End Business Logic Placeholder ---

        return make_response(501, {'message': 'Company verification endpoint not implemented'})

    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for Company verification: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in handle_company_verification: {e}")
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
