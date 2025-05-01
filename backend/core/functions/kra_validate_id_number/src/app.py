import json

from aws_lambda_powertools import Logger, Tracer

from jubilee_esb_api import JubileeESBError, JubileeESBAPI

logger = Logger()
tracer = Tracer()
validator = JubileeESBAPI()

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    try:
        data = dict(idNo=event["id_number"], country="Kenya")
        kra_result = validator.kra_validate_id(data)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "result": kra_result
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
