from typing import Dict, Any

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
                    "country": {
                        "type": "string",
                        "enum": ["COMP", "KE", "NKE", "NKENR"],
                        "description": "COMP: Non-Individual – Company, KE: Individual - Kenyan Citizen, NKE: Individual – Non-Kenyan Resident, NKENR: Individual – Non-Kenyan Non-Resident"
                    },
                    "idNo": {
                        "type": "string",
                        "minLength": 1
                    }
                },
                "required": ["idNo", "country"]
            }
            validate(event=data, schema=schema)
        except Exception as e:
            logger.error(f"Verification schema failed: {str(e)}")
            logger.error(data)
            raise JubileeESBError(f"Verification schema failed: {str(e)}")
        
        try:
            idNo = data['idNo']
            country = data['country']

            return self.utilities.make_api_call(
                "KRA",
                api_method="validate_id",
                url=f"/api/v1/kra/validate-id?typeOfTaxpayer={country}&taxpayerID={idNo}",
                data={},
                is_post=False
            )
        except Exception as e:
            logger.error(f"KRA ID validation failed: {str(e)}")
            raise JubileeESBError(f"KRA ID validation failed: {str(e)}")
