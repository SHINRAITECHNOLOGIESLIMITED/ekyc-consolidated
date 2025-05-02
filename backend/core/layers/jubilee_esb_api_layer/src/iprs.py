from typing import Dict, Any, List

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate

from utiities import JubileeESBError, JubileeESBUtilities

logger = Logger()
tracer = Tracer()


class IPRS:

    def __init__(self, utilities: JubileeESBUtilities):
        self.utilities = utilities
        self.business = utilities.business

    # search Interface
    @tracer.capture_method
    def search_generic(self, data) -> Dict:
        """
        Generic IPRS searches for an individual in the system.(Sec 5-6)
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "identifier": {"type": "string"},
                    "value": {"type": "string"}
                },
                "required": ["identifier", "value"]
            }
            validate(event=data, schema=schema)
            return self.utilities.make_api_call(
                "IPRS",
                api_method="searchV2",
                url=f"/iprs/searchV2/{self.business}",
                data=data,
                is_post=True
            )

        except Exception as e:
            logger.error(f"IPRS search failed: {str(e)}")
            raise JubileeESBError(f"IPRS search failed: {str(e)}")


   # ping IPRS Interface
    @tracer.capture_method
    def ping(self) -> Dict:
        """Check IPRS service availability. (Sec 7-8) """
        try:
            return self.utilities.make_api_call(
                "IPRS",
                api_method="ping",
                url=f"/iprs/pingIprs/{self.business}",
                data={},
                is_post=True
            )

        except Exception as e:
            logger.error(f"IPRS ping failed: {str(e)}")
            raise JubileeESBError(f"IPRS ping failed: {str(e)}")


   # search Alien ID Interface
    @tracer.capture_method
    def search_alien_id(self, data) -> Dict:
        """
        searches for an individual in the system based on the alien id.(Sec 9-10)
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "identifier": {"type": "string"},
                    "value": {"type": "string"}
                },

                "required": ["identifier", "value"]
            }
            validate(event=data, schema=schema)
            return self.utilities._make_api_call(
                "IPRS",
                api_method="search_alien_id",
                url=f"/iprs/searchUsingAlienId/{self.business}",
                data=data,
                is_post=True
            )

        except Exception as e:
            logger.error(f"IPRS alien ID search failed: {str(e)}")
            raise JubileeESBError(f"IPRS alien ID search failed: {str(e)}")


    # search Passport Number Interface
    @tracer.capture_method
    def search_passport_number(self, data) -> Dict:
        """
        searches for an individual in the system based on the passport number.(Sec 10-12)
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "identifier": {"type": "string"},
                    "value": {"type": "string"},
                    "idNumber": {"type": "string"}
                },

                "required": ["identifier", "value", "idNumber"]
            }
            validate(event=data, schema=schema)
            return self.utilities._make_api_call(
                "IPRS",
                api_method="search_passport_number",
                url=f"/iprs/searchUsingPassportNumber/{self.business}",
                data=data,
                is_post=True
            )

        except Exception as e:
            logger.error(f"IPRS passport number search failed: {str(e)}")
            raise JubileeESBError(f"IPRS passport number search failed: {str(e)}")


    #  search Birth Certificate Number Interface
    @tracer.capture_method
    def search_birth_certificate_number(self, data) -> Dict:
        """
        Search based on Birth Certificate (Sec 12-13)
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "identifier": {"type": "string"},
                    "value": {"type": "string"}
                },

                "required": ["identifier", "value"]
            }
            validate(event=data, schema=schema)
            return self.utilities._make_api_call(
                "IPRS",
                api_method="search_birth_certificate_number",
                url=f"/iprs/searchUsingBirthCertificateNumber/{self.business}",
                data=data,
                is_post=True
            )

        except Exception as e:
            logger.error(f"IPRS birth certificate number search failed: {str(e)}")
            raise JubileeESBError(f"IPRS birth certificate number search failed: {str(e)}")


    # search Death Certificate Number Interface
    @tracer.capture_method
    def search_death_certificate_number(self, data) -> Dict:
        """
        Search based on Death Certificate (Sec 13-15)
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "identifier": {"type": "string"},
                    "value": {"type": "string"}
                },

                "required": ["identifier", "value"]
            }

            validate(event=data, schema=schema)
            return self.utilities._make_api_call(
                "IPRS",
                api_method="search_death_certificate_number",
                url=f"/iprs/searchUsingDeathCertificateNumber/{self.business}",
                data=data,
                is_post=True
            )

        except Exception as e:
            logger.error(f"IPRS death certificate number search failed: {str(e)}")
            raise JubileeESBError(f"IPRS death certificate number search failed: {str(e)}")


    # Bulk IPRS search Interface
    @tracer.capture_method
    def bulk_iprs_search(self, data: List[Dict]) -> Dict:
        """
        Bulk IPRS search interface (Sec 5-6), searches for an individual in the system.
        """
        try:
            schema = {
                "type": "array",
                "items" : {
                    "type": "object",
                    "properties": {
                        "identifier": {"type": "string"},
                        "value": {"type": "string"}
                    },
                    "required": ["identifier", "value"]
                }
            }

            validate(event=data, schema=schema)

            return self.utilities.make_api_call(
                "IPRS",
                api_method="bulk_search",
                url=f"/iprs/bulk-search/{self.business}",
                data=data,
                is_post=True
            )

        except Exception as e:
            logger.error(f"IPRS search failed: {str(e)}")
            raise JubileeESBError(f"IPRS search failed: {str(e)}")

