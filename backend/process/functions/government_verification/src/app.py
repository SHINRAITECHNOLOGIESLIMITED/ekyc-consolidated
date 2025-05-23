from datetime import datetime
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
            
            while isinstance(data, str):
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

def process(event_name, api_field_name, event, api_result,is_date_field = False):
    if not event_name in event:
        status = "Not provided"
        details = None
    elif not "data" in api_result:
        status = "Error in API response"
        details = None
    elif not api_field_name in api_result["data"]:
        status = "Not Found"
        details = None
    else:
        expected = api_result['data'][api_field_name]
        actual = event[event_name]
        if is_date_field:
            expected = expected.replace(".","-")
            actual = actual.replace(".","-")
            #convert expected and actual in date objects and check for equality
            # Try different date formats
            date_formats = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d']
            
            expected_date = None
            actual_date = None
            
            # Try to parse expected date
            for fmt in date_formats:
                try:
                    expected_date = datetime.strptime(expected.strip(), fmt).date()
                    break
                except ValueError:
                    continue
            
            # Try to parse actual date
            for fmt in date_formats:
                try:
                    actual_date = datetime.strptime(actual.strip(), fmt).date()
                    break
                except ValueError:
                    continue
            
            if expected_date and actual_date and expected_date == actual_date:
                status = "Matched"
                editdistance = 0
            else:
                status = "Not Matched"
                editdistance = 10
        else:
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
            "serialNumber": {"type": "string"},
            "idNumber": {"type": "string"},
            "fullNames": {"type": "string"},
            "dateOfBirth": {"type": "string", "format": "date"},
            "dateOfIssue": {"type": "string", "format": "date"},
            "gender": {"type": "string", "enum": ["Male", "Female"]},
            "districtOfBirth": {"type": "string"},
        },
        "required": ["idNumber"],
        "additionalProperties": False
    }

    try:
        validate(schema=schema, event=event_data)

        api_result = serviceValidator.iprs.search_generic(dict(identifier="ID_NUMBER", value=event_data['idNumber']))
        
        #construscting fullNames fields         
        firstName = api_result['data']['firstName'] if 'firstName' in api_result['data'] else ''
        otherName = api_result['data']['otherName'] if 'otherName' in api_result['data'] else ''
        surname = api_result['data']['surname'] if 'surname' in api_result['data'] else ''
        
        fullNames = f"{firstName} {otherName} {surname}".replace("  ", " ").strip()
        api_result['data']['fullNames'] = fullNames


        logger.info(api_result)

        serialNumberMatchResult = process(event_name='serialNumber', api_field_name='serialNumber', event=event_data,
                                          api_result=api_result)
        idNumberMatchResult = process(event_name='idNumber', api_field_name='idNumber', event=event_data,
                                      api_result=api_result)
        fullNamesMatchResult = process(event_name='fullNames', api_field_name='firstName, otherName, surname',
                                       event=event_data, api_result=api_result)
        dateOfBirthMatchResult = process(event_name='dateOfBirth', api_field_name='dateOfBirth', event=event_data,
                                         api_result=api_result,is_date_field=True)
        dateOfIssueMatchResult = process(event_name='dateOfIssue', api_field_name='dateOfIssue', event=event_data,
                                         api_result=api_result,is_date_field=True)
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
            "idNumber": {"type": "string"},
            "passportNumber": {"type": "string"},
            "personalNumber": {"type": "string"},
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
        "required": ["passportNumber","idNumber"],
        "additionalProperties": False
    }
    logger.info(event_data)
    try:
        validate(schema=schema, event=event_data)

        api_result = serviceValidator.iprs.search_passport_number(dict(
            identifier="PASSPORT",
            value=event_data["passportNumber"]
            ,idNumber=event_data["idNumber"]),
                                                                  )
        logger.info(api_result)

        documentTypeMatchResult = process(event_name='documentType', api_field_name='documentType', event=event_data,
                                          api_result=api_result)
        countryCodeMatchResult = process(event_name='countryCode', api_field_name='countryCode', event=event_data,
                                         api_result=api_result)
        passportNumberMatchResult = process(event_name='idNumber', api_field_name='idNumber',
                                            event=event_data, api_result=api_result)
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
                                         api_result=api_result,is_date_field=True)
        placeOfBirthMatchResult = process(event_name='placeOfBirth', api_field_name='placeOfBirth', event=event_data,
                                          api_result=api_result)
        dateOfIssueMatchResult = process(event_name='dateOfIssue', api_field_name='dateOfIssue', event=event_data,
                                         api_result=api_result,is_date_field=True)
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
            "taxPayerName": {"type": "string"},
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

        pinMatchResult = process(event_name='pin', api_field_name='pin', event=event_data, api_result=api_result)
        taxPayerNameMatchResult = process(event_name='taxPayerName', api_field_name='taxPayerName', event=event_data,
                                          api_result=api_result)

        matchResults = dict(pin=pinMatchResult,
                            taxPayerName=taxPayerNameMatchResult,
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
