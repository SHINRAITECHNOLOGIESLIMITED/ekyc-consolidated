# E2E Tests for Jubilee eKYC

This directory contains end-to-end tests for the Jubilee eKYC system. The tests are organized into two main categories:

- **Validation Tests**: Tests that validate user-provided data against uploaded document images/PDFs (checking if the data entered by the user matches what's on the document)
- **Verification Tests**: Tests that verify user-provided data against government identity services like IPRS and KRA (checking if the data is authentic according to official records)

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

# KRA PIN Certificate verification - Tests verification of KRA PIN information against official KRA government records
python -m e2e.tests.verification.test_verify_krapincertificate

# Passport verification - Tests verification of passport information against IPRS government records
python -m e2e.tests.verification.test_verify_passport
```

### Background check Tests

```bash
# Check background using lexisnexis api
python -m e2e.tests.backgroundCheck.test_background_check
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

- `config.py`: Configuration file with API endpoints and authentication setup

## Equivalent awscurl Commands for Each Test

Below are the equivalent awscurl commands for each pytest test in the e2e folder. These commands can be used to test the API endpoints directly without using the Python test framework.

### Validation Tests

#### National ID Validation Tests

##### test_idnumber_36296352
```bash
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
  https://ukj5fnux32.execute-api.eu-west-1.amazonaws.com/Stage/document/nationalid | jq .
```

##### test_idnumber_23224868
```bash
awscurl --service execute-api \
  --region eu-west-1 \
  --profile shinrai.devpost \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "uploadedDocumentUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/c2a5e464-30b1-70e8-eeb0-8c196da88147/23224868/KENYAN_NATIONAL_ID-fc1aa117beca19366fcc301c9aa87e50e7f4e5aa.pdf",
    "serialNumber": "217990310",
    "idNumber": "23224868",
    "fullNames": "STEPHEN BIKO NYAMAI",
    "dateOfBirth": "19-02-1984",
    "dateOfIssue": "01-04-2003",
    "gender": "MALE",
    "districtOfBirth": "KIBWEZI",
    "placeOfIssue": "MAKADARA"
  }' \
  https://ukj5fnux32.execute-api.eu-west-1.amazonaws.com/Stage/document/nationalid
```

#### CR12 Validation Test

##### test_businessnumber_PVTRXUMYGVQ
```bash
awscurl --service execute-api \
  --region eu-west-1 \
  --profile shinrai.devpost \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "uploadedDocumentUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/CERTIFICATE_OF_INCORPORATION-003Sample.jpg",
    "businessNumber": "PVT-RXUMYGVQ",
    "businessName": "DETALI INSURANCE AGENCY LIMITED",
    "dateOfIncorporation": "2024-04-09",
    "businessType": "Private Limited Company"
  }' \
  https://ukj5fnux32.execute-api.eu-west-1.amazonaws.com/Stage/document/cr12
```

#### KRA PIN Certificate Validation Test

##### test_pin_A003388522V
```bash
awscurl --service execute-api \
  --region eu-west-1 \
  --profile shinrai.devpost \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "uploadedDocumentUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KRA_PIN_CERTIFICATE-002samplekra.jpg",
    "certificateDate": "2014-10-14",
    "pin": "A003388522V",
    "taxPayerName": "Jackson Gitonga Mwangi",
    "emailAddress": "jackmwangi02@gmail.com"
  }' \
  https://ukj5fnux32.execute-api.eu-west-1.amazonaws.com/Stage/document/krapincertificate
```

#### Passport Validation Test

##### test_passportnumber_DK9038
```bash
awscurl --service execute-api \
  --region eu-west-1 \
  --profile shinrai.devpost \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "uploadedDocumentUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_PASSPORT-001sample.jpg",
    "documentType": "P",
    "countryCode": "KEN",
    "passportNumber": "DK9038",
    "personalNumber": "1736740",
    "surname": "KAJIMBA",
    "givenNames": "GEORGE HUMPHREY",
    "dateOfBirth": "1987-05-18",
    "placeOfBirth": "MIGORI, Ken",
    "dateOfIssue": "2020-08-20",
    "dateOfExpiry": "2030-09-03",
    "nationality": "KENYAN",
    "issuingAuthority": "GOVERNMENT OF KENYA"
  }' \
  https://ukj5fnux32.execute-api.eu-west-1.amazonaws.com/Stage/document/passport | jq .
```

### Verification Tests

#### National ID Verification Tests

##### test_idnumber_23667272
```bash
awscurl --service execute-api \
  --region eu-west-1 \
  --profile shinrai.devpost \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "serialNumber": "242865407",
    "idNumber": "23667272",
    "fullNames": "JANE WAIRIMU MAINA",
    "dateOfBirth": "1985-01-01",
    "dateOfIssue": "2016-10-28",
    "gender": "Female",
    "districtOfBirth": "THIKA WEST"
  }' \
  https://ukj5fnux32.execute-api.eu-west-1.amazonaws.com/Stage/government/nationalid | jq .
```

##### test_idnumber_32140017
```bash
awscurl --service execute-api \
  --region eu-west-1 \
  --profile shinrai.devpost \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "serialNumber": "702945559",
    "idNumber": "32140017",
    "fullNames": "EFFIE NJOKI NYAMBURA",
    "dateOfBirth": "1994-19-12",
    "dateOfIssue": "2021-09-06",
    "gender": "Female",
    "districtOfBirth": "KIAMBU"
  }' \
  https://ukj5fnux32.execute-api.eu-west-1.amazonaws.com/Stage/government/nationalid
```

##### test_idnumber_36296352
```bash
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

##### test_idnumber_23224868
```bash
awscurl --service execute-api \
  --region eu-west-1 \
  --profile shinrai.devpost \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "serialNumber": "217990310",
    "idNumber": "23224868",
    "fullNames": "STEPHEN BIKO NYAMAI",
    "dateOfBirth": "1984-02-19",
    "dateOfIssue": "2003-04-01",
    "gender": "Male",
    "districtOfBirth": "KIBWEZI"
  }' \
  https://ukj5fnux32.execute-api.eu-west-1.amazonaws.com/Stage/government/nationalid
```

#### KRA PIN Certificate Verification Tests

##### test_pin_A003388522V
```bash
awscurl --service execute-api \
  --region eu-west-1 \
  --profile shinrai.devpost \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "pin": "A003388522V",
    "idNumber": "32140017",
    "taxPayerName": "Jackson Gitonga Mwangi",
  }' \
  https://ukj5fnux32.execute-api.eu-west-1.amazonaws.com/Stage/government/kra
```

##### test_pin_A011797599Y
```bash
awscurl --service execute-api \
  --region eu-west-1 \
  --profile shinrai.devpost \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "idNumber": "36296352",
    "pin": "A011797599Y",
    "taxPayerName": "JOEL MUUO"
  }' \
  https://ukj5fnux32.execute-api.eu-west-1.amazonaws.com/Stage/government/kra
```

##### test_pin_A008279496S
```bash
awscurl --service execute-api \
  --region eu-west-1 \
  --profile shinrai.devpost \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "idNumber":"32140017",
    "pin": "A008279496S",
    "taxPayerName": "EFFIE NJOKI NYAMBURA"
  }' \
  https://ukj5fnux32.execute-api.eu-west-1.amazonaws.com/Stage/government/kra
```

##### test_pin_A005394549Z
```bash
awscurl --service execute-api \
  --region eu-west-1 \
  --profile shinrai.devpost \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "pin": "A005394549Z",
    "taxPayerName": "PATRICK OMONDI ODHIAMBO "
    "idNumber": "24106259",
  }' \
  https://ukj5fnux32.execute-api.eu-west-1.amazonaws.com/Stage/government/kra
```

#### Passport Verification Tests

##### test_passportnumber_AK1515374
```bash
awscurl --service execute-api \
  --region eu-west-1 \
  --profile shinrai.devpost \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "documentType": "P",
    "countryCode": "KEN",
    "passportNumber": "AK1515374",
    "idNumber": "32140017",
    "personalNumber": "741116",
     "gender": "F",
    "surname": "NYAMBURA",
    "givenNames": "EFFIE NJOKI",
    "dateOfBirth": "1994-12-19",
    "placeOfBirth": "KIAMBU, KEN",
    "dateOfIssue": "2024-05-06",
    "dateOfExpiry": "2034-05-05",
    "nationality": "KENYAN",
    "issuingAuthority": "GOVERNMENT OF KENYA"
  }' \
  https://ukj5fnux32.execute-api.eu-west-1.amazonaws.com/Stage/government/passport
```

##### test_passportnumber_AK1370344
```bash
awscurl --service execute-api \
  --region eu-west-1 \
  --profile shinrai.devpost \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "documentType": "P",
    "countryCode": "KEN",
    "idNumber": "26465570",
    "passportNumber": "AK1370344",
    "personalNumber": "1944445",
    "surname": "Munyao",
    "gender": "M",
    "givenNames": "Timothy",
    "dateOfBirth": "1988-01-13",
    "placeOfBirth": "NAIROBI, KEN",
    "dateOfIssue": "2023-07-20",
    "dateOfExpiry": "2033-07-19",
    "nationality": "KENYAN",
    "issuingAuthority": "GOVERNMENT OF KENYA"
  }' \
  https://ukj5fnux32.execute-api.eu-west-1.amazonaws.com/Stage/government/passport
```