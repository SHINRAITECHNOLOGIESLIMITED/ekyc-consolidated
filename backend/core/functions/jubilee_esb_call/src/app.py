import json
from enum import Enum

from aws_lambda_powertools import Logger, Tracer

from jubilee_esb_api import JubileeESBAPI
from portal import Portal
from utiities import JubileeESBError

logger = Logger()
tracer = Tracer()
validator = JubileeESBAPI(Portal())


class Method(Enum):
    IPRS_SEARCH_GENERIC = "iprs_search_generic"
    IPRS_PING = "iprs_ping"
    IPRS_SEARCH_ALIEN_ID = "iprs_search_alien_id"
    IPRS_SEARCH_PASSPORT_NUMBER = "iprs_search_passport_number"
    IPRS_SEARCH_BIRTH_CERTIFICATE_NUMBER = "iprs_search_birth_certificate_number"
    IPRS_SEARCH_DEATH_CERTIFICATE_NUMBER = "iprs_search_death_certificate_number"
    IPRS_SEARCH_BULK = "iprs_search_bulk"
    LEXISNEXIS_SEARCH_RECORD = "lexisnexis_search_record"
    KRA_VALIDATE_ID = "kra_validate_id"


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    try:
        logger.info(f"Received event: {event}")
        assert "method" in event, "Method key is not part of payload"
        match Method(event["method"]):
            case Method.IPRS_SEARCH_GENERIC:
                result = validator.iprs.search_generic(event)
            case Method.IPRS_PING:
                result = validator.iprs.ping()
            case Method.IPRS_SEARCH_ALIEN_ID:
                result = validator.iprs.search_alien_id(event)
            case Method.IPRS_SEARCH_PASSPORT_NUMBER:
                result = validator.iprs.search_passport_number(event)
            case Method.IPRS_SEARCH_BIRTH_CERTIFICATE_NUMBER:
                result = validator.iprs.search_birth_certificate_number(event)
            case Method.IPRS_SEARCH_DEATH_CERTIFICATE_NUMBER:
                result = validator.iprs.search_death_certificate_number(event)
            case Method.IPRS_SEARCH_BULK:
                result = validator.iprs.bulk_iprs_search(event["request_list"])
            case Method.LEXISNEXIS_SEARCH_RECORD:
                result = validator.lexisnexis.search_record(event)
            case Method.KRA_VALIDATE_ID:
                result = validator.kra.validate_id(event)
            case _:
                raise JubileeESBError(f"Method {event['method']} is not supported")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "result": result
            })
        }

    except JubileeESBError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"})
        }
