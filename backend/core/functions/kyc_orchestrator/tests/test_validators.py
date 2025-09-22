"""
Unit tests for the KYC request validation functions.
"""

import pytest


class TestKYCValidators:
    """Test cases for KYC request validation functions."""

    def test_validate_customer_request_success(self, mock_dependencies, sample_customer_request):
        """Test successful validation of customer request."""
        from validators import validate_kyc_request

        result = validate_kyc_request(sample_customer_request)

        assert result['valid'] is True
        assert len(result['errors']) == 0

    def test_validate_individual_agent_request_success(self, mock_dependencies, sample_individual_agent_request):
        """Test successful validation of individual agent request."""
        from validators import validate_kyc_request

        result = validate_kyc_request(sample_individual_agent_request)

        assert result['valid'] is True
        assert len(result['errors']) == 0

    def test_validate_business_agent_request_success(self, mock_dependencies, sample_business_agent_request):
        """Test successful validation of business agent request."""
        from validators import validate_kyc_request

        result = validate_kyc_request(sample_business_agent_request)

        assert result['valid'] is True
        assert len(result['errors']) == 0

    def test_validate_missing_required_fields(self, mock_dependencies):
        """Test validation failure for missing required fields."""
        from validators import validate_kyc_request

        invalid_request = {
            "processType": "customer"
            # Missing personalData and documents
        }

        result = validate_kyc_request(invalid_request)
        assert result['valid'] is False
        assert len(result['errors']) > 0

    def test_validate_invalid_process_type(self, mock_dependencies, sample_customer_request):
        """Test validation failure for invalid process type."""
        from validators import validate_kyc_request

        invalid_request = sample_customer_request.copy()
        invalid_request["processType"] = "invalid_type"

        result = validate_kyc_request(invalid_request)
        assert result['valid'] is False
        assert len(result['errors']) > 0

    def test_validate_customer_specific_missing_nationalid_and_passport(self, mock_dependencies):
        """Test customer-specific validation for missing both national ID and passport."""
        from validators import validate_customer_specific

        customer_data = {
            "processType": "customer",
            "personalData": {
                "name": "John Doe",
                "idNumber": "12345678",
                "pinNumber": "A000000000B",
                "dateOfBirth": "1990-01-15"
                # Missing gender
            },
            "documents": {
                "passportPhotoUrl": "https://example.com/photo.jpg",
                "kraUrl": "https://example.com/kra.pdf"
                # Missing nationalIdUrl and passportUrl
            }
        }

        errors = validate_customer_specific(customer_data)

        assert len(errors) > 0
        assert any("requires either nationalIdUrl or passportUrl" in error for error in errors)
        assert any("requires gender" in error for error in errors)

    def test_validate_customer_specific_missing_passport_photo(self, mock_dependencies):
        """Test customer-specific validation for missing passport photo."""
        from validators import validate_customer_specific

        customer_data = {
            "personalData": {"gender": "Male"},
            "documents": {
                "nationalIdUrl": "https://example.com/nationalid.pdf",
                "kraUrl": "https://example.com/kra.pdf"
                # Missing passportPhotoUrl
            }
        }

        errors = validate_customer_specific(customer_data)

        assert any("requires passportPhotoUrl" in error for error in errors)

    def test_validate_customer_specific_missing_kra_url(self, mock_dependencies):
        """Test customer-specific validation for missing KRA URL."""
        from validators import validate_customer_specific

        customer_data = {
            "personalData": {"gender": "Male"},
            "documents": {
                "nationalIdUrl": "https://example.com/nationalid.pdf",
                "passportPhotoUrl": "https://example.com/photo.jpg"
                # Missing kraUrl
            }
        }

        errors = validate_customer_specific(customer_data)

        assert any("requires kraUrl" in error for error in errors)

    def test_validate_individual_agent_specific_missing_nationalid(self, mock_dependencies):
        """Test individual agent-specific validation for missing national ID."""
        from validators import validate_individual_agent_specific

        agent_data = {
            "personalData": {"gender": "Female"},
            "documents": {
                "passportPhotoUrl": "https://example.com/photo.jpg"
                # Missing nationalIdUrl
            }
        }

        errors = validate_individual_agent_specific(agent_data)

        assert any("requires nationalIdUrl" in error for error in errors)

    def test_validate_individual_agent_specific_missing_gender(self, mock_dependencies):
        """Test individual agent-specific validation for missing gender."""
        from validators import validate_individual_agent_specific

        agent_data = {
            "personalData": {},  # Missing gender
            "documents": {
                "nationalIdUrl": "https://example.com/nationalid.pdf",
                "passportPhotoUrl": "https://example.com/photo.jpg"
            }
        }

        errors = validate_individual_agent_specific(agent_data)

        assert any("requires gender" in error for error in errors)

    def test_validate_business_agent_specific_missing_company_certificate(self, mock_dependencies):
        """Test business agent-specific validation for missing company certificate."""
        from validators import validate_business_agent_specific

        agent_data = {
            "personalData": {"businessNumber": "BN123456"},
            "documents": {
                "passportPhotoUrl": "https://example.com/photo.jpg"
                # Missing companyCertificateUrl
            }
        }

        errors = validate_business_agent_specific(agent_data)

        assert any("requires companyCertificateUrl" in error for error in errors)

    def test_validate_business_agent_specific_missing_business_number(self, mock_dependencies):
        """Test business agent-specific validation for missing business number."""
        from validators import validate_business_agent_specific

        agent_data = {
            "personalData": {},  # Missing businessNumber
            "documents": {
                "companyCertificateUrl": "https://example.com/cert.pdf",
                "passportPhotoUrl": "https://example.com/photo.jpg"
            }
        }

        errors = validate_business_agent_specific(agent_data)

        assert any("requires businessNumber" in error for error in errors)

    def test_validate_document_urls_invalid_format(self, mock_dependencies):
        """Test validation of invalid URL formats."""
        from validators import validate_document_urls

        invalid_documents = {
            "nationalIdUrl": "not-a-url",
            "passportPhotoUrl": "ftp://invalid-protocol.com/file.jpg",
            "kraUrl": "https://valid-url.com/file.pdf"
        }

        errors = validate_document_urls(invalid_documents)

        assert len(errors) >= 1  # At least one invalid URL should be caught
        assert any("Invalid URL format" in error for error in errors)

    def test_validate_document_urls_valid_format(self, mock_dependencies):
        """Test validation of valid URL formats."""
        from validators import validate_document_urls

        valid_documents = {
            "nationalIdUrl": "https://example.com/nationalid.pdf",
            "passportPhotoUrl": "http://example.com/photo.jpg",
            "kraUrl": "https://secure.example.com/kra.pdf"
        }

        errors = validate_document_urls(valid_documents)

        assert len(errors) == 0

    def test_validate_date_format_valid(self, mock_dependencies):
        """Test validation of valid date format."""
        from validators import validate_date_format

        errors = validate_date_format("1990-01-15", "dateOfBirth")

        assert len(errors) == 0

    def test_validate_date_format_invalid(self, mock_dependencies):
        """Test validation of invalid date format."""
        from validators import validate_date_format

        invalid_dates = [
            "15-01-1990",  # Wrong format
            "1990/01/15",  # Wrong separator
            "1990-13-01",  # Invalid month
            "1990-01-32",  # Invalid day
            "not-a-date"   # Not a date
        ]

        for invalid_date in invalid_dates:
            errors = validate_date_format(invalid_date, "testField")
            assert len(errors) > 0
            assert "Invalid date format" in errors[0]

    def test_validate_beneficiaries_valid(self, mock_dependencies):
        """Test validation of valid beneficiaries."""
        from validators import validate_kyc_request

        customer_request = {
            "processType": "customer",
            "personalData": {
                "name": "John Doe",
                "idNumber": "12345678",
                "pinNumber": "A000000000B",
                "dateOfBirth": "1990-01-15",
                "gender": "Male"
            },
            "documents": {
                "nationalIdUrl": "https://example.com/nationalid.pdf",
                "passportPhotoUrl": "https://example.com/photo.jpg",
                "kraUrl": "https://example.com/kra.pdf"
            },
            "beneficiaries": [
                {
                    "idNumber": "BC123456",
                    "relationship": "Child",
                    "gender": "Female",
                    "dateOfBirth": "2010-05-10"
                },
                {
                    "idNumber": "87654321",
                    "relationship": "Spouse",
                    "gender": "Female",
                    "dateOfBirth": "1992-03-20"
                }
            ]
        }

        result = validate_kyc_request(customer_request)

        assert result['valid'] is True
        assert len(result['errors']) == 0

    def test_validate_with_options(self, mock_dependencies):
        """Test validation with various options."""
        from validators import validate_kyc_request

        customer_request = {
            "processType": "customer",
            "personalData": {
                "name": "John Doe",
                "idNumber": "12345678",
                "pinNumber": "A000000000B",
                "dateOfBirth": "1990-01-15",
                "gender": "Male"
            },
            "documents": {
                "nationalIdUrl": "https://example.com/nationalid.pdf",
                "passportPhotoUrl": "https://example.com/photo.jpg",
                "kraUrl": "https://example.com/kra.pdf"
            },
            "options": {
                "includeFaceLiveness": True,
                "includeBackgroundCheck": False,
                "generateCertificate": True,
                "skipValidationErrors": False
            }
        }

        result = validate_kyc_request(customer_request)

        assert result['valid'] is True
        assert len(result['errors']) == 0