import json
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate
from aws_lambda_powertools.utilities.validation.exceptions import SchemaValidationError
from jubilee_esb_api import JubileeESBAPI
from portal import Portal
import datetime
from fastjsonschema import JsonSchemaException as SchemaValidationError
from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()
portal = Portal()

govermentValidator = JubileeESBAPI(portal)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    """
    Lambda handler for government verification endpoints (IPRS).
    Handles POST requests to various /government/* paths.
    Routes requests to specific handlers which perform schema validation.
    """
    # logger.info(f"Received event: {json.dumps(event)}")

    http_method = event.get('httpMethod')
    path = event.get('path')

    if http_method == 'POST':
        try:
            data = event.get('body', {})
            #check if data is dict - if its a string convert to dict
            if isinstance(data, str):
                data = json.loads(data)
            logger.info(f"Request Data (body): {data}")
            

            match path:
                case '/government/nationalid-verification':
                    return handle_nationalid_verification(data)
                case '/government/passport-verification':
                    return handle_passport_verification(data)
                case '/government/kra-verification':
                    return handle_kra_verification(data)
                case _:
                    return make_response(404, {'message': 'Path Not Found'})

        except json.JSONDecodeError:
            logger.error("Error decoding JSON body")
            return make_response(400, {'message': 'Invalid JSON body'})
        except Exception as e:
            logger.error(f"An unexpected error occurred in lambda_handler: {e}")
            return make_response(500, {'message': 'Internal Server Error'})
    else:
        logger.error(f'Method Not Allowed - received {http_method}')
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
            "dateOfBirth": {"type": "string", "format": "date"},
            "gender": {"type": "string"},
        },
        "required": ["idNumber", "fullNames", "dateOfBirth","gender"],
        "additionalProperties": False
    }

    try:
        validate(schema=schema,event=data)
        idNumber = data["idNumber"]
        iprs_id_result = govermentValidator.iprs.search_generic(dict(identifier="idNumber", value=idNumber))
        logger.info(iprs_id_result)
        
        
        idnumberVerified = False,"Not processed"
        namesVerified = False,"Not processed"
        dobVerified = False,"Not processed"
        genderVerified = False,"Not processed"
        """
            Example of IPRS Result
                {
            "success": true,
            "status": {
                "code": 200,
                "message": "OK"
            },
            "details": "Request was successful",
            "data": {
                "errorOccurred": false,
                "isFingerprintNil": null,
                "isPhotoNil": null,
                "isSignatureNil": "null",
                "dateOfDeath": "",
                "otherName": "BIKO",
                "surname": "NYAMAI",
                "occupation": null,
                "ethnicGroup": "",
                "dateOfBirth": "2/19/1984 12:00:00 AM",
                "placeOfLive": "",
                "pin": "null",
                "placeOfDeath": "null",
                "placeOfBirth": "NAIROBI\nDISTRICT - STAREHE\n\n",
                "serialNumber": "229769449",
                "clan": "",
                "firstName": "STEPHEN",
                "idNumber": "23224868",
                "citizenship": "Kenyan",
                "gender": "M",
                "dateOfIssue": "10/24/2011 12:00:00 AM",
                "regOffice": "null"
             },
            "pagination": null,
            "error": null
        }
        """
        if "success" in iprs_id_result:
            if iprs_id_result["success"] and "data" in iprs_id_result:
                iprs_id_result = iprs_id_result["data"]
                #verify
                if 'idNumber' in iprs_id_result:
                    if iprs_id_result['idNumber'] == data['idNumber']:
                        idnumberVerified = True,"Matched"
                    else:
                        idnumberVerified = False,f"Mismatch - found {iprs_id_result['idNumber']} expected {data['idNumber']}"
                else:
                    idnumberVerified = False,"ID Number field not found in identity service"


                if 'dateOfBirth' in iprs_id_result:
                    try:
                            extracted_dob = datetime.strptime(iprs_id_result['dateOfBirth'], "%d.%m.%Y").date()
                            input_dob = datetime.strptime(data['dateOfBirth'], "%Y-%m-%d").date()
                            if extracted_dob == input_dob:
                                dobVerified = True, "Matched"
                            else:
                                dobVerified = False, f"Mismatch - found {extracted_dob} expected {input_dob}"
                    except Exception as e:
                            dobVerified = False, f"Date parsing failed: {str(e)}"
                else:
                    dobVerified = False,"Date of Birth field not found in the identity service response"

                if 'firstName' in iprs_id_result and 'otherName' in iprs_id_result and 'surname' in iprs_id_result:
                    fullnames = f"{iprs_id_result['firstName']} {iprs_id_result['otherName']} {iprs_id_result['surname']}"
                    if fullnames.upper() == data['fullNames'].upper():
                        namesVerified = True,"Matched"
                    else:
                        namesVerified = False,f"Mismatch - found {fullnames} expected {data['fullNames'] }"
                else:
                    namesVerified = False,"FullName field not found in the identity service response"

                if 'gender' in iprs_id_result:
                    if iprs_id_result['gender'].upper()[0] == data['gender'].upper()[0]:
                        genderVerified = True,"Matched"
                    else:
                        genderVerified = False,f"Mismatch - found {iprs_id_result['gender'][0]} expected {data['gender'][0]}"
                else:
                    genderVerified = False,"SEX field not found in the identity service response"
                
                
                
                if dobVerified[0] and idnumberVerified[0] and namesVerified[0] and genderVerified[0]:
                    status="Valid"
                else:
                    status="Invalid"
            else:
                logger.error(f"IPRS Response: {iprs_id_result}")
                idnumberVerified = False,"Identity Service call unsuccessfull"
                namesVerified = False,"Identity Service call  unsuccessfull"
                dobVerified = False,"Identity Service call  unsuccessfull"
                genderVerified = False,"Identity Service call  unsuccessfull"
        else:
            logger.error(f"IPRS Response: {iprs_id_result}")
            idnumberVerified = False,"Identity Service call failed"
            namesVerified = False,"Identity Service call failed"
            dobVerified = False,"Identity Service call failed"
            genderVerified = False,"Identity Service call failed"
        matchDetails = dict(idNumber = dict(valid=idnumberVerified[0],reason=idnumberVerified[1]),
                          names = dict(valid=namesVerified[0],reason=namesVerified[1]),
                          dob = dict(valid=dobVerified[0],reason=dobVerified[1]),)
        validation = dict(matchDetails=matchDetails,iprs_id_result=iprs_id_result,status=status)
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
            "idNumber": {"type": "string"}
        },
        "required": ["passportNumber", "idNumber"],
        "additionalProperties": False
    }

    try:
        validate(schema=schema,event=data)
        idNumber = data["idNumber"]
        passport_result = govermentValidator.iprs.search_passport_number(dict(
            identifier = "PASSPORT",
            value = data["passportNumber"],
            idNumber = idNumber
        ))
        logger.info(passport_result)

        return make_response(200, passport_result)

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
                    "country": {
                        "type": "string",
                        "enum": ["COMP", "KE", "NKE", "NKENR"],
                        "description": "COMP: Non-Individual – Company, KE: Individual - Kenyan Citizen, NKE: Individual – Non-Kenyan Resident, NKENR: Individual – Non-Kenyan Non-Resident"
                    },
                    "idNo": {
                        "type": "string",
                        "minLength": 1
                    }
                },
                "required": ["idNo", "country"]
            }

    try:
        validate(schema=schema,event=data)
        idNo = data['idNo']
        country = data['country']
        kra_result = govermentValidator.iprs.validate_id(dict(
            identifier = "KRA",
            value = idNo,
            country = country
        ))
        logger.info(kra_result)

        return make_response(200, kra_result)

    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for KRA verification: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in handle_kra_verification: {e}")
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