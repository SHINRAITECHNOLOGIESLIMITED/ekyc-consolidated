import io
import json
import os
from io import BytesIO

import boto3
import requests
from PIL import Image
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate
from aws_lambda_powertools.utilities.validation.exceptions import SchemaValidationError
from botocore.exceptions import ClientError
from reportlab.pdfgen import canvas
from textract_utils import extract
from datetime import datetime

from portal import Portal

KYCDOCUMENTSBUCKET_NAME = os.environ.get('KYCDOCUMENTSBUCKET_NAME', None)
assert KYCDOCUMENTSBUCKET_NAME is not None, "KYCDOCUMENTSBUCKET_NAME is not set"

logger = Logger()
tracer = Tracer()
portal = Portal()
s3_client = boto3.client('s3')


def convert_to_pdf(file_name, content_type):
    """
    Read file_name format based on content type.

    Parameters:
    - file_name: document path
    - content_type: MIME type of the document

    Returns:
    - PDF binary data
    """

    # update function to convert using filename
    if content_type == 'application/pdf':
        # If it's already a PDF, just return the binary data
        with open(file_name, 'rb') as f:
            return f.read()
    logger.info(f"Document is not a PDF, converting to PDF")
    if content_type.startswith('image/'):
        # Handle image conversion
        img_buffer = io.BytesIO()
        img = Image.open(file_name)

        # Create PDF with the same dimensions as the image
        width, height = img.size
        c = canvas.Canvas(img_buffer, pagesize=(width, height))
        c.drawImage(file_name, 0, 0, width, height)
        c.save()
        return img_buffer.getvalue()
    else:
        raise Exception(f"Unsupported file type: {content_type}")  # Fixed syntax error


def copy_to_s3(url, object_key):
    """
    Downloads a document from a URL and uploads it to an S3 bucket.

    Parameters:
    - url: URL of the document to download. allow http,https,ftp,s3 ...etc
    - object_key: Key to use for the S3 object (if None, will be derived from URL)

    Returns:
    - S3 URI of the uploaded document and the object key
    """
    try:
        tmp_dir = '/tmp'
        file_name = f"{tmp_dir}/{os.path.basename(object_key)}"

        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_name), exist_ok=True)

        # if url is s3 ulr use s3_client to download the document
        if url.startswith('s3://'):
            bucket_name, key = url[5:].split('/', 1)
            try:
                content_type = s3_client.head_object(Bucket=bucket_name, Key=key)['ContentType']
                s3_client.download_file(bucket_name, key, file_name)
            except Exception as e:
                logger.error(f"Error downloading document from S3: {e}")
                raise Exception(f"Error downloading document from S3: {e}")
        else:
            # Download the object from url using requests
            response = requests.get(url)
            if response.status_code != 200:
                logger.error(f"Failed to download document: HTTP {response.status_code} from {url}")
                raise Exception(f"Failed to download document: HTTP {response.status_code} from {url}")
            # write to file
            with open(file_name, 'wb') as f:
                f.write(response.content)
            content_type = response.headers.get('Content-Type')

        # check if downloaded document is pdf - if not make it PDF
        try:
            binary = convert_to_pdf(file_name, content_type)
        except Exception as e:
            logger.error(f"Error converting to PDF: {e}")
            raise Exception(f"Error converting to PDF: {e}")

        s3_client.upload_fileobj(
            BytesIO(binary),
            KYCDOCUMENTSBUCKET_NAME,
            object_key,
            ExtraArgs={'ContentType': 'application/pdf'}
        )
        try:
            os.remove(file_name)
        except Exception as e:
            logger.error(f"Error removing file: {e}")

        # Return the S3 URI
        s3_uri = f"s3://{KYCDOCUMENTSBUCKET_NAME}/{object_key}"
        logger.info(f"Document uploaded to S3: {s3_uri}")
        return s3_uri, object_key

    except ClientError as e:
        logger.error(f"S3 operation error: {e}")
        raise Exception(f"Error accessing S3: {e}")
    except ValueError as e:
        logger.error(f"URL parsing error: {e}")
        raise Exception(f"Invalid S3 URL format: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise Exception(f"Error processing document: {e}")


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    """
    Lambda handler for document validation endpoints.
    Handles POST requests to various /document/* paths.
    Routes requests to specific handlers which perform schema validation.
    """
    # logger.info(f"Received event: {json.dumps(event)}")

    http_method = event.get('httpMethod')
    path = event.get('path')

    if http_method == 'POST':
        try:
            data = event.get('body', {})
            # check if data is dict - if its a string convert to dict
            while isinstance(data, str):
                data = json.loads(data)
            logger.info(f"Request Data (body): {data}")
            match path:
                case '/document/nationalid':
                    return validate_nationalid(data)
                case '/document/passport':
                    return validate_passport(data)
                case '/document/krapincertificate':
                    return validate_krapincertificate(data)
                case '/document/cr12':
                    return validate_cr12(data)
                case _:
                    return make_response(404, {'message': 'Path Not Found'})

        except json.JSONDecodeError as e:
            logger.error("Error decoding JSON body")
            return make_response(400, {'message': 'Invalid JSON body: {e}'})


        except Exception as e:
            logger.error(f"An unexpected error occurred in lambda_handler: {e}")
            return make_response(500, {'message': 'Internal Server Error'})

    else:
        logger.error('Method Not Allowed - received {http_method}')
        return make_response(405, {'message': 'Method Not Allowed'})

def levenshtein_distance(s1, s2):
    """Calculate the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def process(event_name, textract_name, event, form,is_date_field = False):
    if not event_name in event:
        status = "Not provided"
        details = None
    elif not textract_name in form:
        status = "Not Found"
        details = None
    else:
        expected = form[textract_name]['value']
        key_confidence= form[textract_name]['key_confidence']
        value_confidence= form[textract_name]['value_confidence']
        
        actual = event[event_name]
        if is_date_field:
            expected = expected.replace(".","-")
            actual = actual.replace(".","-")
            #convert expected and actual in date objects and check for equality
            # Try different date formats
            date_formats = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d']
            
            expected_date = None
            actual_date = None
            
            # Try to parse expected date
            for fmt in date_formats:
                try:
                    expected_date = datetime.strptime(expected.strip(), fmt).date()
                    break
                except ValueError:
                    continue
            
            # Try to parse actual date
            for fmt in date_formats:
                try:
                    actual_date = datetime.strptime(actual.strip(), fmt).date()
                    break
                except ValueError:
                    continue
            
            if expected_date and actual_date and expected_date == actual_date:
                status = "Matched"
                editdistance = 0
            else:
                status = "Not Matched"
                editdistance = 10  # Default edit distance for dates that don't match
        else:
            if actual.strip().lower() == expected.strip().lower():
                status = "Matched"
                editdistance = 0
            else:
                status = "Not Matched"
                # calculate edit distance
                editdistance = levenshtein_distance(actual.strip().lower(), expected.strip().lower())
        details = dict(editdistance=editdistance, expected=expected, actual=actual, key_confidence = key_confidence, value_confidence = value_confidence)

    return dict(status=status, details=details)
def rate(matchResults):
    accuracy=0.0
    confidence=0.0
    if len(matchResults) == 0:
        pass
    else:
        passed = 0
        failed = 0
        confidence_scores = []
        for field,result in matchResults.items():
            if "details" in result:
                if result["details"]:
                    if "key_confidence" in result["details"]:
                        confidence_scores.append(result["details"]["key_confidence"])
                    if "value_confidence" in result["details"]:
                        confidence_scores.append(result["details"]["value_confidence"])
            if 'status' in result:
                if result['status'] == 'Matched':
                    passed += 1
                elif result['status'] in ["Not Matched","Not Found"]:
                    failed += 1
        if confidence_scores:
            confidence = sum(confidence_scores)/len(confidence_scores)
        if failed + passed == 0:
            accuracy = 0.0
        else:
            accuracy = passed / (passed + failed) * 100
    return confidence,accuracy
def validate_nationalid(data):
    schema = {
        "type": "object",
        "properties": {
            "uploadedDocumentUrl": {"type": "string", "format": "uri"},
            "serialNumber": {"type": "string"},
            "idNumber": {"type": "string"},
            "fullNames": {"type": "string"},
            "dateOfBirth": {"type": "string", "format": "date"},
            "dateOfIssue": {"type": "string", "format": "date"},
            "gender": {"type": "string", "enum": ["Male", "Female"]},
            "districtOfBirth": {"type": "string"},
            "placeOfIssue": {"type": "string"},
        },
        "required": ["uploadedDocumentUrl", "idNumber"],
        "additionalProperties": False
    }

    try:
        validate(event=data, schema=schema)
        object_key = f"NationalID/{data['idNumber']}.pdf"
        url, s3Path = copy_to_s3(url=data['uploadedDocumentUrl'], object_key=object_key)
        logger.info(f"Downloaded {data['uploadedDocumentUrl']} to {url}")
        extracted = extract(s3Path)
        extracted_form = extracted["form"]
        logger.info(extracted_form)
        extracted_prose = " ".join(item['text'] for item in extracted["phrases"]).lower()
        checks = []

        checks.append({"check": 'Contains the words "Jamhuri ya Kenya"',
                       "result": "Jamhuri ya Kenya".lower() in extracted_prose})
        checks.append({"check": 'Contains the words "Republic of Kenya"',
                       "result": "Republic of Kenya".lower() in extracted_prose})
        serialNumberMatchResult = process(event_name='serialNumber', textract_name='SERIAL_NUMBER', event=data,
                                          form=extracted_form)
        idNumberMatchResult = process(event_name='idNumber', textract_name='ID_NUMBER', event=data,
                                      form=extracted_form)
        fullNamesMatchResult = process(event_name='fullNames', textract_name='FULL_NAMES', event=data,
                                       form=extracted_form)
        dateOfBirthMatchResult = process(event_name='dateOfBirth', textract_name='DATE_OF_BIRTH', event=data,
                                         form=extracted_form,is_date_field=True)
        dateOfIssueMatchResult = process(event_name='dateOfIssue', textract_name='DATE_OF_ISSUE', event=data,
                                         form=extracted_form,is_date_field=True)
        genderMatchResult = process(event_name='gender', textract_name='SEX', event=data, form=extracted_form)
        districtOfBirthMatchResult = process(event_name='districtOfBirth', textract_name='DISTRICT_OF_BIRTH',
                                             event=data, form=extracted_form)
        placeOfIssueMatchResult = process(event_name='placeOfIssue', textract_name='PLACE_OF_ISSUE', event=data,
                                          form=extracted_form)

        matchResults = dict(serialNumber=serialNumberMatchResult,
                            idNumber=idNumberMatchResult,
                            fullNames=fullNamesMatchResult,
                            dateOfBirth=dateOfBirthMatchResult,
                            dateOfIssue=dateOfIssueMatchResult,
                            gender=genderMatchResult,
                            districtOfBirth=districtOfBirthMatchResult,
                            placeOfIssue=placeOfIssueMatchResult,
                            )
        overall_confidence,overall_accuracy = rate(matchResults)
        portal.capture_doc_validation(documentType="NationalID", s3Path=s3Path,
                                      documentIdentifier=data['idNumber'], matchResults=matchResults,keywords_checks=checks,overall_accuracy=overall_accuracy,overall_confidence=overall_confidence)
        results = dict(keywords_checks=checks, matchResults=matchResults)
        logger.info(f"Results: {results}")
        return make_response(200, dict(s3Path=s3Path, results=results))
    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for NationalID document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in validate_nationalid: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


def validate_passport(data):
    schema = {
        "type": "object",
        "properties": {
            "uploadedDocumentUrl": {"type": "string", "format": "uri"},
            "documentType": {"type": "string"},
            "countryCode": {"type": "string"},
            "passportNumber": {"type": "string"},
            "personalNumber": {"type": "string"},
            "surname": {"type": "string"},
            "givenNames": {"type": "string"},
            "gender": {"type": "string"},
            "dateOfBirth": {"type": "string", "format": "date"},
            "placeOfBirth": {"type": "string"},
            "dateOfIssue": {"type": "string", "format": "date"},
            "dateOfExpiry": {"type": "string", "format": "date"},
            "nationality": {"type": "string"},
            "issuingAuthority": {"type": "string"},
        },
        "required": ["uploadedDocumentUrl", "passportNumber"],
        "additionalProperties": False
    }

    try:
        validate(event=data, schema=schema)
        object_key = f"Passport/{data['passportNumber']}.pdf"
        url, s3Path = copy_to_s3(url=data['uploadedDocumentUrl'], object_key=object_key)
        logger.info(f"Downloaded {data['uploadedDocumentUrl']} to {url}")
        extracted = extract(s3Path)
        extracted_form = extracted["form"]
        logger.info(extracted_form)
        extracted_prose = " ".join(item['text'] for item in extracted["phrases"]).lower()
        checks = []
        checks.append(
            {"check": 'Contains the words "Jamhuri ya Kenya"', "result": "Jamhuri ya Kenya".lower() in extracted_prose})
        checks.append({"check": 'Contains the words "Republic of Kenya"',
                       "result": "Republic of Kenya".lower() in extracted_prose})
        checks.append({"check": 'Contains the words "Republique de Kenya"',
                       "result": "Republique de Kenya".lower() in extracted_prose})
        documentTypeMatchResult = process(event_name='documentType', textract_name='TYPEAINA/TYPE', event=data,
                                          form=extracted_form)
        countryCodeMatchResult = process(event_name='countryCode',
                                         textract_name='COUNTRY_CODE_NAMBARI_YA_NCHICODE_DU_PAYS', event=data,
                                         form=extracted_form)
        passportNumberMatchResult = process(event_name='passportNumber',
                                            textract_name='PASSPORT_NO_NAMBARI_YA_PAST_N�_DE_PASSEPORT',
                                            event=data, form=extracted_form)
        personalNumberMatchResult = process(event_name='personalNumber',
                                            textract_name='PERSONAL_NO_NAMBARI_YA_KIBINAFSI/NO_PERSONNEL',
                                            event=data, form=extracted_form)
        surnameMatchResult = process(event_name='surname', textract_name='SURNAME./INA_LA_UKAO-NOM', event=data,
                                     form=extracted_form)
        givenNamesMatchResult = process(event_name='givenNames', textract_name='GIVEN_NAMES/MAJINA_ALIYOPEWA,_PRENOMS',
                                        event=data, form=extracted_form)
        genderMatchResult = process(event_name='gender', textract_name='SEXUINSIASEXE', event=data,
                                    form=extracted_form)
        dateOfBirthMatchResult = process(event_name='dateOfBirth',
                                         textract_name='DATE_OF_BIRTH/TAREHE_YA_KUZALIWA_DATE_DE_NAISSANCE',
                                         event=data, form=extracted_form,is_date_field=True)
        placeOfBirthMatchResult = process(event_name='placeOfBirth',
                                          textract_name='PLACE_OF_BIRTH_MAHAH_PA_KUZALIWALIEU_DE_NAISSANCE',
                                          event=data, form=extracted_form)
        dateOfIssueMatchResult = process(event_name='dateOfIssue', textract_name='DATE_OF_ISSUE_TAREHE_VA_KUTOLENA',
                                         event=data, form=extracted_form,is_date_field=True)
        dateOfExpiryMatchResult = process(event_name='dateOfExpiry', textract_name='DATE_OF_EXPIRY', event=data,
                                          form=extracted_form,is_date_field=True)
        nationalityMatchResult = process(event_name='nationality', textract_name='NATIONALITY/UTAIFA/NATIONALITY',
                                         event=data, form=extracted_form)
        issuingAuthorityMatchResult = process(event_name='issuingAuthority',
                                              textract_name='ISSUING_AUTHORITY_MAMLAKA_YA_KUTOA_PASIAUTORITE',
                                              event=data, form=extracted_form)

        matchResults = dict(documentType=documentTypeMatchResult,
                            countryCode=countryCodeMatchResult,
                            passportNumber=passportNumberMatchResult,
                            personalNumber=personalNumberMatchResult,
                            surname=surnameMatchResult,
                            givenNames=givenNamesMatchResult,
                            gender=genderMatchResult,
                            dateOfBirth=dateOfBirthMatchResult,
                            placeOfBirth=placeOfBirthMatchResult,
                            dateOfIssue=dateOfIssueMatchResult,
                            dateOfExpiry=dateOfExpiryMatchResult,
                            nationality=nationalityMatchResult,
                            issuingAuthority=issuingAuthorityMatchResult,
                            )
        overall_confidence,overall_accuracy = rate(matchResults)
        portal.capture_doc_validation(documentType="Passport", s3Path=s3Path,
                                      documentIdentifier=data['passportNumber'], matchResults=matchResults,keywords_checks=checks,overall_accuracy=overall_accuracy,overall_confidence=overall_confidence)
        results = dict(keywords_checks=checks, matchResults=matchResults)
        logger.info(f"Results: {results}")
        return make_response(200, dict(s3Path=s3Path, results=results))
    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for Passport document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in validate_passport: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


def validate_krapincertificate(data):
    schema = {
        "type": "object",
        "properties": {
            "uploadedDocumentUrl": {"type": "string", "format": "uri"},
            "certificateDate": {"type": "string"},
            "pin": {"type": "string"},
            "taxPayerName": {"type": "string"},
            "emailAddress": {"type": "string"},
        },
        "required": ["uploadedDocumentUrl", "pin"],
        "additionalProperties": False
    }
    try:
        validate(event=data, schema=schema)
        object_key = f"KRAPinCertificate/{data['pin']}.pdf"
        url, s3Path = copy_to_s3(url=data['uploadedDocumentUrl'], object_key=object_key)
        logger.info(f"Downloaded {data['uploadedDocumentUrl']} to {url}")
        extracted = extract(s3Path)
        extracted_form = extracted["form"]
        logger.info(extracted_form)
        extracted_prose = " ".join(item['text'] for item in extracted["phrases"]).lower()
        checks = []

        checks.append({"check": 'Contains the words "Kenya Revenue Authority"',
                       "result": "Kenya Revenue Authority".lower() in extracted_prose})
        checks.append(
            {"check": 'Contains the words "PIN Certificate"', "result": "PIN Certificate".lower() in extracted_prose})
        checks.append({"check": 'The url "www.kra.go.ke"', "result": "None".lower() in extracted_prose})
        certificateDateMatchResult = process(event_name='certificateDate', textract_name='CERTIFICATE_DATE',
                                             event=data, form=extracted_form,is_date_field=True)
        pinMatchResult = process(event_name='pin', textract_name='PERSONAL_IDENTIFICATION_NUMBER', event=data,
                                 form=extracted_form)
        taxPayerNameMatchResult = process(event_name='taxPayerName', textract_name='TAXPAYER_NAME', event=data,
                                          form=extracted_form)
        emailAddressMatchResult = process(event_name='emailAddress', textract_name='EMAIL_ADDRESS', event=data,
                                          form=extracted_form)

        matchResults = dict(certificateDate=certificateDateMatchResult,
                            pin=pinMatchResult,
                            taxPayerName=taxPayerNameMatchResult,
                            emailAddress=emailAddressMatchResult,
                            )
        overall_confidence,overall_accuracy = rate(matchResults)
        
        portal.capture_doc_validation(documentType="KRAPinCertificate", s3Path=s3Path,
                                      documentIdentifier=data['pin'], matchResults=matchResults,keywords_checks=checks,overall_accuracy=overall_accuracy,overall_confidence=overall_confidence)
        results = dict(keywords_checks=checks, matchResults=matchResults)
        logger.info(f"Results: {results}")
        return make_response(200, dict(s3Path=s3Path, results=results))
    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for KRAPinCertificate document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in validate_krapincertificate: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


def validate_cr12(data):
    schema = {
        "type": "object",
        "properties": {
            "uploadedDocumentUrl": {"type": "string", "format": "uri"},
            "businessNumber": {"type": "string"},
            "businessName": {"type": "string"},
            "dateOfIncorporation": {"type": "string", "format": "date"},
            "businessType": {"type": "string"},
        },
        "required": ["uploadedDocumentUrl", "businessNumber"],
        "additionalProperties": False
    }

    try:
        validate(event=data, schema=schema)
        object_key = f"CertificateOfIncorporation /{data['businessNumber']}.pdf"
        url, s3Path = copy_to_s3(url=data['uploadedDocumentUrl'], object_key=object_key)
        logger.info(f"Downloaded {data['uploadedDocumentUrl']} to {url}")
        extracted = extract(s3Path)
        extractedData = extracted["phrases"]
        logger.info(extractedData)
        extracted_form = extract_form_from_cr12_phrases(extractedData)
        logger.info(extracted_form)
        extracted_prose = " ".join(item['text'] for item in extracted["phrases"]).lower()
        checks = []

        checks.append({"check": 'Contains the words  "Certificate Of Incorporation"',
                       "result": "Certificate Of Incorporation".lower() in extracted_prose})
        businessNumberMatchResult = process(event_name='businessNumber', textract_name='businessNumber', event=data,
                                            form=extracted_form)
        businessNameMatchResult = process(event_name='businessName', textract_name='businessName', event=data,
                                          form=extracted_form)
        dateOfIncorporationMatchResult = process(event_name='dateOfIncorporation',
                                                 textract_name='dateOfIncorporation', event=data,
                                                 form=extracted_form,is_date_field=True)
        businessTypeMatchResult = process(event_name='businessType', textract_name='businessType', event=data,
                                          form=extracted_form)

        matchResults = dict(businessNumber=businessNumberMatchResult,
                            businessName=businessNameMatchResult,
                            dateOfIncorporation=dateOfIncorporationMatchResult,
                            businessType=businessTypeMatchResult,
                            )
        overall_confidence,overall_accuracy = rate(matchResults)
        portal.capture_doc_validation(documentType="CertificateOfIncorporation ", s3Path=s3Path,
                                      documentIdentifier=data['businessNumber'], matchResults=matchResults,keywords_checks=checks,overall_accuracy=overall_accuracy,overall_confidence=overall_confidence)
        results = dict(keywords_checks=checks, matchResults=matchResults)
        logger.info(f"Results: {results}")
        return make_response(200, dict(s3Path=s3Path, results=results))
    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for CertificateOfIncorporation  document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in validate_cr12: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


def extract_form_from_cr12_phrases(extractedData):
    if len(extractedData) >= 2:
        bsNumber = extractedData[1]['text'].replace("No.", "").strip()
        bsNumber_confidence = extractedData[1]['confidence']
    else:
        bsNumber = ""
        bsNumber_confidence = 0
    if len(extractedData) >= 5:
        businessName = extractedData[4]["text"].strip()
        businessName_confidence = extractedData[4]['confidence']
    else:
        businessName = extractedData[4].strip()
        businessName_confidence = 0
        
    dateOfIncorporation = ""
    businessType = ""
            
    extracted_form = dict(businessNumber=dict(value = bsNumber,key_confidence=100,value_confidence=bsNumber_confidence),
                          businessName=dict(value = businessName,key_confidence=100,value_confidence=businessName_confidence),
                          dateOfIncorporation=dict(value = dateOfIncorporation,key_confidence=100,value_confidence=0),
                          businessType=dict(value = businessType,key_confidence=100,value_confidence=0))
    return extracted_form


def make_response(status_code, body):
    """
    Helper function to format responses for API Gateway.
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }

if __name__ == "__main__":
    
    results = {
            "serialNumber": {
            "status": "Not provided",
            "details": null
            },
            "idNumber": {
            "status": "Matched",
            "details": {
                "editdistance": 0,
                "expected": "36296352",
                "actual": "36296352",
                "key_confidence": 95.16634368896484,
                "value_confidence": 95.16634368896484
            }
            },
            "fullNames": {
            "status": "Matched",
            "details": {
                "editdistance": 0,
                "expected": "JOEL MUUO",
                "actual": "JOEL MUUO",
                "key_confidence": 94.73348236083984,
                "value_confidence": 94.73348236083984
            }
            },
            "dateOfBirth": {
            "status": "Matched",
            "details": {
                "editdistance": 0,
                "expected": "30-08-1998",
                "actual": "1998-08-30",
                "key_confidence": 95.38103485107422,
                "value_confidence": 95.38103485107422
            }
            },
            "dateOfIssue": {
            "status": "Not provided",
            "details": null
            },
            "gender": {
            "status": "Not provided",
            "details": null
            },
            "districtOfBirth": {
            "status": "Not provided",
            "details": null
            },
            "placeOfIssue": {
            "status": "Not provided",
            "details": null
            }
        }
    
    print(rate(results))