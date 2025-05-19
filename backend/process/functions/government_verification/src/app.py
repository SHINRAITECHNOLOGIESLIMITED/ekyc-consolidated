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
        "required": ["idNumber"],
        "additionalProperties": False
    }

    try:
        validate(schema=schema,event=data)
        idNumber = data["idNumber"]
        iprs_id_result = govermentValidator.iprs.search_generic(dict(identifier="ID_NUMBER", value=idNumber))
        logger.info(iprs_id_result)


        idnumberVerified = False,"Not processed"
        namesVerified = False,"Not processed"
        dobVerified = False,"Not processed"
        genderVerified = False,"Not processed"

        if "success" in iprs_id_result:
            if iprs_id_result.get("success") and "data" in iprs_id_result:
                iprs_id_result = iprs_id_result.get("data", {})
                #verify
                if 'idNumber' in iprs_id_result:
                    if iprs_id_result.get('idNumber') == data['idNumber']:
                        idnumberVerified = True,"Matched"
                    else:
                        idnumberVerified = False,f"Mismatch - found {iprs_id_result('idNumber')} expected {data['idNumber']}"
                else:
                    idnumberVerified = False,"ID Number field not found in identity service"


                if 'dateOfBirth' in iprs_id_result:
                    try:
                            extracted_dob = iprs_id_result.get('dateOfBirth')
                            if extracted_dob:
                                dobVerified = True, "Matched"
                            else:
                                dobVerified = False, f"Mismatch - {extracted_dob} not found"
                    except Exception as e:
                            dobVerified = False, f"Date parsing failed: {str(e)}"
                else:
                    dobVerified = False,"Date of Birth field not found in the identity service response"

                if 'firstName' in iprs_id_result and 'otherName' in iprs_id_result and 'surname' in iprs_id_result:
                    fullnames = f"{iprs_id_result['firstName']} {iprs_id_result['otherName']} {iprs_id_result['surname']}"
                    if fullnames.upper():
                        namesVerified = True,"Matched"
                    else:
                        namesVerified = False,f"Mismatch -  {fullnames} not found "
                else:
                    namesVerified = False,"FullName field not found in the identity service response"

                if 'gender' in iprs_id_result:
                    if iprs_id_result.get('gender').upper()[0]:
                        genderVerified = True,"Matched"
                    else:
                        genderVerified = False,f"Mismatch - found"
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
            "idNumber": {"type": "string"},
            "fullNames": {"type": "string"},
            "dateOfbirth": {"type": "string", "format": "date"}
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

        id_numberVerified = False,"Not processed"
        passport_numberVerified = False,"Not processed"
        full_namesVerified = False,"Not processed"
        dob_Verified = False,"Not processed"

        if "success" in passport_result:
            if passport_result.get("success") and "data" in passport_result:
                passport_result = passport_result.get("data", {})

                id = passport_result.get('idNumber')
                passportNo = passport_result.get('passportNumber')
                status = "Unknown"

                #verify
                if 'idNumber' in passport_result:
                    if id == data['idNumber']:
                        id_numberVerified = True,"Matched"
                    else:
                        id_numberVerified = False,f"Mismatch - found {id} expected {data['idNumber']}"
                else:
                    id_numberVerified = False,"ID Number field not found in identity service"

                if 'passportNumber' in passport_result:
                    if passportNo == data['passportNumber']:
                        passport_numberVerified = True,"Matched"
                    else:
                        passport_numberVerified = False,f"Mismatch - found {passportNo} expected {data['passportNumber']}"
                else:
                    passport_numberVerified = False,"ID Number field not found in identity service"

                if 'dateOfBirth' in passport_result:
                    try:
                        extracted_dob = datetime.strptime(passport_result.get('dateOfBirth'), "%d.%m.%Y").date()
                        input_dob = datetime.strptime(data['dateOfBirth'], "%Y-%m-%d").date()
                        if extracted_dob == input_dob:
                            dob_Verified = True, "Matched"
                        else:
                            dob_Verified = False, f"Mismatch - found {extracted_dob} expected {input_dob}"
                    except Exception as e:
                            dob_Verified = False, f"Date parsing failed: {str(e)}"
                else:
                    dob_Verified = False,"Date of Birth field not found in the identity service response"

                if 'firstName' in passport_result and 'otherName' in passport_result and 'surname' in passport_result:
                    fullnames = f"{passport_result.get('firstName')} {passport_result('otherName')} {passport_result.get('surname')}"
                    if fullnames:
                        full_namesVerified = True,"Matched"
                    else:
                        full_namesVerified = False,f"Mismatch - found {fullnames} expected {fullnames}"
                else:
                    full_namesVerified = False,"FullName field not found in the identity service response"

                if dob_Verified[0] and id_numberVerified[0] and passport_numberVerified[0] and full_namesVerified[0]:
                    status="Valid"
                else:
                    status="Invalid"
            else:
                logger.error(f"IPRS_PASSPORT Response: {passport_result}")
                passport_numberVerified = False,"Identity Service call  unsuccessfull"
                id_numberVerified = False,"Identity Service call unsuccessfull"
                full_namesVerified = False,"Identity Service call  unsuccessfull"
                dob_Verified = False,"Identity Service call  unsuccessfull"

        else:
            logger.error(f"IPRS_PASSPORT Response: {passport_result}")
            passport_numberVerified = False,"Identity Service call failed"
            id_numberVerified = False,"Identity Service call failed"
            full_namesVerified = False,"Identity Service call failed"
            dob_Verified = False,"Identity Service call failed"
        matchDetails = dict(passport_numberVerified = dict(valid=passport_numberVerified[0],reason=passport_numberVerified[1]),
                        id_numberVerified = dict(valid=id_numberVerified[0],reason=id_numberVerified[1]),
                        full_namesVerified= dict(valid=full_namesVerified[0],reason=full_namesVerified[1]),
                        dateOfbirth = dict(valid=dob_Verified[0],reason=dob_Verified[1]),)
        validation = dict(matchDetails=matchDetails,passport_result=passport_result,status=status)
        return make_response(200, validation)

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
                    "idNo": {"type": "string"},
                    "taxpayerName": {"type": "string"},
                    "pin": {"type": "string"},
                },
                "required": ["idNo", "country"],
                "additionalProperties": False
            }
    try:
        validate(schema=schema,event=data)
        kra_result = govermentValidator.kra.validate_id(dict(
            idNo = data['idNo'],
            country = data['country']
        ))
        logger.info(kra_result)

        taxpayerName_Verified = False,"Not processed"
        pin_Verified = False,"Not processed"

        if "success" in kra_result:
            if kra_result.get("success") and "data" in kra_result:
                kra_result_data = kra_result.get("data", {})

                pin = kra_result_data.get("pin")
                taxpayerName = kra_result_data.get("taxpayerName")

                expected_pin = kra_result_data.get("pin")
                expected_name = kra_result_data.get('taxpayerName')

                if 'pin' in kra_result_data:
                    if pin == expected_pin:
                        pin_Verified = True,"Matched"
                    else:
                        pin_Verified = False,f"Mismatch - found {pin} expected {expected_pin}"
                else:
                    pin_Verified = False,"PIN Number field not found in identity service"

                # verify taxpayerName
                if 'taxpayerName' in kra_result_data:
                    if taxpayerName == expected_name:
                        taxpayerName_Verified = True,"Matched"
                    else:
                        taxpayerName_Verified = False,f"Mismatch - found {taxpayerName} expected {expected_name}"
                else:
                    taxpayerName_Verified = False,"FullName field not found in the identity service response"

                if pin_Verified[0] and taxpayerName_Verified[0]:
                    status="Valid"
                else:
                    status="Invalid"
            else:
                logger.error(f"IPRS_KRA Response: {kra_result}")
                taxpayerName_Verified = False,"Identity Service call unsuccessfull"
                pin_Verified = False,"Identity Service call  unsuccessfull"
        else:
            logger.error(f"IPRS_KRA Response: {kra_result}")
            pin_Verified = False,"Identity Service call failed"
            taxpayerName_Verified = False,"Identity Service call failed"
        matchDetails = dict(pin = dict(valid=pin_Verified[0],reason=pin_Verified[1]),
                        taxpayername = dict(valid=taxpayerName_Verified[0],reason=taxpayerName_Verified[1]))
        validation = dict(matchDetails=matchDetails,kra_result_data=kra_result_data,status=status)
        return make_response(200, validation)

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