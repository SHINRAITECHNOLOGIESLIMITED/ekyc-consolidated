import json

from aws_lambda_powertools import Logger, Tracer

from jubilee_esb_api import JubileeESBAPI
from utiities import JubileeESBError

logger = Logger()
tracer = Tracer()
validator = JubileeESBAPI()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    try:
        logger.info(f"Received event: {event}")
        assert "method" in event, "Method key is not part of payload"

        match event["method"]:
            case "search_generic":
                result = validator.iprs.search_generic(event)

            case "ping":
                result = validator.iprs.ping()

            case "search_alien_id":
                result = validator.iprs.search_alien_id(event)

            case "search_passport_number":
                result = validator.iprs.search_passport_number(event)

            case "search_birth_certificate_number":
                result = validator.iprs.search_birth_certificate_number(event)

            case "search_death_certificate_number":
                result = validator.iprs.search_death_certificate_number(event)

            case "bulk_iprs_search":
                result = validator.iprs.bulk_iprs_search(event["request_list"])


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
