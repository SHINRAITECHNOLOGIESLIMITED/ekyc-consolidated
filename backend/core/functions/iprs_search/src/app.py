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
        iprs_search_result = validator.iprs.search_generic(event)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "result": iprs_search_result
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
