import json
from enum import Enum

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate
from aws_lambda_powertools.utilities.validation.exceptions import SchemaValidationError

from jubilee_esb_api import JubileeESBAPI
from portal import Portal
from utiities import JubileeESBError

logger = Logger()
tracer = Tracer()
portal = Portal()
validator = JubileeESBAPI(portal)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    schema = {
                "type": "object",
                "properties": {
                            "s3Path": {
                                "type": "string",
                                "description": "S3 path to the document"
                            },
                            "documentType": {
                                "type": "string",
                                "description": "Type of document being uploaded"
                            },
                            "customerId": {
                                "type": "string",
                                "description": "Customer identifier"
                            },
                            "invocation_number": {
                                "type": "integer",
                                "description": "Invocation level of the event"
                            },
                            "document": {
                                "type": "object",
                                "description": "Document object",
                                "additionalProperties": True  # Allow any properties in document
                            },
                            "extractedData": {
                                "type": "object",
                                "description": "Data extracted from textract",
                                "additionalProperties": True  # Allow any properties in extractedData
                            }
                        },
                        "required": ["s3Path", "documentType", "customerId", "invocation_number"],
                        "description": "Event containing document metadata and invocation info"
            }

    try:
        # Validate the event against the schema
        validate(event=event, schema=schema)

        # Validate invocation number constraint
        if event['invocation_number'] > 2:
            error_msg = "Expected validation to be within first 2 invocations"
            logger.error(error_msg)
            if "document" in event:
                event["document"]["documentStatus"] = "VALIDATION_ERROR: " + error_msg
                portal.update_kyc_document(event["document"])
            raise JubileeESBError(error_msg)

        # Check if extractedData exists
        if "extractedData" not in event:
            error_msg = "Missing extractedData in event"
            logger.error(error_msg)
            if "document" in event:
                event["document"]["documentStatus"] = "VALIDATION_ERROR: " + error_msg
                portal.update_kyc_document(event["document"])
            raise JubileeESBError(error_msg)

        extractedData = event["extractedData"]
        match event["documentType"]:
            case "KENYAN_NATIONAL_ID":
                logger.info("Searching Details for doc:", extractedData)
                # Debug: Log the entire extractedData to see what we're working with
                logger.info(f"Full extractedData content: {json.dumps(extractedData)}")

                if "ID_NUMBER" in extractedData:
                    idNumber = extractedData["ID_NUMBER"]
                    #IPRS Search
                    try:
                        iprs_result = validator.iprs.search_generic(dict(identifier="ID_NUMBER", value=idNumber))
                        event["search_iprs"] = iprs_result
                    except Exception as e:
                        event["search_iprs"] = dict(error=str(e))
                        iprs_result = dict(error=str(e))
                        logger.error(f"Error in IPRS search: {str(e)}")
                    #KRA Search
                    try:
                        kra_result = validator.kra.validate_id(dict(country="KE", idNo=idNumber))
                        event["search_kra"] = kra_result
                    except Exception as e:
                        kra_result = dict(error=str(e))
                        event["search_kra"] = dict(error=str(e))
                        logger.error(f"Error in KRA ID search: {str(e)}")
                    #LexisNexis Search
                    try:
                        firstName = ""
                        middleName = ""
                        lastName = ""
                        gender = "Male"  # Changed from "M" to "Male" to match curl format
                        dob = ""
                        nationalIdentificationNumber = idNumber
                        countryCode = "KEN"
                        entityType = "Individual"
                        sourceName = "Portals"
                        # Debug: Check if FULL_NAMES exists
                        logger.info(f"FULL_NAMES in extractedData: {'FULL_NAMES' in extractedData}")
                        if "FULL_NAMES" in extractedData:
                            full_name = extractedData["FULL_NAMES"].strip()
                            logger.info(f"FULL_NAMES value: {full_name}")
                            names = [name for name in full_name.split(" ") if name]
                            logger.info(f"Parsed names array: {names}")

                            if len(names) == 1:
                                # Only one name provided
                                firstName = names[0]
                                lastName = names[0]  # Use the same name as lastName to satisfy API requirements
                            elif len(names) == 2:
                                # Common case: First and Last name
                                firstName = names[0]
                                lastName = names[1]
                            elif len(names) >= 3:
                                # Case with middle name(s)
                                firstName = names[0]
                                lastName = names[-1]  # Last element as surname
                                middleName = " ".join(names[1:-1])  # Everything in between as middle name

                            logger.info(f"Parsed names: firstName={firstName}, middleName={middleName}, lastName={lastName}")
                        # Get gender if available
                        if "SEX" in extractedData:
                            # Convert single letter gender to full word format
                            gender = extractedData["SEX"]
                        else:
                            gender = "Male"  # Default to Male if not specified
                        # Debug: Check if DATE_OF_BIRTH exists
                        logger.info(f"DATE_OF_BIRTH in extractedData: {'DATE_OF_BIRTH' in extractedData}")
                        if "DATE_OF_BIRTH" in extractedData:
                            #YYYY-MM-DD
                            try:
                                date_split = extractedData["DATE_OF_BIRTH"].replace(" ","").split(".")
                                if len(date_split) > 2:
                                    dob = f"{date_split[2]}-{date_split[1]}-{date_split[0]}"
                            except Exception as e:
                                logger.error(f"Error Extracting date : {str(e)}")
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
                        event["search_lexisnexis"] = lexis_nexis_result

                    except Exception as e:
                        event["search_lexisnexis"] = dict(error=str(e))
                        lexis_nexis_result = dict(error=str(e))
                        logger.error(f"Error NexisLexis search: {str(e)}")

                    event["document"]["documentStatus"] = 'SEARCHED'
                    event["document"]["searchedData"] = json.dumps(dict(iprs = iprs_result,
                                                                        kra = kra_result,
                                                                        lexis_nexis=lexis_nexis_result))
                    portal.update_kyc_document(event["document"])
                    #to be moved to verification lambda
                    event["document"]["documentStatus"] = 'VERIFICATION FAILED'
                    event["document"]["verifiedData"] = json.dumps(dict(error = "Verification not implemented"))
                    portal.update_kyc_document(event["document"])
                else:
                    error_msg = 'ID_NUMBER not found in extracted data'
                    event["document"]["documentStatus"] = 'SEARCH FAILED. Cannot Find "ID_NUMBER"'
                    event["document"]["verifiedData"] = json.dumps(dict(error = "Cannot Find 'ID_NUMBER' field from extracted data"))
                    portal.update_kyc_document(event["document"])
                    raise JubileeESBError(error_msg)

            # case Method.IPRS_PING:
            #     result = validator.iprs.ping()
            # case Method.IPRS_SEARCH_ALIEN_ID:
            #     result = validator.iprs.search_alien_id(event)
            # case Method.IPRS_SEARCH_PASSPORT_NUMBER:
            #     result = validator.iprs.search_passport_number(event)
            # case Method.IPRS_SEARCH_BIRTH_CERTIFICATE_NUMBER:
            #     result = validator.iprs.search_birth_certificate_number(event)
            # case Method.IPRS_SEARCH_DEATH_CERTIFICATE_NUMBER:
            #     result = validator.iprs.search_death_certificate_number(event)
            # case Method.IPRS_SEARCH_BULK:
            #     result = validator.iprs.bulk_iprs_search(event["request_list"])
            # case Method.LEXISNEXIS_SEARCH_RECORD:
            #     result = validator.lexisnexis.search_record(event)
            case _:
                error_msg = f"Document {event['documentType']} is not implemented"
                if "document" in event:
                    event["document"]["documentStatus"] = f'SEARCH FAILED. Document type not implemented {event["documentType"]}'
                    portal.update_kyc_document(event["document"])
                raise JubileeESBError(error_msg)

        event['invocation_number'] += 1
        return event

    except SchemaValidationError as e:
        logger.error(f"Schema validation error: {str(e)}")
        if "document" in event:
            event["document"]["documentStatus"] = f"VALIDATION_ERROR: {str(e)}"
            portal.update_kyc_document(event["document"])
        raise JubileeESBError(f"Schema validation error: {str(e)}")

    except AssertionError as e:
        logger.error(f"Assertion error: {str(e)}")
        if "document" in event:
            event["document"]["documentStatus"] = f"VALIDATION_ERROR: {str(e)}"
            portal.update_kyc_document(event["document"])
        raise JubileeESBError(f"Validation error: {str(e)}")

    except JubileeESBError as e:
        logger.error(f"Jubilee ESB error: {str(e)}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        if "document" in event:
            event["document"]["documentStatus"] = f"ERROR: {str(e)}"
            portal.update_kyc_document(event["document"])
        raise JubileeESBError(f"Error processing document: {str(e)}")
