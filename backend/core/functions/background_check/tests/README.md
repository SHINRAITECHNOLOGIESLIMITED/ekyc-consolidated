# Background Check Lambda Tests

This directory contains unit and integration tests for the background check Lambda function.

## Test Structure

- `test_app.py`: Unit tests for individual components of the Lambda function
- `test_integration.py`: Integration tests for the Lambda function's interaction with external dependencies
- `test_cors.py`: Tests for CORS headers in responses
- `test_edge_cases.py`: Tests for edge cases and error handling

## Running Tests

To run the tests, navigate to the `background_check` directory and run:

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=src

# Run specific test file
pytest tests/test_app.py
```

## Test Coverage

These tests cover:
- Input validation
- Error handling
- Successful processing
- Integration with external services
- Response formatting
- CORS headers
- Edge cases