import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from io import BytesIO

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate
from aws_lambda_powertools.utilities.validation.exceptions import SchemaValidationError
from textract_utils import extract
import requests
import os
from portal import Portal
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image
import io
    
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
    
    #update function to convert using filename
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
    
        #if url is s3 ulr use s3_client to download the document
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
            #write to file
            with open(file_name, 'wb') as f:
                f.write(response.content)
            content_type = response.headers.get('Content-Type')
        #check if downloaded document is pdf - if not make it PDF
        
        try:
            binary = convert_to_pdf(file_name,content_type)
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
            data = json.loads(event.get('body', '{}'))
            logger.error(f"Request body: {data}")
            match path:
                case  '/document/nationalid-validation':
                    return handle_nationalid_document_validation(data)
                case   '/document/passport-validation':
                    return handle_passport_document_validation(data)
                case   '/document/kra-validation':
                    return handle_kra_document_validation(data)
                case   '/document/company-validation':
                    return handle_company_document_validation(data)
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

def handle_nationalid_document_validation(data):
    """
    Validates schema (defined inline and locally) and indicates not implemented for National ID document validation.
    """
    schema = {
        "type": "object",
        "properties": {
            "uploadedDocumentUrl": {"type": "string", "format": "uri"},
            "idNumber": {"type": "string"},
            "fullNames": {"type": "string"},
            "dateOfBirth": {"type": "string", "format": "date"}
        },
        "required": ["uploadedDocumentUrl", "idNumber", "fullNames", "dateOfBirth"],
        "additionalProperties": False
    }
    validate(schema=schema,event=data)

    try:
        #download document to local s3
        object_key = f"KenyanNationalIDs/{data['idNumber']}.pdf"
        url,s3Path = copy_to_s3(url=data['uploadedDocumentUrl'], object_key=object_key)
        logger.info(f"Downloaded {data['uploadedDocumentUrl']} to {url}")
        extractedData =  extract(s3Path)
        logger.info(f"Textracted {data['uploadedDocumentUrl']}")
        logger.info(extractedData)

        idnumberValid = False,"Not processed"
        namesValid = False,"Not processed"
        dobValid = False,"Not processed"

        #verify
        if 'ID_NUMBER' in extractedData:
            if extractedData['ID_NUMBER'] == data['idNumber']:
                idnumberValid = True,"Matched"
            else:
                idnumberValid = False,f"Mismatch - found {extractedData['ID_NUMBER']} expected {data['idNumber']}"
        else:
            idnumberValid = False,"ID Number field not found in the document"


        if 'DATE_OF_BIRTH' in extractedData:
            try:
                    extracted_dob = datetime.strptime(extractedData['DATE_OF_BIRTH'], "%d.%m.%Y").date()
                    input_dob = datetime.strptime(data['dateOfBirth'], "%Y-%m-%d").date()
                    if extracted_dob == input_dob:
                        dobValid = True, "Matched"
                    else:
                        dobValid = False, f"Mismatch - found {extracted_dob} expected {input_dob}"
            except Exception as e:
                    dobValid = False, f"Date parsing failed: {str(e)}"

        if 'FULL_NAMES' in extractedData:
            if extractedData['FULL_NAMES'].upper() == data['fullNames'].upper():
                namesValid = True,"Matched"
            else:
                namesValid = False,f"Mismatch - found {extractedData['FULL_NAMES']} expected {data['fullNames'] }"
        else:
            namesValid = False,"FullName field not found in the document"

        if dobValid[0] and idnumberValid[0] and namesValid[0]:
            status="Valid"
        else:
            status="Invalid"
        matchDetails = dict(idNumber = dict(valid=idnumberValid[0],reason=idnumberValid[1]),
                          names = dict(valid=namesValid[0],reason=namesValid[1]),
                          dob = dict(valid=dobValid[0],reason=dobValid[1]),)
        validation = dict(matchDetails=matchDetails,extractedData=extractedData,status=status)
        return make_response(200, validation)

    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for National ID document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in handle_nationalid_document_validation: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


def handle_passport_document_validation(data):
    """
    Validates schema (defined inline and locally) and indicates not implemented for Passport document validation.
    """
    schema = {
        "type": "object",
        "properties": {
            "uploadedDocumentUrl": {"type": "string", "format": "uri"},
            "passportNumber": {"type": "string"},
            "fullNames": {"type": "string"},
            "dateOfBirth": {"type": "string", "format": "date"}
        },
        "required": ["uploadedDocumentUrl", "passportNumber", "fullNames", "dateOfBirth"],
        "additionalProperties": False
    }
    validate(schema=schema,event=data)

    try:
        object_key = f"Passports/{data['passportNumber']}.pdf"
        url,s3Path = copy_to_s3(url=data['uploadedDocumentUrl'], object_key=object_key)
        
        logger.info(f"Downloaded {data['uploadedDocumentUrl']} to {url}")
        extractedData =  extract(s3Path)
        logger.info(f"Textracted {data['uploadedDocumentUrl']}")
        logger.info(extractedData)

        passportNumberValid = False,"Not processed"
        fullnamesValid = False,"Not processed"
        dobValid = False,"Not processed"

        #Verify PP
        if 'PASSPORT_NO_NAMBARI_YA_PAST_NO_DE_PASSEPORT' in extractedData:
            if extractedData['PASSPORT_NO_NAMBARI_YA_PAST_NO_DE_PASSEPORT'] == data['passportNumber']:
                passportNumberValid = True,"Matched"
            else:
                passportNumberValid = False,f"Mismatch - found {extractedData['PASSPORT_NO_NAMBARI_YA_PAST_NO_DE_PASSEPORT']} expected {data['passportNumber']}"
        else:
            passportNumberValid = False,"Passport Number field not found in the document"

        if 'GIVEN_NAMES/MAJINA_ALIYOPEWA_PRENOMS' in extractedData:
            if extractedData['GIVEN_NAMES/MAJINA_ALIYOPEWA_PRENOMS'].upper() == data['fullNames'].upper():
                fullnamesValid = True,"Matched"
            else:
                fullnamesValid = False,f"Mismatch - found {extractedData['GIVEN_NAMES/MAJINA_ALIYOPEWA_PRENOMS']} expected {data['fullNames'] }"
        else:
            fullnamesValid = False,"FullName field not found in the document"

        if 'DATE_OF_BIRTH/TAREHE_VA_KUZALIWA_DATE_DE_NAISSANCE' in extractedData:
            if extractedData['DATE_OF_BIRTH/TAREHE_VA_KUZALIWA_DATE_DE_NAISSANCE'] == data['dateOfBirth'] :
                dobValid = True,"Matched"
            else:
                dobValid = False,f"Mismatch - found {extractedData['DATE_OF_BIRTH/TAREHE_VA_KUZALIWA_DATE_DE_NAISSANCE']} expected {data['dateOfBirth'] }"
        else:
            dobValid = False,"Date of Birth field not found in the document"

        if dobValid[0] and passportNumberValid[0] and fullnamesValid[0]:
            status="Valid"
        else:
            status="Invalid"
        matchDetails = dict(passportNumber = dict(valid=passportNumberValid[0], reason=passportNumberValid[1]),
                          names = dict(valid=fullnamesValid[0], reason=fullnamesValid[1]),
                          dob = dict(valid=dobValid[0], reason=dobValid[1]),)
        validation = dict(matchDetails=matchDetails, extractedData=extractedData, status=status)
        return make_response(200, validation)

    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for Passport document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in handle_passport_document_validation: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


def handle_kra_document_validation(data):
    """
    Validates schema (defined inline and locally) and indicates not implemented for KRA document validation.
    """
    schema = {
        "type": "object",
        "properties": {
            "uploadedDocumentUrl": {"type": "string", "format": "uri"},
            "kraPin": {"type": "string"},
            "taxPayersName": {"type": "string"},
        },
        "required": ["uploadedDocumentUrl", "kraPin", "taxPayersName"],
        "additionalProperties": False
    }
    validate(schema=schema,event=data)

    try:
        object_key = f"KRAPinCertificate/{data['kraPin']}.pdf"
        url,s3Path = copy_to_s3(url=data['uploadedDocumentUrl'], object_key=object_key)
        logger.info(f"Downloaded {data['uploadedDocumentUrl']} to {url}")
        extractedData = extract(s3Path)
        logger.info(f"Textracted {data['uploadedDocumentUrl']}")
        logger.info(extractedData)

        krapinValid = False,"Not processed"
        taxPayersNameValid = False,"Not processed"

        # Verify KRA
        if 'PERSONAL_IDENTIFICATION_NUMBER' in extractedData:
            if extractedData['PERSONAL_IDENTIFICATION_NUMBER'] == data['kraPin']:
                krapinValid = True,"Matched"
            else:
                krapinValid = False,f"Mismatch - found {extractedData['PERSONAL_IDENTIFICATION_NUMBER']} expected {data['kraPin']}"
        else:
            krapinValid = False,"KRA PIN field not found in the document"

        if 'TAXPAYER_NAME' in extractedData:
            if extractedData['TAXPAYER_NAME'].upper() == data['taxPayersName'].upper():
                taxPayersNameValid = True,"Matched"
            else:
                taxPayersNameValid = False,f"Mismatch - found {extractedData['TAXPAYER_NAME']} expected {data['taxPayersName'] }"
        else:
            taxPayersNameValid = False,"taxPayersName field not found in the document"


        if krapinValid[0] and taxPayersNameValid[0]:
            status="Valid"

        else:
            status="Invalid"
        matchDetails = dict(kraPin = dict(valid=krapinValid[0], reason=krapinValid[1]),
                        names = dict(valid=taxPayersNameValid[0], reason=taxPayersNameValid[1]))
        validation = dict(matchDetails=matchDetails, extractedData=extractedData, status=status)
        return make_response(200, validation)

    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for KRA document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in handle_kra_document_validation: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


def handle_company_document_validation(data):
    """
    Validates schema (defined inline and locally) and indicates not implemented for Company document validation.
    """
    schema = {
        "type": "object",
        "properties": {
            "uploadedDocumentUrl": {"type": "string", "format": "uri"},
            "businessNumber": {"type": "string"},
            "businessName": {"type": "string"},
        },
        "required": ["uploadedDocumentUrl", "businessNumber"],
        "additionalProperties": False
    }
    validate(schema=schema,event=data)

    try:
        # download doc to local s3
        object_key = f"CR12/{data['businessNumber']}.pdf"
        url,s3Path = copy_to_s3(url=data['uploadedDocumentUrl'], object_key=object_key)
        logger.info(f"Downloaded {data['uploadedDocumentUrl']} to {url}")
        extractedData = extract(s3Path)

        logger.info(f"Textracted {data['uploadedDocumentUrl']}")
        
        # logger.info(extractedData)
        bsNoinValid = False,"Not processed"
        bsNameinValid = False,"Not processed"
        if 'TEXT_PHRASES' in extractedData:
            extractedData = extractedData['TEXT_PHRASES']
            logger.info(extractedData)

            if len(extractedData) >= 2:
                bsNumber = extractedData[1].replace("No.","").strip()
                if bsNumber == data['businessNumber']:
                    bsNoinValid = True,"Matched"
                else:
                    bsNoinValid = False,f"Mismatch - found {bsNumber} expected {data['businessNumber']}"
            else:
                bsNoinValid = False,"Not found"
            if len(extractedData) >= 5:
                companyName = extractedData[4].strip()
                if companyName.upper() == data['businessName'].upper():
                    bsNameinValid = True,"Matched"
                else:
                    bsNameinValid = False,f"Mismatch - found {companyName} expected {data['companyName']}"
            else:
                bsNameinValid = False,"Not found"
            
            
        else:
            bsNoinValid = False,"Could not read text data"
            bsNameinValid= False,"Could not read text data"

        if bsNoinValid[0]:
            status="Valid"
        else:
            status="Invalid"
        matchdetails = dict(businessNumber = dict(valid=bsNoinValid[0], reason=bsNoinValid[1]),name = dict(valid=bsNameinValid[0], reason=bsNameinValid[1]))
        validation = dict(matchdetails=matchdetails, extractedData=extractedData, status=status)
        return make_response(200, validation)

    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for Company document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in handle_company_document_validation: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


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