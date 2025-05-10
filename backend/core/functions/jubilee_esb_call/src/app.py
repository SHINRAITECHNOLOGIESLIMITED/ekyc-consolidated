import json
from enum import Enum

from aws_lambda_powertools import Logger, Tracer

from jubilee_esb_api import JubileeESBAPI
from portal import Portal
from utiities import JubileeESBError
from aws_lambda_powertools.utilities.validation import validate

logger = Logger()
tracer = Tracer()
validator = JubileeESBAPI(Portal())


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
                            "extractedData": {
                                "type": "object",
                                "description": "Data extracted from textract",
                                "additionalProperties": True  # Allow any properties in extractedData
                            }
                        },
                        "required": ["s3Path", "documentType", "customerId","invocation_number"],
                        "description": "Event containing document metadata and invocation info"
                    
            }
    validate(event=event, schema=schema)
    assert event['invocation_number']<=10,"Expected validation to be withing first 10 invocations"
    try:
        match Method(event["documentType"]):
            case "KENYAN_NATIONAL_ID":
                idNumber = event["extractedData"]["ID NUMBER"]
                #we make two apis calls to jubilee ESB to check seperates things for KE National ID
                iprs_result = validator.iprs.search_generic(dict(identifier="ID_NUMBER",value = idNumber))
                kra_result = validator.kra.validate_id(dict(country = "KE",idNo = idNumber))
                #merge both results into one
                event["iprs_result"]=dict(iprs_result=iprs_result,kra_result=kra_result)

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
                raise JubileeESBError(f"Document {event['documentType']} is not supported")
        
        event['invocation_number'] += 1
        return  event
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise Exception(e)
