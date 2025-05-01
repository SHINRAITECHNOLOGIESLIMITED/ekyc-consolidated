from typing import Dict, Any, List

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate

from utiities import JubileeESBError, JubileeESBUtilities

logger = Logger()
tracer = Tracer()


class IPRS:

    def __init__(self, utilities: JubileeESBUtilities):
        self.utilities = utilities

    # IPRS Methods
    @tracer.capture_method
    def search(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        This interface searches for an individual in the system.
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
                api_method="search",
                url=f"/iprs/searchV2/{self.business}",
                data=data
            )
        except Exception as e:
            logger.error(f"IPRS search failed: {str(e)}")
            raise JubileeESBError(f"IPRS search failed: {str(e)}")

    @tracer.capture_method
    def ping(self) -> Dict[str, Any]:
        """Check IPRS service availability"""
        try:
            return self._make_api_call(
                "IPRS",
                f"{self.base_url}/ping",
                {},
                self.credentials
            )
        except Exception as e:
            logger.error(f"IPRS ping failed: {str(e)}")
            raise JubileeESBError(f"IPRS ping failed: {str(e)}")

    @tracer.capture_method
    def search_alien_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search IPRS using Alien ID

        Args:
            data: Dictionary containing alien ID number
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "alien_id": {"type": "string"}
                },
                "required": ["alien_id"]
            }
            validate(event=data, schema=schema)

            return self._make_api_call(
                "IPRS",
                f"{self.base_url}/search/alien",
                data,
                self.credentials
            )
        except Exception as e:
            logger.error(f"IPRS alien ID search failed: {str(e)}")
            raise JubileeESBError(f"IPRS alien ID search failed: {str(e)}")

    @tracer.capture_method
    def search_passport(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search IPRS using Passport Number

        Args:
            data: Dictionary containing passport number
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "passport_number": {"type": "string"}
                },
                "required": ["passport_number"]
            }
            validate(event=data, schema=schema)

            return self._make_api_call(
                "IPRS",
                f"{self.base_url}/search/passport",
                data,
                self.credentials
            )
        except Exception as e:
            logger.error(f"IPRS passport search failed: {str(e)}")
            raise JubileeESBError(f"IPRS passport search failed: {str(e)}")

    @tracer.capture_method
    def search_birth_certificate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search IPRS using Birth Certificate Number

        Args:
            data: Dictionary containing birth certificate number
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "birth_certificate_number": {"type": "string"}
                },
                "required": ["birth_certificate_number"]
            }
            validate(event=data, schema=schema)

            return self._make_api_call(
                "IPRS",
                f"{self.base_url}/search/birth",
                data,
                self.credentials
            )
        except Exception as e:
            logger.error(f"IPRS birth certificate search failed: {str(e)}")
            raise JubileeESBError(f"IPRS birth certificate search failed: {str(e)}")

    @tracer.capture_method
    def search_death_certificate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search IPRS using Death Certificate Number

        Args:
            data: Dictionary containing death certificate number
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "death_certificate_number": {"type": "string"}
                },
                "required": ["death_certificate_number"]
            }
            validate(event=data, schema=schema)

            return self._make_api_call(
                "IPRS",
                f"{self.base_url}/search/death",
                data,
                self.credentials
            )
        except Exception as e:
            logger.error(f"IPRS death certificate search failed: {str(e)}")
            raise JubileeESBError(f"IPRS death certificate search failed: {str(e)}")

    @tracer.capture_method
    def bulk_search(self, data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Perform bulk IPRS search

        Args:
            data: Dictionary containing list of search requests
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "searches": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id_number": {"type": "string"},
                                "search_type": {"type": "string"}
                            },
                            "required": ["id_number"]
                        }
                    }
                },
                "required": ["searches"]
            }
            validate(event=data, schema=schema)

            return self._make_api_call(
                "IPRS",
                f"{self.base_url}/search/bulk",
                data,
                self.credentials
            )
        except Exception as e:
            logger.error(f"IPRS bulk search failed: {str(e)}")
            raise JubileeESBError(f"IPRS bulk search failed: {str(e)}")
