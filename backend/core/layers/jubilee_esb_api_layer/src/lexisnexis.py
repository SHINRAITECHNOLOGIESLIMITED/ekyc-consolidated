from typing import Dict, Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate

from utiities import JubileeESBError, JubileeESBUtilities

logger = Logger()
tracer = Tracer()


class LexisNexis:

    def __init__(self, utilities: JubileeESBUtilities):
        self.utilities = utilities
        self.business = utilities.business

    # LexisNexis Methods
    @tracer.capture_method
    def search_record(self, data) -> Dict:
        """
        Search LexisNexis records
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "firstName": {"type": "string"},
                    "middleName": {"type": "string"},
                    "lastName": {"type": "string"},
                    "gender": {"type": "string"},
                    "dob": {"type": "string"},
                    "nationalIdentificationNumber": {"type": "string"},
                    "countryCode": {"type": "string"},
                    "entityType": {"type": "string"},
                    "sourceName": {"type": "string"},
                },
                "required": ["firstName", "lastName", "gender", "dob", "countryCode", "entityType", "sourceName"]
            }
            validate(event=data, schema=schema)

            return self.utilities.make_api_call(
                "LexisNexis",
                api_method="lexis_nexis",
                url=f"/lexis/search/{self.business}",
                data=data,
                is_post=True
            )
        except Exception as e:
            logger.error(f"LexisNexis search failed: {str(e)}")
            raise JubileeESBError(f"LexisNexis search failed: {str(e)}")
