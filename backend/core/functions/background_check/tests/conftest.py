import sys
import os
from unittest.mock import MagicMock, patch
import pytest

# Create mocks for external dependencies
@pytest.fixture(autouse=True)
def mock_dependencies(monkeypatch):
    """Mock all external dependencies for tests"""
    # Mock modules
    mock_jubilee_esb_api = MagicMock()
    mock_portal = MagicMock()
    mock_aws_lambda_powertools = MagicMock()
    mock_validation = MagicMock()
    
    # Apply mocks
    monkeypatch.setitem(sys.modules, 'jubilee_esb_api', mock_jubilee_esb_api)
    monkeypatch.setitem(sys.modules, 'portal', mock_portal)
    monkeypatch.setitem(sys.modules, 'aws_lambda_powertools', mock_aws_lambda_powertools)
    monkeypatch.setitem(sys.modules, 'aws_lambda_powertools.utilities.validation', mock_validation)
    
    # Add the src directory to the path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))