import sys
import os
from unittest.mock import MagicMock, patch
import pytest

# Create mocks for external dependencies
@pytest.fixture(autouse=True)
def mock_dependencies(monkeypatch):
    """Mock all external dependencies for tests"""
    # Mock AWS Lambda Powertools modules
    mock_logger = MagicMock()
    mock_tracer = MagicMock()

    # Create decorators that return the original function
    def mock_inject_lambda_context(func):
        return func

    def mock_capture_lambda_handler(func):
        return func

    def mock_capture_method(func):
        return func

    mock_logger.inject_lambda_context = mock_inject_lambda_context
    mock_tracer.capture_lambda_handler = mock_capture_lambda_handler
    mock_tracer.capture_method = mock_capture_method

    mock_powertools = MagicMock()
    mock_powertools.Logger = MagicMock(return_value=mock_logger)
    mock_powertools.Tracer = MagicMock(return_value=mock_tracer)

    # Mock validation
    mock_validation = MagicMock()
    mock_validation.validate = MagicMock()

    # Mock portal
    mock_portal = MagicMock()
    mock_portal_class = MagicMock(return_value=mock_portal)

    # Mock boto3
    mock_boto3 = MagicMock()
    mock_lambda_client = MagicMock()
    mock_boto3.client.return_value = mock_lambda_client

    # Apply mocks
    monkeypatch.setitem(sys.modules, 'aws_lambda_powertools', mock_powertools)
    monkeypatch.setitem(sys.modules, 'aws_lambda_powertools.utilities.validation', mock_validation)
    monkeypatch.setitem(sys.modules, 'portal', mock_portal_class)
    monkeypatch.setitem(sys.modules, 'boto3', mock_boto3)

    # Add the src directory to the path
    src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    return {
        'mock_logger': mock_logger,
        'mock_tracer': mock_tracer,
        'mock_portal': mock_portal,
        'mock_lambda_client': mock_lambda_client,
        'mock_validation': mock_validation
    }

@pytest.fixture
def sample_customer_request():
    """Sample customer KYC request for testing"""
    return {
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
            "includeFaceLiveness": False,
            "includeBackgroundCheck": True,
            "generateCertificate": True
        }
    }

@pytest.fixture
def sample_individual_agent_request():
    """Sample individual agent KYC request for testing"""
    return {
        "processType": "individual_agent",
        "personalData": {
            "name": "Jane Smith",
            "idNumber": "87654321",
            "pinNumber": "A111111111C",
            "dateOfBirth": "1985-05-20",
            "gender": "Female"
        },
        "documents": {
            "nationalIdUrl": "https://example.com/nationalid.pdf",
            "passportPhotoUrl": "https://example.com/photo.jpg"
        },
        "options": {
            "includeFaceLiveness": True,
            "includeBackgroundCheck": True,
            "generateCertificate": True
        }
    }

@pytest.fixture
def sample_business_agent_request():
    """Sample business agent KYC request for testing"""
    return {
        "processType": "business_agent",
        "personalData": {
            "name": "ABC Limited",
            "idNumber": "12345678",
            "pinNumber": "A222222222D",
            "dateOfBirth": "1980-01-01",
            "businessNumber": "BN123456"
        },
        "documents": {
            "companyCertificateUrl": "https://example.com/certificate.pdf",
            "passportPhotoUrl": "https://example.com/photo.jpg"
        },
        "options": {
            "includeFaceLiveness": False,
            "includeBackgroundCheck": False,
            "generateCertificate": True
        }
    }

@pytest.fixture
def mock_lambda_responses():
    """Mock responses from existing Lambda functions"""
    return {
        "document_validation": {
            'statusCode': 200,
            'body': '{"status": "Valid", "extractedData": {"name": "John Doe"}, "success": true}'
        },
        "government_verification": {
            'statusCode': 200,
            'body': '{"status": "Valid", "matchDetails": {"names": {"valid": true}}, "success": true}'
        },
        "background_check": {
            'statusCode': 200,
            'body': '{"riskScore": 10, "status": "Low Risk", "success": true}'
        },
        "face_liveness": {
            'statusCode': 200,
            'body': '{"sessionId": "sess-12345", "status": "Created", "success": true}'
        },
        "certification": {
            'statusCode': 200,
            'body': '{"s3Path": "certificates/cert-12345.pdf", "certificateUrl": "https://example.com/cert.pdf", "success": true}'
        }
    }

@pytest.fixture
def mock_environment_variables(monkeypatch):
    """Mock environment variables"""
    env_vars = {
        'DOCUMENT_VALIDATION_FUNCTION': 'arn:aws:lambda:us-east-1:123456789:function:DocumentValidationFn',
        'GOVERNMENT_VERIFICATION_FUNCTION': 'arn:aws:lambda:us-east-1:123456789:function:GovernmentVerificationFn',
        'BACKGROUND_CHECK_FUNCTION': 'arn:aws:lambda:us-east-1:123456789:function:BackgroundChecksFn',
        'FACE_LIVENESS_FUNCTION': 'arn:aws:lambda:us-east-1:123456789:function:FaceLivenessFn',
        'CERTIFICATION_FUNCTION': 'arn:aws:lambda:us-east-1:123456789:function:CertificationFn',
        'PORTAL_GRAPHQL_SECRET_ARN': 'arn:aws:secretsmanager:us-east-1:123456789:secret:portal-graphql'
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)