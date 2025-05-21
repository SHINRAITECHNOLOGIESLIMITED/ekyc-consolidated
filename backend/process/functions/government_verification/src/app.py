import json

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate
from aws_lambda_powertools.utilities.validation.exceptions import SchemaValidationError
from fastjsonschema import JsonSchemaException as SchemaValidationError
from jubilee_esb_api import JubileeESBAPI

from portal import Portal

logger = Logger()
tracer = Tracer()
portal = Portal()

serviceValidator = JubileeESBAPI(portal)


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
            # check if data is dict - if its a string convert to dict
            if isinstance(data, str):
                data = json.loads(data)
            logger.info(f"Request Data (body): {data}")

            match path:
                case '/government/nationalid':
                    return verify_nationalid(data)
                case '/government/passport':
                    return verify_passport(data)
                case '/government/krapincertificate':
                    return verify_krapincertificate(data)
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

def levenshtein_distance(s1, s2):
    """Calculate the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def process(event_name, variable_name, event, api_result):
    if event_name in event:
        status = "Not provided"
        details = None
    else:
        expected = api_result['data'][variable_name]
        actual = event[event_name]
        if actual.strip().lower() == expected.strip().lower():
            status = "Matched"
            editdistance = 0
        else:
            status = "Not Matched"
            # calculate edit distance
            editdistance = levenshtein_distance(actual.strip().lower(), expected.strip().lower())
        details = dict(editdistance=editdistance, expected=expected, actual=actual)
    
    return dict(status=status, details=details)


def verify_nationalid(event_data):
    schema = {
        "type": "object",
        "properties": {
            "serialNumber": {"type": "integer"},
            "idNumber": {"type": "integer"},
            "fullNames": {"type": "string"},
            "dateOfBirth": {"type": "string", "format": "date"},
            "dateOfIssue": {"type": "string", "format": "GENDER"},
            "gender": {"type": "string", "format": "date"},
            "districtOfBirth": {"type": "string"},
        },
        "required": ["idNumber"],
        "additionalProperties": False
    }

    try:
        validate(schema=schema, event=event_data)

        api_result = serviceValidator.iprs.search_generic(dict(identifier="ID_NUMBER", value=event_data['idNumber']))
        logger.info(api_result)

        serialNumberMatchResult = process(event_name='serialNumber', api_field_name='serialNumber', event=event_data,
                                          api_result=api_result)
        idNumberMatchResult = process(event_name='idNumber', api_field_name='idNumber', event=event_data,
                                      api_result=api_result)
        fullNamesMatchResult = process(event_name='fullNames', api_field_name='firstName, otherName, surname',
                                       event=event_data, api_result=api_result)
        dateOfBirthMatchResult = process(event_name='dateOfBirth', api_field_name='dateOfBirth', event=event_data,
                                         api_result=api_result)
        dateOfIssueMatchResult = process(event_name='dateOfIssue', api_field_name='dateOfIssue', event=event_data,
                                         api_result=api_result)
        genderMatchResult = process(event_name='gender', api_field_name='gender', event=event_data,
                                    api_result=api_result)
        districtOfBirthMatchResult = process(event_name='districtOfBirth', api_field_name='placeOfBirth',
                                             event=event_data, api_result=api_result)

        matchResults = dict(serialNumber=serialNumberMatchResult,
                            idNumber=idNumberMatchResult,
                            fullNames=fullNamesMatchResult,
                            dateOfBirth=dateOfBirthMatchResult,
                            dateOfIssue=dateOfIssueMatchResult,
                            gender=genderMatchResult,
                            districtOfBirth=districtOfBirthMatchResult,
                            )

        portal.capture_doc_verification(documentType="NationalID", documentIdentifier=event_data['idNumber'],
                                        matchResults=matchResults)
        logger.info(f"Match results: {matchResults}")
        return make_response(200, dict(results=matchResults))
    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for NationalID document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in validate_nationalid: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


def verify_passport(event_data):
    schema = {
        "type": "object",
        "properties": {
            "documentType": {"type": "string"},
            "countryCode": {"type": "string"},
            "passportNumber": {"type": "string"},
            "personalNumber": {"type": "integer"},
            "surname": {"type": "string"},
            "givenNames": {"type": "string"},
            "gender": {"type": "string"},
            "dateOfBirth": {"type": "string", "format": "date"},
            "placeOfBirth": {"type": "string"},
            "dateOfIssue": {"type": "string", "format": "date"},
            "dateOfExpiry": {"type": "string", "format": "date"},
            "nationality": {"type": "string"},
            "issuingAuthority": {"type": "string"},
        },
        "required": ["passportNumber"],
        "additionalProperties": False
    }

    try:
        validate(schema=schema, event=event_data)

        api_result = serviceValidator.iprs.search_passport_number(dict(
            identifier="PASSPORT",
            value=event_data["passportNumber"]))
        logger.info(api_result)

        documentTypeMatchResult = process(event_name='documentType', api_field_name='documentType', event=event_data,
                                          api_result=api_result)
        countryCodeMatchResult = process(event_name='countryCode', api_field_name='countryCode', event=event_data,
                                         api_result=api_result)
        passportNumberMatchResult = process(event_name='passportNumber', api_field_name='passportNumber',
                                            event=event_data, api_result=api_result)
        personalNumberMatchResult = process(event_name='personalNumber', api_field_name='personalNumber',
                                            event=event_data, api_result=api_result)
        surnameMatchResult = process(event_name='surname', api_field_name='surname', event=event_data,
                                     api_result=api_result)
        givenNamesMatchResult = process(event_name='givenNames', api_field_name='givenNames', event=event_data,
                                        api_result=api_result)
        genderMatchResult = process(event_name='gender', api_field_name='gender', event=event_data,
                                    api_result=api_result)
        dateOfBirthMatchResult = process(event_name='dateOfBirth', api_field_name='dateOfBirth', event=event_data,
                                         api_result=api_result)
        placeOfBirthMatchResult = process(event_name='placeOfBirth', api_field_name='placeOfBirth', event=event_data,
                                          api_result=api_result)
        dateOfIssueMatchResult = process(event_name='dateOfIssue', api_field_name='dateOfIssue', event=event_data,
                                         api_result=api_result)
        dateOfExpiryMatchResult = process(event_name='dateOfExpiry', api_field_name='dateOfExpiry', event=event_data,
                                          api_result=api_result)
        nationalityMatchResult = process(event_name='nationality', api_field_name='nationality', event=event_data,
                                         api_result=api_result)
        issuingAuthorityMatchResult = process(event_name='issuingAuthority', api_field_name='issuingAuthority',
                                              event=event_data, api_result=api_result)


        matchResults = dict(documentType=documentTypeMatchResult,
                            countryCode=countryCodeMatchResult,
                            passportNumber=passportNumberMatchResult,
                            personalNumber=personalNumberMatchResult,
                            surname=surnameMatchResult,
                            givenNames=givenNamesMatchResult,
                            gender=genderMatchResult,
                            dateOfBirth=dateOfBirthMatchResult,
                            placeOfBirth=placeOfBirthMatchResult,
                            dateOfIssue=dateOfIssueMatchResult,
                            dateOfExpiry=dateOfExpiryMatchResult,
                            nationality=nationalityMatchResult,
                            issuingAuthority=issuingAuthorityMatchResult,
                            )

        portal.capture_doc_verification(documentType="Passport", documentIdentifier=event_data['passportNumber'],
                                        matchResults=matchResults)
        logger.info(f"Match results: {matchResults}")
        return make_response(200, dict(results=matchResults))
    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for Passport document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in validate_passport: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


def verify_krapincertificate(event_data):
    schema = {
        "type": "object",
        "properties": {
            "pin": {"type": "string"},
            "taxpayerName": {"type": "string"},
        },
        "required": ["pin"],
        "additionalProperties": False
    }

    try:
        validate(schema=schema, event=event_data)

        api_result = serviceValidator.kra.validate_id(dict(
            idNo=event_data['idNo'],
            country=event_data['country']
        ))
        logger.info(api_result)

        pinMatchResult = process(event_name='pin', api_field_name='=B7', event=event_data, api_result=api_result)
        taxpayerNameMatchResult = process(event_name='taxpayerName', api_field_name='=B8', event=event_data,
                                          api_result=api_result)

        matchResults = dict(pin=pinMatchResult,
                            taxpayerName=taxpayerNameMatchResult,
                            )

        portal.capture_doc_verification(documentType="KRAPinCertificate", documentIdentifier=event_data['pin'],
                                        matchResults=matchResults)
        logger.info(f"Match results: {matchResults}")
        return make_response(200, dict(results=matchResults))
    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for KRAPinCertificate document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in validate_krapincertificate: {e}")
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
