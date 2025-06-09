from datetime import datetime
import json

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate
from jubilee_esb_api import JubileeESBAPI

from portal import Portal,DOCUMENT_TYPE

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
                case '/government/nationalid':
                    return verify_nationalid(data)
                case '/government/passport':
                    return verify_passport(data)
                case '/government/kra':
                    return verify_taxpayerinfo(data)
                case _:
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

            # Normalize dates by removing midnight time component
            if " 12:00:00 AM" in expected:
                expected = expected.replace(" 12:00:00 AM", "")
            if " 12:00:00 AM" in actual:
                actual = actual.replace(" 12:00:00 AM", "")

            # Try different date formats
            date_formats = [
                '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d', # Standard formats
                '%m/%d/%Y', '%Y/%d/%m',  # US format and year-day-month format
                '%d %b %Y', '%d %B %Y',  # 18 May 1987, 18 MAY 1987
                '%Y-%b-%d', '%Y-%B-%d',  # 1987-May-18
                '%d- %m- %Y',  # 19- 02- 1984
                '%m-%d-%Y',   # 12-24-2009
            ]

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

def rate(matchResults):
    validation_accuracy=0.0
    if len(matchResults) == 0:
        pass
    else:
        passed = 0
        failed = 0
        mapping_issue = 0
        for field,result in matchResults.items():
            if 'status' in result:
                if result['status'] == 'Matched':
                    passed += 1
                elif result['status'] == "Not Matched":
                    failed += 1
                elif result['status'] == "Not Found":
                    mapping_issue +=1
        if failed + passed == 0:
            validation_accuracy = 0.0
        else:
            validation_accuracy = passed / (passed + failed) * 100

        if failed + passed + mapping_issue == 0:
            processing_accuracy = 0.0
        else:
            processing_accuracy = (passed + failed)/(failed + passed + mapping_issue) * 100
    return validation_accuracy,processing_accuracy


def verify_nationalid(event_data):
    schema = {
        "type": "object",
        "properties": {
            "serialNumber": {"type": "string"},
            "idNumber": {"type": "string"},
            "fullNames": {"type": "string"},
            "dateOfBirth": {"type": "string"},
            "dateOfIssue": {"type": "string"},
            "gender": {"type": "string"},
            "districtOfBirth": {"type": "string"},
        },
        "required": ["idNumber"],
        "additionalProperties": False
    }

    try:
        validate(schema=schema, event=event_data)
    except Exception as e:
        logger.error(f"Schema validation failed for NationalID: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})

    try:
        response = serviceValidator.iprs.search_generic(dict(identifier="ID_NUMBER", value=event_data['idNumber']))
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
                    return make_response(400, {'message': api_result['error'], 'details': api_result})
            if "success" in api_result:
                if api_result["success"] == False:
                    return make_response(400, {'message': 'Call was not successfull', 'details': api_result['details']})
            if 'data' in api_result:
                # Constructing fullNames field with uppercase letters
                firstName = api_result['data']['firstName'] if 'firstName' in api_result['data'] else ''
                otherName = api_result['data']['otherName'] if 'otherName' in api_result['data'] else ''
                surname = api_result['data']['surname'] if 'surname' in api_result['data'] else ''

                fullNames = f"{firstName} {otherName} {surname}".replace("  ", " ").strip().upper()
                api_result['data']['fullNames'] = fullNames


                logger.info(api_result)

                serialNumberMatchResult = process(event_name='serialNumber', api_field_name='serialNumber', event=event_data,
                                                api_result=api_result)
                idNumberMatchResult = process(event_name='idNumber', api_field_name='idNumber', event=event_data,
                                            api_result=api_result)
                fullNamesMatchResult = process(event_name='fullNames', api_field_name='fullNames',
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
                _documentType=DOCUMENT_TYPE.NATIONAL_ID
                _documentIdentifier=event_data['idNumber']

                validation_accuracy,processing_accuracy = rate(matchResults)

                portal.capture_doc_verification(documentType=_documentType,
                                                documentIdentifier=_documentIdentifier,
                                                matchResults=matchResults,
                                                validation_accuracy=validation_accuracy,
                                                processing_accuracy=processing_accuracy)

                return make_response(200, dict(results=matchResults))
            else:
                return make_response(400, {'message': 'Missing \'data\' field in returned data', 'details': api_result})
    except Exception as e:
        logger.error(f"National Id verfification failed: {e}")
        return make_response(500, {'message': 'Passport verfification failed','details': str(e)})


def verify_passport(event_data):
    schema = {
        "type": "object",
        "properties": {
            "idNumber": {"type": "string"},
            "passportNumber": {"type": "string"},
            "firstName": {"type": "string"},
            "otherName": {"type": "string"},
            "surname": {"type": "string"},
            "gender": {"type": "string"},
            "dateOfBirth": {"type": "string"},
            "dateOfIssue": {"type": "string"},
            "dateOfExpiry": {"type": "string"},
        },
        "required": ["passportNumber","idNumber"],
        "additionalProperties": False
    }
    logger.info(event_data)
    try:
        validate(schema=schema, event=event_data)
    except Exception as e:
        logger.error(f"Schema validation failed for Passport: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})

    try:
        response = serviceValidator.iprs.search_passport_number(dict(
                identifier="PASSPORT",
                value=event_data["passportNumber"],
                idNumber=event_data["idNumber"])
            )
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
                    return make_response(400, {'message': api_result['error'], 'details': api_result})

            if "success" in api_result:
                if api_result["success"] == False:
                    return make_response(400, {'message': 'Call was not successfull', 'details': api_result['details']})

            if "data" in api_result and isinstance(api_result["data"], dict) and api_result["data"]:
                passportNumberMatchResult = process(event_name='passportNumber', api_field_name='passportNumber',
                                                    event=event_data, api_result=api_result)
                surnameMatchResult = process(event_name='surname', api_field_name='surname', event=event_data,
                                            api_result=api_result)
                firstNameMatchResult = process(event_name='firstName', api_field_name='firstName', event=event_data,
                                                api_result=api_result)
                otherNameMatchResult = process(event_name='otherName', api_field_name='otherName', event=event_data,
                                                api_result=api_result)
                genderMatchResult = process(event_name='gender', api_field_name='gender', event=event_data,
                                            api_result=api_result)
                dateOfBirthMatchResult = process(event_name='dateOfBirth', api_field_name='dateOfBirth', event=event_data,
                                                api_result=api_result,is_date_field=True)
                dateOfIssueMatchResult = process(event_name='dateOfIssue', api_field_name='dateOfIssue', event=event_data,
                                                api_result=api_result,is_date_field=True)
                dateOfExpiryMatchResult = process(event_name='dateOfExpiry', api_field_name='dateOfExpiry', event=event_data,
                                                api_result=api_result, is_date_field=True)

                matchResults = dict(
                                    passportNumber=passportNumberMatchResult,
                                    surname=surnameMatchResult,
                                    firstName=firstNameMatchResult,
                                    otherName=otherNameMatchResult,
                                    gender=genderMatchResult,
                                    dateOfBirth=dateOfBirthMatchResult,
                                    dateOfIssue=dateOfIssueMatchResult,
                                    dateOfExpiry=dateOfExpiryMatchResult
                                    )

                _documentType=DOCUMENT_TYPE.PASSPORT
                _documentIdentifier=event_data['passportNumber']

                validation_accuracy,processing_accuracy = rate(matchResults)

                portal.capture_doc_verification(documentType=_documentType,
                                                documentIdentifier=_documentIdentifier,
                                                matchResults=matchResults,
                                                validation_accuracy=validation_accuracy,
                                                processing_accuracy=processing_accuracy)

                logger.info(f"Match results: {matchResults}")
                return make_response(200, dict(results=matchResults))
            else:
                return make_response(400, {'message': 'Missing \'data\' field in returned data', 'details': api_result})
    except Exception as e:
        error_message = str(e)
        logger.error(f"Passport verfification failed: {error_message}")
        return make_response(500, {'message': 'Passport verfification failed','details': error_message})


def verify_taxpayerinfo(event_data):
    schema = {
        "type": "object",
        "properties": {
            "pin": {"type": "string"},
            "taxPayerName": {"type": "string"},
            "idNumber" : {"type": "string"}
        },
        "required": ["idNumber"],
        "additionalProperties": False
    }

    try:
        validate(schema=schema, event=event_data)
    except Exception as e:
        logger.error(f"Schema validation failed for KRA Pin: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})

    """
    Following are the options for the typeOfTaxpayer parameter:
        COMP: Non-Individual – Company
        KE: Individual - Kenyan Citizen
        NKE: Individual – Non-Kenyan Resident
        NKENR: Individual – Non-Kenyan Non-Resident
    """
    try:
        response = serviceValidator.kra.validate_id(dict(
            idNo=event_data['idNumber'],
            country='KE' #Individual - Kenyan Citizen
        ))
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
                    return make_response(400, {'message': api_result['error'], 'details': api_result})
            if "success" in api_result:
                if api_result["success"] == False:
                    return make_response(400, {'message': 'Call was not successfull', 'details': api_result['details']})
            if "data" in api_result:
                if "responseCode" in api_result["data"]:
                    match api_result["data"]["responseCode"]:
                        case "30000":
                            #Valid ID
                            pinMatchResult = process(event_name='pin', api_field_name='pin', event=event_data, api_result=api_result)
                            taxPayerNameMatchResult = process(event_name='taxPayerName', api_field_name='taxpayerName', event=event_data,
                                                            api_result=api_result)

                            matchResults = dict(pin=pinMatchResult,
                                                taxPayerName=taxPayerNameMatchResult,
                                                )

                            _documentType=DOCUMENT_TYPE.KRA_PIN_CERTIFICATE
                            _documentIdentifier=event_data['pin']

                            validation_accuracy,processing_accuracy = rate(matchResults)

                            portal.capture_doc_verification(documentType=_documentType,
                                                            documentIdentifier=_documentIdentifier,
                                                            matchResults=matchResults,
                                                            validation_accuracy=validation_accuracy,
                                                            processing_accuracy=processing_accuracy)

                            logger.info(f"Match results: {matchResults}")
                            return make_response(200, dict(results=matchResults))
                        case "30001":
                            #NOK Invalid User ID or Password
                            return make_response(400, {'message': 'Invalid User ID or Password', 'details': api_result})
                        case "30002":
                            #NOK Invalid ID
                            return make_response(400, {'message': 'Invalid ID', 'details': api_result})
                        case "30003":
                            #NOK iPage not Done
                            return make_response(400, {'message': 'iPage not Done', 'details': api_result})
                        case _:
                            return make_response(400, {'message': f'Unknown respsonse code {api_result["data"]["responseCode"]}', 'details': api_result})
                else:
                    return make_response(400, {'message': 'Missing response code in returned data', 'details': api_result['data']})
            else:
                return make_response(400, {'message': 'Missing \'data\' field in returned data', 'details': api_result})
    except Exception as e:
        logger.error(f"KRA ID validation failed: {str(e)}")
        return make_response(500, {'message': 'Error: KRA ID validation failed', 'details': str(e)})


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
