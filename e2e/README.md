# E2E Tests for Jubilee eKYC

This directory contains end-to-end tests for the Jubilee eKYC system. The tests are organized into four main categories:

- **Validation Tests**: Tests that validate user-provided data against uploaded document images/PDFs (checking if the data entered by the user matches what's on the document)
- **Verification Tests**: Tests that verify user-provided data against government identity services like IPRS and KRA (checking if the data is authentic according to official records)
- **Background Check Tests**: Tests that verify background check functionality using LexisNexis API
- **Registration Tests**: Tests for agent and customer registration processes

## Prerequisites

- Python 3.6+
- AWS CLI configured with appropriate credentials
- `boto3` and `requests` Python packages

## Configuration

The tests use AWS SigV4 authentication to access the API Gateway endpoints. The configuration is stored in `e2e/tests/config.py` and includes:

- API Gateway URL
- S3 bucket for documents
- AWS profile name
- AWS region
- Service name (execute-api)

## Running Tests with Python

### Setup

1. Make sure you have the required Python packages installed:

```bash
pip install boto3 requests
```

2. Configure your AWS credentials:

```bash
aws configure --profile shinrai.devpost
```

### Running All Tests

To run all tests with report:
```
pytest e2e/tests --html=temp/report.html
```

To run all tests:

```bash
python -m unittest discover -s e2e/tests
```

### Running Specific Test Categories

To run only validation tests:

```bash
python -m unittest discover -s e2e/tests/validation
```

To run only verification tests:

```bash
python -m unittest discover -s e2e/tests/verification
```

To run only background check tests:

```bash
python -m unittest discover -s e2e/tests/background_checks
```

To run only registration tests:

```bash
python -m unittest discover -s e2e/tests/registration
```

### Running Individual Test Files

Below are commands to run each individual test file with descriptions of what each test validates:

#### Validation Tests

```bash
# National ID validation - Tests if user-provided National ID data matches the uploaded ID document
python -m e2e.tests.validation.test_validate_nationalid

# CR12 validation - Tests if user-provided business registration data matches the uploaded CR12 document
python -m e2e.tests.validation.test_validate_cr12

# KRA PIN Certificate validation - Tests if user-provided KRA PIN data matches the uploaded certificate
python -m e2e.tests.validation.test_validate_krapincertificate

# Passport validation - Tests if user-provided passport data matches the uploaded passport document
python -m e2e.tests.validation.test_validate_passport
```

#### Verification Tests

```bash
# National ID verification - Tests verification of National ID information against IPRS government records
python -m e2e.tests.verification.test_verify_nationalid

# KRA PIN verification - Tests verification of KRA PIN information against official KRA government records
python -m e2e.tests.verification.test_verify_kra

# KRA PIN Certificate verification - Tests verification of KRA PIN certificate information against official KRA government records
python -m e2e.tests.verification.test_verify_krapincertificate

# Passport verification - Tests verification of passport information against IPRS government records
python -m e2e.tests.verification.test_verify_passport
```

#### Background Check Tests

```bash
# Check background using LexisNexis API
python -m e2e.tests.background_checks.test_background_check
```

#### Registration Tests

```bash
# Test agent registration
python -m e2e.tests.registration.test_agent_registration

# Test customer registration
python -m e2e.tests.registration.test_customer_registration
```

## Running Tests with cURL

### Authentication

The API requires AWS SigV4 authentication. You can use the `awscurl` tool which supports SigV4 signing:

```bash
pip install awscurl
```

### Creating a Shell Script for Testing

You can create shell scripts to automate testing with cURL. Here's an example:

```bash
#!/bin/bash
# test_national_id.sh

echo "Testing National ID Validation..."
awscurl --service execute-api \
  --region eu-west-1 \
  --profile shinrai.devpost \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "uploadedDocumentUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_NATIONAL_ID-9f0ea801f683f6c8314c9d7ad0e7a93ed01b9693.jpg",
    "serialNumber": "242772451",
    "idNumber": "36296352",
    "fullNames": "JOEL MUUO",
    "dateOfBirth": "1998-08-30",
    "dateOfIssue": "2017-03-31",
    "gender": "Male",
    "districtOfBirth": "KIBWEZI",
    "placeOfIssue": "KIBWEZI"
  }' \
  https://ukj5fnux32.execute-api.eu-west-1.amazonaws.com/Stage/document/nationalid

echo -e "\nTesting National ID Verification..."
awscurl --service execute-api \
  --region eu-west-1 \
  --profile shinrai.devpost \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "serialNumber": "242772451",
    "idNumber": "36296352",
    "fullNames": "JOEL MUUO",
    "dateOfBirth": "1998-08-30",
    "dateOfIssue": "2017-03-31",
    "gender": "Male",
    "districtOfBirth": "KIBWEZI"
  }' \
  https://ukj5fnux32.execute-api.eu-west-1.amazonaws.com/Stage/government/nationalid
```

Make the script executable and run it:

```bash
chmod +x test_national_id.sh
./test_national_id.sh
```

## Test Structure

### Validation Tests
Tests that validate user-provided data against uploaded document images/PDFs (checking if the data entered matches what appears on the document):

- `test_validate_cr12.py`:
  - Tests CR12 document validation
  - Validates Certificate of Incorporation details against uploaded document
  - Tests business number PVT-RXUMYGVQ for DETALI INSURANCE AGENCY LIMITED

- `test_validate_krapincertificate.py`:
  - Tests KRA PIN certificate validation
  - Validates PIN A003388522V for Jackson Gitonga Mwangi
  - Checks certificate details against uploaded document

- `test_validate_nationalid.py`:
  - Tests National ID validation
  - Validates ID numbers 36296352 and 23224868
  - Checks ID details against uploaded document images

- `test_validate_passport.py`:
  - Tests Passport validation
  - Validates passport number DK9038 for GEORGE HUMPHREY KAJIMBA
  - Checks passport details against uploaded document

### Verification Tests
Tests that verify user-provided data against official government identity services like IPRS and KRA (checking if the data is authentic according to official government records):

- `test_verify_kra.py`:
  - Tests KRA PIN verification
  - Verifies multiple PINs: A003388522V, A011797599Y, A008279496S, A005394549Z
  - Checks PIN information against KRA records

- `test_verify_krapincertificate.py`:
  - Tests KRA PIN certificate verification
  - Verifies multiple PINs: A003388522V, A011797599Y, A008279496S, A005394549Z
  - Checks PIN information against KRA records

- `test_verify_nationalid.py`:
  - Tests National ID verification
  - Verifies ID numbers 23667272, 32140017, 36296352, 23224868
  - Checks ID information against government records

- `test_verify_passport.py`:
  - Tests Passport verification
  - Verifies passport numbers AK1515374 and AK1370344
  - Checks passport information against government records

### Background Check Tests
Tests that verify background check functionality:

- `test_background_check.py`:
  - Tests background check functionality using LexisNexis API
  - Verifies risk assessment for individuals

### Registration Tests
Tests for agent and customer registration processes:

- `test_agent_registration.py`:
  - Tests agent registration process
  - Validates agent data submission and account creation

- `test_customer_registration.py`:
  - Tests customer registration process
  - Validates customer data submission and account creation

- `config.py`: Configuration file with API endpoints and authentication setup