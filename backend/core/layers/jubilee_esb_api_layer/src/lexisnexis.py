from typing import Dict, Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate

from utiities import JubileeESBError, JubileeESBUtilities

logger = Logger()
tracer = Tracer()


class LexisNexis:

    def __init__(self, utilities: JubileeESBUtilities):
        self.utilities = utilities

    # LexisNexis Methods
    @tracer.capture_method
    def search_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search LexisNexis records

        Args:
            data: Dictionary containing search parameters
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "reference_id": {"type": "string"},
                    "search_parameters": {"type": "object"}
                },
                "required": ["reference_id", "search_parameters"]
            }
            validate(event=data, schema=schema)

            return self.utilities.make_api_call(
                service="LexisNexis",
                api_method="search",
                url=f"{self.lexisnexis_base_url}/search",
                data=data
            )
        except Exception as e:
            logger.error(f"LexisNexis search failed: {str(e)}")
            raise JubileeESBError(f"LexisNexis search failed: {str(e)}")
