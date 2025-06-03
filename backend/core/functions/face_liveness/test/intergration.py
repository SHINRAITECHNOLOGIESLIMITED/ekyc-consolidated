import pytest
import json
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

# Import your functions
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
from app import create_face_liveness_session, get_face_liveness_results, handler
from importlib import reload
import app  # Import the app module

@pytest.fixture
def setup_environment():
    """Setup environment variables needed for the tests"""
    # Store original environment
    original_env = dict(os.environ)

    # Set test environment variables
    os.environ['FACELIVENESSRESULTS_TABLE_NAME'] = 'test-table'

    # Reload the app module to pick up new environment variables
    reload(app)

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
    reload(app)
@pytest.fixture
def mock_context():
    context = Mock()
    context.aws_request_id = "test-request-id"
    context.get_remaining_time_in_millis.return_value = 1000
    return context

@pytest.fixture
def mock_rekognition_client():
    with patch('app.rekognition_client') as mock:
        yield mock

@pytest.fixture
def mock_dynamodb_table():
    with patch('app.table') as mock:
        yield mock

class TestCreateFaceLivenessSession:
    def test_successful_session_creation(self, mock_context, mock_rekognition_client, mock_dynamodb_table):
        # Arrange
        mock_rekognition_client.create_face_liveness_session.return_value = {
            'SessionId': 'test-session-id'
        }

        # Act
        result = create_face_liveness_session({}, mock_context)

        # Assert
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert 'sessionId' in response_body
        assert response_body['sessionId'] == 'test-session-id'
        mock_dynamodb_table.put_item.assert_called_once()

    def test_handle_client_error(self, mock_context, mock_rekognition_client, mock_dynamodb_table):
        # Arrange
        error_response = {
            'Error': {
                'Code': 'AccessDeniedException',
                'Message': 'Test error'
            }
        }
        mock_rekognition_client.create_face_liveness_session.side_effect = \
            ClientError(error_response, 'CreateFaceLivenessSession')

        # Act
        result = create_face_liveness_session({}, mock_context)

        # Assert
        assert result['statusCode'] == 500
        response_body = json.loads(result['body'])
        assert 'error' in response_body
        assert 'message' in response_body

class TestGetFaceLivenessResults:
    def test_successful_results_retrieval(self, mock_context, mock_rekognition_client, mock_dynamodb_table):
        # Arrange
        event = {
            'body': json.dumps({'sessionId': 'test-session-id'})
        }
        mock_rekognition_client.get_face_liveness_session_results.return_value = {
            'Confidence': 95,
            'Status': 'SUCCEEDED'
        }

        # Act
        result = get_face_liveness_results(event, mock_context)

        # Assert
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['confidence'] == 95
        assert response_body['status'] == 'SUCCEEDED'
        assert response_body['isLive'] == True
        mock_dynamodb_table.update_item.assert_called_once()

    def test_missing_session_id(self, mock_context, mock_rekognition_client, mock_dynamodb_table):
        # Arrange
        event = {'body': json.dumps({})}

        # Act
        result = get_face_liveness_results(event, mock_context)

        # Assert
        assert result['statusCode'] == 400
        response_body = json.loads(result['body'])
        assert 'message' in response_body

    def test_rekognition_client_error(self, mock_context, mock_rekognition_client, mock_dynamodb_table):
        # Arrange
        event = {
            'body': json.dumps({'sessionId': 'test-session-id'})
        }
        error_response = {
            'Error': {
                'Code': 'ResourceNotFoundException',
                'Message': 'Session not found'
            }
        }
        mock_rekognition_client.get_face_liveness_session_results.side_effect = \
            ClientError(error_response, 'GetFaceLivenessSessionResults')

        # Act
        result = get_face_liveness_results(event, mock_context)

        # Assert
        assert result['statusCode'] == 500
        response_body = json.loads(result['body'])
        assert 'error' in response_body

# Tests that require environment variables use setup_environment fixture
class TestHandler:
    def test_handler_with_create_action(self, setup_environment, mock_context, mock_rekognition_client, mock_dynamodb_table):
        # Arrange
        event = {
            'body': json.dumps({'action': 'create'})
        }
        mock_rekognition_client.create_face_liveness_session.return_value = {
            'SessionId': 'test-session-id'
        }

        # Act
        result = app.handler(event, mock_context)

        # Assert
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert 'sessionId' in response_body

    def test_handler_with_get_results(self, setup_environment, mock_context, mock_rekognition_client, mock_dynamodb_table):
        # Arrange
        event = {
            'body': json.dumps({
                'action': 'get_results',
                'sessionId': 'test-session-id'
            })
        }
        mock_rekognition_client.get_face_liveness_session_results.return_value = {
            'Confidence': 95,
            'Status': 'SUCCEEDED'
        }

        # Act
        result = app.handler(event, mock_context)

        # Assert
        assert result['statusCode'] == 200
        response_body = json.loads(result['body'])
        assert response_body['confidence'] == 95
        assert response_body['isLive'] == True

    def test_handler_with_invalid_action(self, setup_environment, mock_context):
        # Arrange
        event = {
            'body': json.dumps({'action': 'invalid_action'})
        }

        # Act
        result = app.handler(event, mock_context)

        # Assert
        assert result['statusCode'] == 400
        response_body = json.loads(result['body'])
        assert 'message' in response_body
        assert response_body['message'] == 'Invalid action specified'

    def test_handler_with_missing_action(self, setup_environment, mock_context):
        # Arrange
        event = {
            'body': json.dumps(dict(message='no action'))
        }

        # Act
        result = app.handler(event, mock_context)

        # Assert
        assert result['statusCode'] == 400
        response_body = json.loads(result['body'])
        assert 'message' in response_body
        assert response_body['message'] == 'Invalid action specified'

    def test_handler_with_malformed_json(self, setup_environment, mock_context):
        # Arrange
        event = {
            'body': 'invalid json'
        }

        # Act
        result = app.handler(event, mock_context)

        # Assert
        assert result['statusCode'] == 400
        response_body = json.loads(result['body'])
        assert 'message' in response_body
        assert response_body['message'] == 'Invalid JSON in request body'

    def test_handler_with_missing_body(self, setup_environment, mock_context):
        # Arrange
        event = {}  # No body at all

        # Act
        result = app.handler(event, mock_context)

        # Assert
        assert result['statusCode'] == 400
        response_body = json.loads(result['body'])
        assert 'message' in response_body
        assert response_body['message'] == 'Empty request body'