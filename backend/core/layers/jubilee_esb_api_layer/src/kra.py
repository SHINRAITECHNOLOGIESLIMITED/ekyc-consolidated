from typing import Dict, Any, List

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate

from utiities import JubileeESBError, JubileeESBUtilities

logger = Logger()
tracer = Tracer()


class KRA:

    def __init__(self, utilities: JubileeESBUtilities):
        self.utilities = utilities

    # KRA Methods
    @tracer.capture_method
    def validate_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        This interface validates an id number.

        Args:
            data: Dictionary containing ID number and country
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "country": {"type": "string"},
                    "idNo": {"type": "string"}
                },
                "required": ["idNo", "country"]
            }
            validate(event=data, schema=schema)
            idNo = data['idNo']
            country = data['country']
            return self._make_api_call(
                "KRA",
                f"/api/v1/kra/validate-id?typeOfTaxpayer={country}&taxpayerID={idNo}",
                None,
                is_post=False
            )
        except Exception as e:
            logger.error(f"KRA ID validation failed: {str(e)}")
            raise JubileeESBError(f"KRA ID validation failed: {str(e)}")