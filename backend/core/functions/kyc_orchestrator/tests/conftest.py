"""Shared fixtures for KYC Orchestrator face match tests."""
import sys
import os
import pytest
from unittest.mock import Mock, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def mock_rekognition():
    """Mock Rekognition client."""
    client = Mock()
    return client


@pytest.fixture
def mock_s3():
    """Mock S3 client."""
    client = Mock()
    return client


@pytest.fixture
def mock_liveness_image():
    """Fake liveness reference image bytes."""
    return b'\xff\xd8\xff\xe0' + b'\x00' * 100  # Minimal JPEG-like bytes


@pytest.fixture
def mock_document_image():
    """Fake document image bytes (valid JPEG for Pillow)."""
    from PIL import Image
    import io
    img = Image.new('RGB', (800, 600), color='white')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    return buf.read()
