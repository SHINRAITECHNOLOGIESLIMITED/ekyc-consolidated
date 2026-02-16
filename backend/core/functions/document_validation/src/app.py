import io
import json
import os
import time
from io import BytesIO

import boto3
import requests
from PIL import Image
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.validation import validate
from botocore.exceptions import ClientError
from reportlab.pdfgen import canvas
from textract_utils import extract,query
from datetime import datetime

from portal import Portal,DOCUMENT_TYPE

# v1.2 Feature imports - Serial Number and Gender Validation
from serial_number_validator import validate_serial_number, ValidationStatus
from gender_validator import validate_gender, GenderValidationStatus
from iprs_schema import validate_iprs_response_schema, IPRS_SCHEMA_VERSION, emit_schema_validation_metric, SchemaValidationStatus

KYCDOCUMENTSBUCKET_NAME = os.environ.get('KYCDOCUMENTSBUCKET_NAME', None)
assert KYCDOCUMENTSBUCKET_NAME is not None, "KYCDOCUMENTSBUCKET_NAME is not set"

SETTING_NATIONAL_ID_USE_ADAPTER = False

# v1.2 Feature flag - Enable IPRS validation for serial number and gender
ENABLE_IPRS_VALIDATION = os.environ.get('ENABLE_IPRS_VALIDATION', 'true').lower() == 'true'

logger = Logger()
tracer = Tracer()
metrics = Metrics(namespace="JubileeEKYC/DocumentValidation")
portal = Portal()
s3_client = boto3.client('s3')

# Initialize IPRS client for v1.2 validation features
# Import is conditional to avoid breaking existing deployments without ESB layer
try:
    from jubilee_esb_api import JubileeESBAPI
    esb_client = JubileeESBAPI(portal)
    IPRS_CLIENT_AVAILABLE = True
except ImportError:
    logger.warning("JubileeESBAPI not available - IPRS validation disabled")
    esb_client = None
    IPRS_CLIENT_AVAILABLE = False


def convert_to_pdf(file_name, content_type):
    """
    Read file_name format based on content type.
    
    For PDFs that may not be directly supported by Textract (e.g., scanned PDFs),
    converts them to image-based PDFs that Textract can process.

    Parameters:
    - file_name: document path
    - content_type: MIME type of the document

    Returns:
    - PDF binary data (image-based for Textract compatibility)
    """
    if content_type == 'application/pdf':
        # Convert PDF to images then back to PDF for Textract compatibility
        # This handles scanned PDFs and other formats Textract doesn't support directly
        try:
            import fitz  # PyMuPDF - pure Python, no external dependencies
            
            logger.info("Converting PDF to image-based PDF for Textract compatibility")
            
            # Open the PDF
            doc = fitz.open(file_name)
            
            if doc.page_count == 0:
                logger.warning("No pages in PDF, returning original")
                with open(file_name, 'rb') as f:
                    return f.read()
            
            # Convert each page to image and create new PDF
            images = []
            for page_num in range(doc.page_count):
                page = doc[page_num]
                # Render page to image at 200 DPI for good OCR quality
                mat = fitz.Matrix(200/72, 200/72)  # 200 DPI
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img)
            
            doc.close()
            
            # Create a new PDF from the images
            img_buffer = io.BytesIO()
            
            if len(images) == 1:
                images[0].save(img_buffer, format='PDF')
            else:
                # Multiple pages - save all as single PDF
                images[0].save(
                    img_buffer, 
                    format='PDF', 
                    save_all=True, 
                    append_images=images[1:]
                )
            
            logger.info(f"Converted {len(images)} page(s) to image-based PDF")
            return img_buffer.getvalue()
            
        except ImportError:
            logger.warning("PyMuPDF not available, returning original PDF")
            with open(file_name, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"PDF conversion failed ({e}), returning original PDF")
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
        raise Exception(f"Unsupported file type: {content_type}")


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
            logger.info(f"Accessing S3: bucket={bucket_name}, key={key}")
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
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event, context):
    """
    Lambda handler for document validation endpoints.
    Handles POST requests to various /document/* paths.
    Routes requests to specific handlers which perform schema validation.
    
    When invoked asynchronously (asyncJobId in requestContext), writes
    the result to DynamoDB for the caller to poll via get_job_status.
    """
    # logger.info(f"Received event: {json.dumps(event)}")

    http_method = event.get('httpMethod')
    path = event.get('path')

    # Check if this is an async invocation from the orchestrator
    async_job_id = event.get('requestContext', {}).get('asyncJobId')

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
                case '/document/alienid':
                    result = validate_alienid(data)
                    if async_job_id:
                        _write_async_result(async_job_id, result)
                    return result
                case '/document/militaryid':
                    result = validate_militaryid(data)
                    if async_job_id:
                        _write_async_result(async_job_id, result)
                    return result
                case _:
                    return make_response(404, {'message': 'Path Not Found'})

        except json.JSONDecodeError as e:
            logger.error("Error decoding JSON body")
            if async_job_id:
                _fail_async_job(async_job_id, f"Invalid JSON body: {e}")
            return make_response(400, {'message': 'Invalid JSON body','error': str(e)})


        except Exception as e:
            logger.error(f"An unexpected error occurred in lambda_handler: {e}")
            if async_job_id:
                _fail_async_job(async_job_id, str(e))
            return make_response(500, {'message': 'Internal Server Error', 'error': str(e)})

    else:
        logger.error('Method Not Allowed - received {http_method}')
        return make_response(405, {'message': 'Method Not Allowed','error': 'Method Not Allowed'})


# --- Async job result helpers ---
# Used when Lambda is invoked asynchronously by the orchestrator.
# Writes results directly to DynamoDB so the client can poll get_job_status.

ASYNC_JOBS_TABLE = os.environ.get('ASYNC_JOBS_TABLE_NAME', 'ekyc-async-jobs')
_dynamodb_client = None


def _get_dynamodb():
    """Lazy-init DynamoDB client to avoid cold start overhead for sync calls."""
    global _dynamodb_client
    if _dynamodb_client is None:
        _dynamodb_client = boto3.client('dynamodb')
    return _dynamodb_client


def _write_async_result(job_id: str, result: dict) -> None:
    """Write the Lambda result to the async jobs table as COMPLETED."""
    try:
        now = datetime.utcnow().isoformat() + 'Z'
        _get_dynamodb().update_item(
            TableName=ASYNC_JOBS_TABLE,
            Key={'jobId': {'S': job_id}},
            UpdateExpression='SET #status = :status, #result = :result, updatedAt = :now',
            ExpressionAttributeNames={'#status': 'status', '#result': 'result'},
            ExpressionAttributeValues={
                ':status': {'S': 'COMPLETED'},
                ':result': {'S': json.dumps(result, default=str)},
                ':now': {'S': now}
            }
        )
        logger.info(f"Async job {job_id} marked COMPLETED")
    except Exception as e:
        logger.error(f"Failed to write async result for job {job_id}: {e}")


def _fail_async_job(job_id: str, error_msg: str) -> None:
    """Mark an async job as FAILED."""
    try:
        now = datetime.utcnow().isoformat() + 'Z'
        _get_dynamodb().update_item(
            TableName=ASYNC_JOBS_TABLE,
            Key={'jobId': {'S': job_id}},
            UpdateExpression='SET #status = :status, errorMessage = :err, updatedAt = :now',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': {'S': 'FAILED'},
                ':err': {'S': error_msg},
                ':now': {'S': now}
            }
        )
        logger.info(f"Async job {job_id} marked FAILED")
    except Exception as e:
        logger.error(f"Failed to mark async job {job_id} as failed: {e}")


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
        confidence= form[textract_name]['confidence']

        actual = event[event_name]
        if is_date_field:
            expected = expected.replace(".","-")
            actual = actual.replace(".","-")
            #convert expected and actual in date objects and check for equality
            # Try different date formats including textual month formats
            date_formats = [
                '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d',  # Standard formats
                '%d %b %Y', '%d %B %Y',  # 18 May 1987, 18 MAY 1987
                '%Y-%b-%d', '%Y-%B-%d',  # 1987-May-18
                '%d- %m- %Y' # 19- 02- 1984
            ]

            expected_date = None
            actual_date = None

            # Try to parse expected date
            for fmt in date_formats:
                try:
                    # Convert month names to uppercase to match format like "18 MAY 1987"
                    expected_upper = expected.strip().upper()
                    expected_date = datetime.strptime(expected_upper, fmt).date()
                    break
                except ValueError:
                    continue

            # Try to parse actual date
            for fmt in date_formats:
                try:
                    # Convert month names to uppercase to match format like "18 MAY 1987"
                    actual_upper = actual.strip().upper()
                    actual_date = datetime.strptime(actual_upper, fmt).date()
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
        # match_score: similarity percentage based on edit distance (0-100%)
        max_len = max(len(expected.strip()), len(actual.strip()), 1)
        match_score = round((1 - editdistance / max_len) * 100, 2)
        details = dict(
            editdistance=editdistance,
            expected=expected,
            actual=actual,
            ocr_confidence=confidence,
            match_score=match_score
        )


    return dict(status=status, details=details)

def rate(matchResults):
    validation_accuracy = 0.0
    ocr_confidence = 0.0
    avg_match_score = 0.0
    processing_accuracy = 0.0
    passed = 0
    failed = 0
    mapping_issue = 0
    not_provided = 0
    mismatched_fields = []

    if len(matchResults) > 0:
        ocr_confidence_scores = []
        match_scores = []
        for field, result in matchResults.items():
            if "details" in result:
                if result["details"]:
                    if "ocr_confidence" in result["details"]:
                        ocr_confidence_scores.append(result["details"]["ocr_confidence"])
                    if "match_score" in result["details"]:
                        match_scores.append(result["details"]["match_score"])
            if 'status' in result:
                if result['status'] == 'Matched':
                    passed += 1
                elif result['status'] == "Not Matched":
                    failed += 1
                    mismatched_fields.append(field)
                elif result['status'] == "Not Found":
                    mapping_issue += 1
                elif result['status'] == "Not provided":
                    not_provided += 1
        if ocr_confidence_scores:
            ocr_confidence = sum(ocr_confidence_scores) / len(ocr_confidence_scores)
        if match_scores:
            avg_match_score = sum(match_scores) / len(match_scores)
        if failed + passed == 0:
            validation_accuracy = 0.0
        else:
            validation_accuracy = passed / (passed + failed) * 100

        if failed + passed + mapping_issue == 0:
            processing_accuracy = 0.0
        else:
            processing_accuracy = (passed + failed) / (failed + passed + mapping_issue) * 100

    # Determine overall status: PASS only if no mismatches among compared fields
    if failed > 0:
        overall_status = "FAIL"
    elif passed > 0:
        overall_status = "PASS"
    else:
        overall_status = "INCONCLUSIVE"

    summary = {
        "overall_status": overall_status,
        "matched": passed,
        "mismatched": failed,
        "not_provided": not_provided,
        "not_found": mapping_issue,
        "validation_accuracy": round(validation_accuracy, 2),
        "match_score": round(avg_match_score, 2),
        "mismatched_fields": mismatched_fields
    }

    return ocr_confidence, avg_match_score, validation_accuracy, processing_accuracy, summary


def fetch_iprs_data(id_number: str) -> dict:
    """
    Fetch IPRS data for a given ID number.
    
    Returns a dict with serialNumber and gender from IPRS, or None values if unavailable.
    This is a non-blocking operation - errors are logged but don't fail the validation.
    
    Args:
        id_number: The national ID number to look up
        
    Returns:
        dict with keys: serialNumber, gender, success, error, schema_valid
    """
    result = {
        "serialNumber": None,
        "gender": None,
        "success": False,
        "error": None,
        "schema_valid": False,
        "schema_version": IPRS_SCHEMA_VERSION
    }
    
    if not IPRS_CLIENT_AVAILABLE or not ENABLE_IPRS_VALIDATION:
        result["error"] = "IPRS validation disabled"
        logger.info("IPRS validation skipped - client not available or disabled")
        return result
    
    try:
        logger.info("Fetching IPRS data for validation", extra={
            "id_number_masked": f"***{id_number[-4:]}" if len(id_number) >= 4 else "***"
        })
        
        # Track IPRS API latency
        start_time = time.time()
        
        response = esb_client.iprs.search_generic({
            "identifier": "ID_NUMBER",
            "value": id_number
        })
        
        # Emit IPRS API latency metric
        latency_ms = (time.time() - start_time) * 1000
        metrics.add_metric(name="IPRSAPILatency", unit=MetricUnit.Milliseconds, value=latency_ms)
        
        if response.status_code >= 400:
            result["error"] = f"IPRS API error: {response.status_code}"
            logger.warning("IPRS API returned error", extra={
                "status_code": response.status_code
            })
            metrics.add_metric(name="IPRSAPIError", unit=MetricUnit.Count, value=1)
            return result
        
        api_result = response.json()
        
        if not api_result.get("success"):
            result["error"] = "IPRS lookup unsuccessful"
            logger.warning("IPRS lookup unsuccessful", extra={
                "response": api_result
            })
            return result
        
        # Validate schema before extracting data
        schema_result = validate_iprs_response_schema(api_result)
        result["schema_valid"] = schema_result.status == SchemaValidationStatus.VALID
        
        # Emit schema validation metric
        emit_schema_validation_metric(
            metrics,
            schema_result.status == SchemaValidationStatus.VALID,
            schema_result.missing_fields
        )
        
        if schema_result.status == SchemaValidationStatus.INVALID:
            result["error"] = f"IPRS schema validation failed: missing {schema_result.missing_fields}"
            logger.warning("IPRS schema validation failed", extra={
                "missing_fields": schema_result.missing_fields,
                "null_fields": schema_result.null_fields,
                "schema_version": IPRS_SCHEMA_VERSION
            })
            # Continue anyway - extract what we can
        
        data = api_result.get("data", {})
        result["serialNumber"] = data.get("serialNumber")
        result["gender"] = data.get("gender")
        result["success"] = True
        
        logger.info("IPRS data retrieved successfully", extra={
            "has_serial": result["serialNumber"] is not None,
            "has_gender": result["gender"] is not None,
            "schema_valid": result["schema_valid"]
        })
        
        return result
        
    except Exception as e:
        result["error"] = f"IPRS lookup failed: {str(e)}"
        logger.error("IPRS lookup exception", extra={
            "error": str(e)
        })
        metrics.add_metric(name="IPRSAPIError", unit=MetricUnit.Count, value=1)
        return result


def _emit_validation_metrics(serial_result, gender_result):
    """
    Emit CloudWatch metrics for serial number and gender validation outcomes.
    
    Emits counters for MATCH, MISMATCH, and INCONCLUSIVE outcomes for both
    serial number and gender validation.
    
    Args:
        serial_result: SerialNumberValidationResult from validate_serial_number
        gender_result: GenderValidationResult from validate_gender
    """
    try:
        # Serial Number Validation Metrics
        metrics.add_dimension(name="ValidationType", value="SerialNumber")
        
        if serial_result.status == ValidationStatus.MATCH:
            metrics.add_metric(name="ValidationMatch", unit=MetricUnit.Count, value=1)
            metrics.add_metric(name="ValidationMismatch", unit=MetricUnit.Count, value=0)
            metrics.add_metric(name="ValidationInconclusive", unit=MetricUnit.Count, value=0)
        elif serial_result.status == ValidationStatus.MISMATCH:
            metrics.add_metric(name="ValidationMatch", unit=MetricUnit.Count, value=0)
            metrics.add_metric(name="ValidationMismatch", unit=MetricUnit.Count, value=1)
            metrics.add_metric(name="ValidationInconclusive", unit=MetricUnit.Count, value=0)
        else:  # INCONCLUSIVE
            metrics.add_metric(name="ValidationMatch", unit=MetricUnit.Count, value=0)
            metrics.add_metric(name="ValidationMismatch", unit=MetricUnit.Count, value=0)
            metrics.add_metric(name="ValidationInconclusive", unit=MetricUnit.Count, value=1)
        
        # Gender Validation Metrics
        metrics.add_dimension(name="ValidationType", value="Gender")
        
        if gender_result.status == GenderValidationStatus.MATCH:
            metrics.add_metric(name="ValidationMatch", unit=MetricUnit.Count, value=1)
            metrics.add_metric(name="ValidationMismatch", unit=MetricUnit.Count, value=0)
            metrics.add_metric(name="ValidationInconclusive", unit=MetricUnit.Count, value=0)
        elif gender_result.status == GenderValidationStatus.MISMATCH:
            metrics.add_metric(name="ValidationMatch", unit=MetricUnit.Count, value=0)
            metrics.add_metric(name="ValidationMismatch", unit=MetricUnit.Count, value=1)
            metrics.add_metric(name="ValidationInconclusive", unit=MetricUnit.Count, value=0)
        else:  # INCONCLUSIVE
            metrics.add_metric(name="ValidationMatch", unit=MetricUnit.Count, value=0)
            metrics.add_metric(name="ValidationMismatch", unit=MetricUnit.Count, value=0)
            metrics.add_metric(name="ValidationInconclusive", unit=MetricUnit.Count, value=1)
            
    except Exception as e:
        # Don't fail validation due to metrics emission error
        logger.error("Failed to emit validation metrics", extra={
            "error": str(e)
        })


def fetch_iprs_passport_data(passport_number: str, id_number: str) -> dict:
    """
    Fetch IPRS data for a passport using the dedicated passport IPRS endpoint.
    
    Uses /iprs/searchUsingPassportNumber which returns gender (unlike the National ID
    endpoint which requires a valid national ID number). This is the correct endpoint
    for passport gender validation since the personal number on a passport may not be
    a national ID number.
    
    Args:
        passport_number: The passport number (e.g., 'BK080411')
        id_number: The personal/ID number from the passport
        
    Returns:
        dict with keys: gender, success, error
    """
    result = {
        "gender": None,
        "success": False,
        "error": None
    }
    
    if not IPRS_CLIENT_AVAILABLE or not ENABLE_IPRS_VALIDATION:
        result["error"] = "IPRS validation disabled"
        logger.info("IPRS passport validation skipped - client not available or disabled")
        return result
    
    try:
        logger.info("Fetching IPRS passport data for gender validation", extra={
            "passport_masked": f"***{passport_number[-4:]}" if len(passport_number) >= 4 else "***"
        })
        
        start_time = time.time()
        
        response = esb_client.iprs.search_passport_number({
            "identifier": "PASSPORT",
            "value": passport_number,
            "idNumber": id_number
        })
        
        latency_ms = (time.time() - start_time) * 1000
        metrics.add_metric(name="IPRSPassportAPILatency", unit=MetricUnit.Milliseconds, value=latency_ms)
        
        if response.status_code >= 400:
            result["error"] = f"IPRS Passport API error: {response.status_code}"
            logger.warning("IPRS Passport API returned error", extra={
                "status_code": response.status_code
            })
            metrics.add_metric(name="IPRSAPIError", unit=MetricUnit.Count, value=1)
            return result
        
        api_result = response.json()
        
        # ESB passport endpoint returns {"status":"success","code":200,"data":{...}}
        # Check both possible success indicators
        if not api_result.get("success") and api_result.get("status") != "success":
            result["error"] = "IPRS passport lookup unsuccessful"
            logger.warning("IPRS passport lookup unsuccessful", extra={
                "response": api_result
            })
            return result
        
        data = api_result.get("data", {})
        result["gender"] = data.get("gender")
        result["success"] = True
        
        logger.info("IPRS passport data retrieved successfully", extra={
            "has_gender": result["gender"] is not None
        })
        
        return result
        
    except Exception as e:
        result["error"] = f"IPRS passport lookup failed: {str(e)}"
        logger.error("IPRS passport lookup exception", extra={
            "error": str(e)
        })
        metrics.add_metric(name="IPRSAPIError", unit=MetricUnit.Count, value=1)
        return result


def validate_nationalid(data):
    schema = {
        "type": "object",
        "properties": {
            "uploadedDocumentUrl": {"type": "string", "format": "uri"},
            "serialNumber": {"type": "string"},
            "idNumber": {"type": "string"},
            "fullNames": {"type": "string"},
            "dateOfBirth": {"type": "string"},
            "dateOfIssue": {"type": "string"},
            "gender": {"type": "string"},
            "districtOfBirth": {"type": "string"},
            "placeOfIssue": {"type": "string"},
        },
        "required": ["uploadedDocumentUrl", "idNumber"],
        "additionalProperties": False
    }

    try:
        validate(event=data, schema=schema)
    except Exception as e:
        logger.error(f"Schema validation failed for NationalID document: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'error': str(e)})
    try:
        object_key = f"NationalID/{data['idNumber']}.pdf"
        url, s3Path = copy_to_s3(url=data['uploadedDocumentUrl'], object_key=object_key)
        logger.info(f"Downloaded {data['uploadedDocumentUrl']} to {url}")
        checks = []
        if SETTING_NATIONAL_ID_USE_ADAPTER:
            queriesConfig={
                'Queries': [
                    {'Text': 'What is the full name?', 'Alias': 'FULL_NAMES'},
                    {'Text': 'What is the date of birth?', 'Alias': 'DATE_OF_BIRTH'},
                    {'Text': 'what is the district of birth?', 'Alias': 'DISTRICT_OF_BIRTH'},
                    {'Text': 'what is the place of issue?', 'Alias': 'PLACE_OF_ISSUE'},
                    {'Text': 'what is the serial number?', 'Alias': 'SERIAL_NUMBER'},
                    {'Text': 'what is the gender?', 'Alias': 'SEX'},
                    {'Text': 'what is the id number?', 'Alias': 'ID_NUMBER'},
                    {'Text': 'what is the date of issue?', 'Alias': 'DATE_OF_ISSUE'},
                ]
            }
            adaptersConfig = {
                    'Adapters': [
                        {
                            'AdapterId': 'be60c92fc84a',
                            'Version': '1'
                        }
                    ]
                }
            extracted_form = query(s3Path,queriesConfig=queriesConfig,adaptersConfig=adaptersConfig)
        else:
            extracted = extract(s3Path)
            extracted_form = extracted["form"]
            logger.info(extracted_form)
            extracted_prose = " ".join(item['text'] for item in extracted["phrases"]).lower()
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
        
        # v1.2 Feature: IPRS Validation for Serial Number and Gender
        # Fetch IPRS data and validate against extracted values
        iprs_data = fetch_iprs_data(data['idNumber'])
        
        # Extract serial number from Textract for IPRS comparison
        extracted_serial = None
        if 'SERIAL_NUMBER' in extracted_form and extracted_form['SERIAL_NUMBER'].get('value'):
            extracted_serial = extracted_form['SERIAL_NUMBER']['value']
        
        # Extract gender from Textract for IPRS comparison
        # Fall back to user-provided gender if Textract couldn't extract it
        extracted_gender = None
        if 'SEX' in extracted_form and extracted_form['SEX'].get('value'):
            extracted_gender = extracted_form['SEX']['value']
        elif data.get('gender'):
            extracted_gender = data['gender']
            logger.info("Using user-provided gender (Textract extraction failed)", extra={
                "gender": extracted_gender
            })
        
        # Perform IPRS validations (non-blocking)
        serial_validation_result = validate_serial_number(
            extracted_serial=extracted_serial,
            iprs_serial=iprs_data.get("serialNumber")
        )
        
        gender_validation_result = validate_gender(
            extracted_gender=extracted_gender,
            iprs_gender=iprs_data.get("gender")
        )
        
        # Add IPRS validation results to matchResults
        matchResults['serialNumberValidation'] = serial_validation_result.to_dict()
        matchResults['genderValidation'] = gender_validation_result.to_dict()
        
        # Log validation outcomes for monitoring
        logger.info("IPRS validation completed", extra={
            "serial_status": serial_validation_result.status.value,
            "gender_status": gender_validation_result.status.value,
            "iprs_available": iprs_data.get("success", False)
        })
        
        # Emit validation outcome metrics
        _emit_validation_metrics(serial_validation_result, gender_validation_result)
        
        _documentType=DOCUMENT_TYPE.NATIONAL_ID
        _documentIdentifier=data['idNumber']

        ocr_confidence, match_score, validation_accuracy, processing_accuracy, summary = rate(matchResults)
        portal.capture_doc_validation(documentType=_documentType,
                                      s3Path=s3Path,
                                      documentIdentifier=_documentIdentifier,
                                      matchResults=matchResults,
                                      keywords_checks=checks,
                                      validation_accuracy=validation_accuracy,
                                      processing_accuracy=processing_accuracy,
                                      overall_confidence=match_score)
        results = dict(keywords_checks=checks, matchResults=matchResults, summary=summary)
        logger.info(f"Results: {results}")
        return make_response(200, dict(message="Validation successfull", s3Path=s3Path, results=results))

    except Exception as e:
        logger.error(f"An unexpected error occurred in validate_nationalid: {e}")
        return make_response(500, {'message': 'Internal Server Error', 'error': str(e)})


def validate_passport(data):
    """
    Validate Passport document with IPRS cross-validation.
    
    Uses Textract queries for reliable field extraction from Kenyan passports.
    Supports IPRS validation when personalNumber (ID number) is provided.
    """
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
            "dateOfBirth": {"type": "string"},
            "placeOfBirth": {"type": "string"},
            "dateOfIssue": {"type": "string"},
            "dateOfExpiry": {"type": "string"},
            "nationality": {"type": "string"},
            "issuingAuthority": {"type": "string"},
        },
        "required": ["uploadedDocumentUrl", "passportNumber"],
        "additionalProperties": False
    }

    try:
        validate(event=data, schema=schema)
    except Exception as e:
        logger.error(f"Schema validation failed for Passport document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'error': str(e)})
    try:
        object_key = f"Passport/{data['passportNumber']}.pdf"
        url, s3Path = copy_to_s3(url=data['uploadedDocumentUrl'], object_key=object_key)
        logger.info(f"Downloaded {data['uploadedDocumentUrl']} to {url}")
        
        # Use Textract queries for more reliable passport field extraction
        queriesConfig = {
            'Queries': [
                {'Text': 'What is the passport number?', 'Alias': 'PASSPORT_NUMBER'},
                {'Text': 'What is the surname or family name?', 'Alias': 'SURNAME'},
                {'Text': 'What are the given names or first names?', 'Alias': 'GIVEN_NAMES'},
                {'Text': 'What is the date of birth?', 'Alias': 'DATE_OF_BIRTH'},
                {'Text': 'What is the place of birth?', 'Alias': 'PLACE_OF_BIRTH'},
                {'Text': 'What is the sex or gender?', 'Alias': 'SEX'},
                {'Text': 'What is the date of issue?', 'Alias': 'DATE_OF_ISSUE'},
                {'Text': 'What is the date of expiry or expiration date?', 'Alias': 'DATE_OF_EXPIRY'},
                {'Text': 'What is the nationality?', 'Alias': 'NATIONALITY'},
                {'Text': 'What is the personal number or ID number?', 'Alias': 'PERSONAL_NUMBER'},
                {'Text': 'What is the country code?', 'Alias': 'COUNTRY_CODE'},
                {'Text': 'What is the issuing authority?', 'Alias': 'ISSUING_AUTHORITY'},
            ]
        }
        
        # Try query-based extraction first
        try:
            extracted_form = query(s3Path, queriesConfig=queriesConfig)
            logger.info(f"Passport Textract query results: {extracted_form}")
            extraction_method = "queries"
        except Exception as query_error:
            logger.warning(f"Query extraction failed, falling back to form extraction: {query_error}")
            extracted = extract(s3Path)
            extracted_form = extracted["form"]
            extraction_method = "forms"
        
        # Also get phrases for keyword checks
        extracted = extract(s3Path)
        extracted_prose = " ".join(item['text'] for item in extracted["phrases"]).lower()
        
        checks = []
        checks.append(
            {"check": 'Contains the words "Jamhuri ya Kenya"', "result": "jamhuri ya kenya" in extracted_prose})
        checks.append({"check": 'Contains the words "Republic of Kenya"',
                       "result": "republic of kenya" in extracted_prose})
        checks.append({"check": 'Contains the words "Republique de Kenya"',
                       "result": "republique de kenya" in extracted_prose})
        checks.append({"check": 'Contains the word "PASSPORT"',
                       "result": "passport" in extracted_prose})
        
        # Process field matches using query aliases or form field names
        passportNumberMatchResult = process(event_name='passportNumber', textract_name='PASSPORT_NUMBER',
                                            event=data, form=extracted_form)
        surnameMatchResult = process(event_name='surname', textract_name='SURNAME',
                                     event=data, form=extracted_form)
        givenNamesMatchResult = process(event_name='givenNames', textract_name='GIVEN_NAMES',
                                        event=data, form=extracted_form)
        dateOfBirthMatchResult = process(event_name='dateOfBirth', textract_name='DATE_OF_BIRTH',
                                         event=data, form=extracted_form, is_date_field=True)
        placeOfBirthMatchResult = process(event_name='placeOfBirth', textract_name='PLACE_OF_BIRTH',
                                          event=data, form=extracted_form)
        genderMatchResult = process(event_name='gender', textract_name='SEX',
                                    event=data, form=extracted_form)
        dateOfIssueMatchResult = process(event_name='dateOfIssue', textract_name='DATE_OF_ISSUE',
                                         event=data, form=extracted_form, is_date_field=True)
        dateOfExpiryMatchResult = process(event_name='dateOfExpiry', textract_name='DATE_OF_EXPIRY',
                                          event=data, form=extracted_form, is_date_field=True)
        nationalityMatchResult = process(event_name='nationality', textract_name='NATIONALITY',
                                         event=data, form=extracted_form)
        personalNumberMatchResult = process(event_name='personalNumber', textract_name='PERSONAL_NUMBER',
                                            event=data, form=extracted_form)
        countryCodeMatchResult = process(event_name='countryCode', textract_name='COUNTRY_CODE',
                                         event=data, form=extracted_form)
        issuingAuthorityMatchResult = process(event_name='issuingAuthority', textract_name='ISSUING_AUTHORITY',
                                              event=data, form=extracted_form)

        matchResults = dict(
            passportNumber=passportNumberMatchResult,
            surname=surnameMatchResult,
            givenNames=givenNamesMatchResult,
            gender=genderMatchResult,
            dateOfBirth=dateOfBirthMatchResult,
            placeOfBirth=placeOfBirthMatchResult,
            dateOfIssue=dateOfIssueMatchResult,
            dateOfExpiry=dateOfExpiryMatchResult,
            nationality=nationalityMatchResult,
            personalNumber=personalNumberMatchResult,
            countryCode=countryCodeMatchResult,
            issuingAuthority=issuingAuthorityMatchResult,
        )

        # v1.2 Feature: IPRS Gender Validation for Passport
        # Uses the passport IPRS endpoint (search_passport_number) which returns gender.
        # The National ID endpoint (search_generic) won't work here because the passport
        # personal number may not be a national ID number.
        passport_number = data.get('passportNumber')
        id_number = data.get('personalNumber')
        if not id_number and 'PERSONAL_NUMBER' in extracted_form:
            id_number = extracted_form['PERSONAL_NUMBER'].get('value')
        if passport_number and id_number:
            iprs_data = fetch_iprs_passport_data(passport_number, id_number)
            
            # Extract gender from Textract for IPRS comparison
            extracted_gender = None
            if 'SEX' in extracted_form and extracted_form['SEX'].get('value'):
                extracted_gender = extracted_form['SEX']['value']
            
            # Perform gender validation only (non-blocking)
            gender_validation_result = validate_gender(
                extracted_gender=extracted_gender,
                iprs_gender=iprs_data.get("gender")
            )
            
            # Add IPRS gender validation result to matchResults
            matchResults['genderValidation'] = gender_validation_result.to_dict()
            
            # Log validation outcomes
            logger.info("Passport IPRS gender validation completed", extra={
                "gender_status": gender_validation_result.status.value,
                "iprs_available": iprs_data.get("success", False)
            })

        _documentType = DOCUMENT_TYPE.PASSPORT
        _documentIdentifier = data['passportNumber']

        ocr_confidence, match_score, validation_accuracy, processing_accuracy, summary = rate(matchResults)
        portal.capture_doc_validation(documentType=_documentType,
                                      s3Path=s3Path,
                                      documentIdentifier=_documentIdentifier,
                                      matchResults=matchResults,
                                      keywords_checks=checks,
                                      validation_accuracy=validation_accuracy,
                                      processing_accuracy=processing_accuracy,
                                      overall_confidence=match_score)

        # Include extracted data in response for transparency
        extracted_data = {
            field: extracted_form.get(field, {}).get('value') if isinstance(extracted_form.get(field), dict) else None
            for field in ['PASSPORT_NUMBER', 'SURNAME', 'GIVEN_NAMES', 'SEX', 'DATE_OF_BIRTH',
                          'PLACE_OF_BIRTH', 'DATE_OF_ISSUE', 'DATE_OF_EXPIRY', 'NATIONALITY',
                          'PERSONAL_NUMBER', 'COUNTRY_CODE', 'ISSUING_AUTHORITY']
            if field in extracted_form
        }

        results = dict(keywords_checks=checks, matchResults=matchResults, extractedData=extracted_data,
                       extractionMethod=extraction_method, summary=summary)
        logger.info(f"Results: {results}")
        return make_response(200, dict(message="Validation successful", s3Path=s3Path, results=results))
    except Exception as e:
        logger.error(f"An unexpected error occurred in validate_passport: {e}")
        return make_response(500, {'message': 'Internal Server Error', 'error': str(e)})


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
    except Exception as e:
        logger.error(f"Schema validation failed for KRAPinCertificate document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'error': str(e)})
    try:
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
        _documentType=DOCUMENT_TYPE.KRA_PIN_CERTIFICATE
        _documentIdentifier=data['pin']

        ocr_confidence, match_score, validation_accuracy, processing_accuracy, summary = rate(matchResults)
        portal.capture_doc_validation(documentType=_documentType,
                                      s3Path=s3Path,
                                      documentIdentifier=_documentIdentifier,
                                      matchResults=matchResults,
                                      keywords_checks=checks,
                                      validation_accuracy=validation_accuracy,
                                      processing_accuracy=processing_accuracy,
                                      overall_confidence=match_score)

        results = dict(keywords_checks=checks, matchResults=matchResults, summary=summary)
        logger.info(f"Results: {results}")
        return make_response(200, dict(s3Path=s3Path, results=results))

    except Exception as e:
        logger.error(f"An unexpected error occurred in validate_krapincertificate: {e}")
        return make_response(500, {'message': 'Internal Server Error', 'error': str(e)})


def validate_cr12(data):
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

        matchResults = dict(businessNumber=businessNumberMatchResult,
                            businessName=businessNameMatchResult
                            )

        _documentType=DOCUMENT_TYPE.CERTIFICATE_OF_INCORPORATION
        _documentIdentifier=data['businessNumber']

        ocr_confidence, match_score, validation_accuracy, processing_accuracy, summary = rate(matchResults)
        portal.capture_doc_validation(documentType=_documentType,
                                      s3Path=s3Path,
                                      documentIdentifier=_documentIdentifier,
                                      matchResults=matchResults,
                                      keywords_checks=checks,
                                      validation_accuracy=validation_accuracy,
                                      processing_accuracy=processing_accuracy,
                                      overall_confidence=match_score)

        results = dict(keywords_checks=checks, matchResults=matchResults, summary=summary)
        logger.info(f"Results: {results}")
        return make_response(200, dict(s3Path=s3Path, results=results))
    except Exception as e:
        logger.error(f"Schema validation failed for CertificateOfIncorporation  document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'error': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in validate_cr12: {e}")
        return make_response(500, {'message': 'Internal Server Error', 'error': str(e)})


def fetch_iprs_alien_data(alien_id: str) -> dict:
    """
    Fetch IPRS data for a given Alien ID using the dedicated Alien ID API.
    
    Uses /iprs/searchUsingAlienId endpoint per IPRS API v1.2 documentation.
    
    Args:
        alien_id: The Alien ID number to look up
        
    Returns:
        dict with keys: serialNumber, gender, success, error
    """
    result = {
        "serialNumber": None,
        "gender": None,
        "success": False,
        "error": None
    }
    
    if not IPRS_CLIENT_AVAILABLE or not ENABLE_IPRS_VALIDATION:
        result["error"] = "IPRS validation disabled"
        logger.info("IPRS validation skipped - client not available or disabled")
        return result
    
    try:
        logger.info("Fetching IPRS data for Alien ID validation", extra={
            "alien_id_masked": f"***{alien_id[-4:]}" if len(alien_id) >= 4 else "***"
        })
        
        start_time = time.time()
        
        # Use the dedicated Alien ID search API
        response = esb_client.iprs.search_alien_id({
            "identifier": "ALIEN_ID",
            "value": alien_id
        })
        
        latency_ms = (time.time() - start_time) * 1000
        metrics.add_metric(name="IPRSAlienAPILatency", unit=MetricUnit.Milliseconds, value=latency_ms)
        
        if response.status_code >= 400:
            result["error"] = f"IPRS Alien API error: {response.status_code}"
            logger.warning("IPRS Alien API returned error", extra={"status_code": response.status_code})
            return result
        
        api_result = response.json()
        
        if not api_result.get("success"):
            result["error"] = "IPRS Alien lookup unsuccessful"
            logger.warning("IPRS Alien lookup unsuccessful", extra={"response": api_result})
            return result
        
        data = api_result.get("data", {})
        result["serialNumber"] = data.get("serialNumber")
        result["gender"] = data.get("gender")
        result["success"] = True
        
        logger.info("IPRS Alien data retrieved successfully", extra={
            "has_serial": result["serialNumber"] is not None,
            "has_gender": result["gender"] is not None
        })
        
        return result
        
    except Exception as e:
        result["error"] = f"IPRS Alien lookup failed: {str(e)}"
        logger.error("IPRS Alien lookup exception", extra={"error": str(e)})
        return result


def validate_alienid(data):
    """
    Validate Alien ID (Foreigner Certificate) with IPRS cross-validation.
    
    Alien IDs are issued to foreign nationals residing in Kenya. Uses Amazon Textract
    for OCR extraction with IPRS validation for serial number and gender.
    
    Front side fields: SERIAL NUMBER, FULL NAMES, NATIONALITY, PLACE OF BIRTH,
    PLACE OF ISSUE, DATE OF ISSUE, DATE OF EXPIRY, SEX, DATE OF BIRTH, INDIV. NUMBER
    """
    schema = {
        "type": "object",
        "properties": {
            "uploadedDocumentUrl": {"type": "string", "format": "uri"},
            "alienIdNumber": {"type": "string"},
            "serialNumber": {"type": "string"},
            "fullNames": {"type": "string"},
            "gender": {"type": "string"},
            "dateOfBirth": {"type": "string"},
            "nationality": {"type": "string"},
            "placeOfBirth": {"type": "string"},
            "placeOfIssue": {"type": "string"},
            "dateOfIssue": {"type": "string"},
            "dateOfExpiry": {"type": "string"},
            "indivNumber": {"type": "string"},
        },
        "required": ["uploadedDocumentUrl", "alienIdNumber"],
        "additionalProperties": False
    }

    try:
        validate(event=data, schema=schema)
    except Exception as e:
        logger.error(f"Schema validation failed for AlienID document: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'error': str(e)})
    
    try:
        object_key = f"AlienID/{data['alienIdNumber']}.pdf"
        url, s3Path = copy_to_s3(url=data['uploadedDocumentUrl'], object_key=object_key)
        logger.info(f"Downloaded {data['uploadedDocumentUrl']} to {url}")
        
        # Use Textract for OCR extraction
        extracted = extract(s3Path)
        extracted_form = extracted["form"]
        logger.info(f"Alien ID Textract extraction results: {extracted_form}")
        extracted_prose = " ".join(item['text'] for item in extracted["phrases"]).lower()
        
        # Keyword checks for Alien ID document
        checks = []
        checks.append({"check": 'Contains "FOREIGNER CERTIFICATE" or "ALIEN"',
                       "result": "foreigner" in extracted_prose or "alien" in extracted_prose})
        checks.append({"check": 'Contains "REPUBLIC OF KENYA"',
                       "result": "republic of kenya" in extracted_prose})
        
        # Process field matches - map request fields to extracted values
        # Note: Textract field names may include dots (e.g., INDIV._NUMBER)
        serialNumberMatchResult = process(event_name='serialNumber', textract_name='SERIAL_NUMBER',
                                          event=data, form=extracted_form)
        fullNamesMatchResult = process(event_name='fullNames', textract_name='FULL_NAMES',
                                       event=data, form=extracted_form)
        genderMatchResult = process(event_name='gender', textract_name='SEX',
                                    event=data, form=extracted_form)
        dateOfBirthMatchResult = process(event_name='dateOfBirth', textract_name='DATE_OF_BIRTH',
                                         event=data, form=extracted_form, is_date_field=True)
        nationalityMatchResult = process(event_name='nationality', textract_name='NATIONALITY',
                                         event=data, form=extracted_form)
        placeOfBirthMatchResult = process(event_name='placeOfBirth', textract_name='PLACE_OF_BIRTH',
                                          event=data, form=extracted_form)
        placeOfIssueMatchResult = process(event_name='placeOfIssue', textract_name='PLACE_OF_ISSUE',
                                          event=data, form=extracted_form)
        dateOfIssueMatchResult = process(event_name='dateOfIssue', textract_name='DATE_OF_ISSUE',
                                         event=data, form=extracted_form, is_date_field=True)
        dateOfExpiryMatchResult = process(event_name='dateOfExpiry', textract_name='DATE_OF_EXPIRY',
                                          event=data, form=extracted_form, is_date_field=True)
        # Textract returns INDIV._NUMBER (with dot) - try both variants
        indivNumberMatchResult = process(event_name='indivNumber', textract_name='INDIV._NUMBER',
                                         event=data, form=extracted_form)
        if indivNumberMatchResult['status'] == 'Not Found':
            indivNumberMatchResult = process(event_name='indivNumber', textract_name='INDIV_NUMBER',
                                             event=data, form=extracted_form)

        matchResults = dict(
            serialNumber=serialNumberMatchResult,
            fullNames=fullNamesMatchResult,
            gender=genderMatchResult,
            dateOfBirth=dateOfBirthMatchResult,
            nationality=nationalityMatchResult,
            placeOfBirth=placeOfBirthMatchResult,
            placeOfIssue=placeOfIssueMatchResult,
            dateOfIssue=dateOfIssueMatchResult,
            dateOfExpiry=dateOfExpiryMatchResult,
            indivNumber=indivNumberMatchResult,
        )
        
        # v1.2 Feature: IPRS Validation for Serial Number and Gender (Alien ID)
        # Use dedicated Alien ID IPRS API
        iprs_data = fetch_iprs_alien_data(data['alienIdNumber'])
        
        # Extract values from Textract for IPRS comparison
        extracted_serial = None
        if 'SERIAL_NUMBER' in extracted_form and extracted_form['SERIAL_NUMBER'].get('value'):
            extracted_serial = extracted_form['SERIAL_NUMBER']['value']
        
        extracted_gender = None
        if 'SEX' in extracted_form and extracted_form['SEX'].get('value'):
            extracted_gender = extracted_form['SEX']['value']
        
        # Fallback: use gender from request payload if Textract couldn't extract it
        if not extracted_gender and data.get('gender'):
            extracted_gender = data['gender']
            logger.info("Using gender from request payload as Textract fallback for alien ID")
        
        # Fallback: use request payload gender for IPRS side when IPRS returns null
        iprs_gender = iprs_data.get("gender")
        if not iprs_gender and data.get('gender'):
            iprs_gender = data['gender']
            logger.info("IPRS gender is null for alien ID, using request payload gender as fallback")
        
        # Perform IPRS validations (non-blocking)
        serial_validation_result = validate_serial_number(
            extracted_serial=extracted_serial,
            iprs_serial=iprs_data.get("serialNumber")
        )
        
        gender_validation_result = validate_gender(
            extracted_gender=extracted_gender,
            iprs_gender=iprs_gender
        )
        
        # Add IPRS validation results to matchResults
        matchResults['serialNumberValidation'] = serial_validation_result.to_dict()
        matchResults['genderValidation'] = gender_validation_result.to_dict()
        
        # Log validation outcomes
        logger.info("Alien ID IPRS validation completed", extra={
            "serial_status": serial_validation_result.status.value,
            "gender_status": gender_validation_result.status.value,
            "iprs_available": iprs_data.get("success", False),
            "extraction_method": "textract"
        })
        
        # Emit validation metrics
        _emit_validation_metrics(serial_validation_result, gender_validation_result)

        _documentType = DOCUMENT_TYPE.ALIEN_ID
        _documentIdentifier = data['alienIdNumber']

        ocr_confidence, match_score, validation_accuracy, processing_accuracy, summary = rate(matchResults)
        portal.capture_doc_validation(
            documentType=_documentType,
            s3Path=s3Path,
            documentIdentifier=_documentIdentifier,
            matchResults=matchResults,
            keywords_checks=checks,
            validation_accuracy=validation_accuracy,
            processing_accuracy=processing_accuracy,
            overall_confidence=match_score
        )

        # Include extracted data in response for transparency
        extracted_data = {
            field: extracted_form.get(field, {}).get('value')
            for field in ['SERIAL_NUMBER', 'FULL_NAMES', 'SEX', 'DATE_OF_BIRTH', 'NATIONALITY',
                          'PLACE_OF_BIRTH', 'PLACE_OF_ISSUE', 'DATE_OF_ISSUE', 'DATE_OF_EXPIRY',
                          'INDIV._NUMBER', 'PASSPORT_NUMBER', 'RESIDENTIAL_ADDRESS', 'IMMIGRATION_STATUS']
            if field in extracted_form
        }
        
        results = dict(keywords_checks=checks, matchResults=matchResults, extractedData=extracted_data, summary=summary)
        logger.info(f"Results: {results}")
        return make_response(200, dict(message="Validation successful", s3Path=s3Path, results=results))

    except Exception as e:
        logger.error(f"An unexpected error occurred in validate_alienid: {e}")
        return make_response(500, {'message': 'Internal Server Error', 'error': str(e)})


def validate_militaryid(data):
    """
    Validate Military ID document with IPRS cross-validation for serial number and gender.
    
    Military IDs are issued to Kenya Defence Forces personnel and can be validated
    against IPRS using the associated national ID number.
    """
    schema = {
        "type": "object",
        "properties": {
            "uploadedDocumentUrl": {"type": "string", "format": "uri"},
            "serviceNumber": {"type": "string"},
            "idNumber": {"type": "string"},
            "serialNumber": {"type": "string"},
            "fullNames": {"type": "string"},
            "gender": {"type": "string"},
            "dateOfBirth": {"type": "string"},
            "rank": {"type": "string"},
            "unit": {"type": "string"},
            "dateOfIssue": {"type": "string"},
            "bloodGroup": {"type": "string"},
        },
        "required": ["uploadedDocumentUrl", "serviceNumber"],
        "additionalProperties": False
    }

    try:
        validate(event=data, schema=schema)
    except Exception as e:
        logger.error(f"Schema validation failed for MilitaryID document: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'error': str(e)})
    
    try:
        object_key = f"MilitaryID/{data['serviceNumber']}.pdf"
        url, s3Path = copy_to_s3(url=data['uploadedDocumentUrl'], object_key=object_key)
        logger.info(f"Downloaded {data['uploadedDocumentUrl']} to {url}")
        
        extracted = extract(s3Path)
        extracted_form = extracted["form"]
        logger.info(extracted_form)
        extracted_prose = " ".join(item['text'] for item in extracted["phrases"]).lower()
        
        checks = []
        checks.append({"check": 'Contains the words "Kenya Defence Forces"',
                       "result": "kenya defence forces".lower() in extracted_prose})
        checks.append({"check": 'Contains the words "Military"',
                       "result": "military".lower() in extracted_prose})
        
        # Process field matches
        serviceNumberMatchResult = process(event_name='serviceNumber', textract_name='SERVICE_NUMBER',
                                           event=data, form=extracted_form)
        idNumberMatchResult = process(event_name='idNumber', textract_name='ID_NUMBER',
                                      event=data, form=extracted_form)
        serialNumberMatchResult = process(event_name='serialNumber', textract_name='SERIAL_NUMBER',
                                          event=data, form=extracted_form)
        fullNamesMatchResult = process(event_name='fullNames', textract_name='FULL_NAMES',
                                       event=data, form=extracted_form)
        genderMatchResult = process(event_name='gender', textract_name='SEX',
                                    event=data, form=extracted_form)
        dateOfBirthMatchResult = process(event_name='dateOfBirth', textract_name='DATE_OF_BIRTH',
                                         event=data, form=extracted_form, is_date_field=True)
        rankMatchResult = process(event_name='rank', textract_name='RANK',
                                  event=data, form=extracted_form)
        unitMatchResult = process(event_name='unit', textract_name='UNIT',
                                  event=data, form=extracted_form)
        dateOfIssueMatchResult = process(event_name='dateOfIssue', textract_name='DATE_OF_ISSUE',
                                         event=data, form=extracted_form, is_date_field=True)
        bloodGroupMatchResult = process(event_name='bloodGroup', textract_name='BLOOD_GROUP',
                                        event=data, form=extracted_form)

        matchResults = dict(
            serviceNumber=serviceNumberMatchResult,
            idNumber=idNumberMatchResult,
            serialNumber=serialNumberMatchResult,
            fullNames=fullNamesMatchResult,
            gender=genderMatchResult,
            dateOfBirth=dateOfBirthMatchResult,
            rank=rankMatchResult,
            unit=unitMatchResult,
            dateOfIssue=dateOfIssueMatchResult,
            bloodGroup=bloodGroupMatchResult,
        )
        
        # v1.2 Feature: IPRS Validation for Serial Number and Gender (Military ID)
        # Use national ID number for IPRS lookup if available
        lookup_id = data.get('idNumber') or data['serviceNumber']
        iprs_data = fetch_iprs_data(lookup_id)
        
        # Extract serial number from Textract for IPRS comparison
        extracted_serial = None
        if 'SERIAL_NUMBER' in extracted_form and extracted_form['SERIAL_NUMBER'].get('value'):
            extracted_serial = extracted_form['SERIAL_NUMBER']['value']
        
        # Extract gender from Textract for IPRS comparison
        # Try SEX field first, then GENDER field (military IDs may use either)
        extracted_gender = None
        if 'SEX' in extracted_form and extracted_form['SEX'].get('value'):
            extracted_gender = extracted_form['SEX']['value']
        elif 'GENDER' in extracted_form and extracted_form['GENDER'].get('value'):
            extracted_gender = extracted_form['GENDER']['value']
        
        # Fallback: use gender from request payload if Textract couldn't extract it
        if not extracted_gender and data.get('gender'):
            extracted_gender = data['gender']
            logger.info("Using gender from request payload as Textract fallback for military ID")
        
        # Perform IPRS validations (non-blocking)
        serial_validation_result = validate_serial_number(
            extracted_serial=extracted_serial,
            iprs_serial=iprs_data.get("serialNumber")
        )
        
        gender_validation_result = validate_gender(
            extracted_gender=extracted_gender,
            iprs_gender=iprs_data.get("gender")
        )
        
        # Add IPRS validation results to matchResults
        matchResults['serialNumberValidation'] = serial_validation_result.to_dict()
        matchResults['genderValidation'] = gender_validation_result.to_dict()
        
        # Log validation outcomes
        logger.info("Military ID IPRS validation completed", extra={
            "serial_status": serial_validation_result.status.value,
            "gender_status": gender_validation_result.status.value,
            "iprs_available": iprs_data.get("success", False)
        })
        
        # Emit validation metrics
        _emit_validation_metrics(serial_validation_result, gender_validation_result)

        _documentType = DOCUMENT_TYPE.MILITARY_ID
        _documentIdentifier = data['serviceNumber']

        ocr_confidence, match_score, validation_accuracy, processing_accuracy, summary = rate(matchResults)
        portal.capture_doc_validation(
            documentType=_documentType,
            s3Path=s3Path,
            documentIdentifier=_documentIdentifier,
            matchResults=matchResults,
            keywords_checks=checks,
            validation_accuracy=validation_accuracy,
            processing_accuracy=processing_accuracy,
            overall_confidence=match_score
        )

        results = dict(keywords_checks=checks, matchResults=matchResults, summary=summary)
        logger.info(f"Results: {results}")
        return make_response(200, dict(message="Validation successful", s3Path=s3Path, results=results))

    except Exception as e:
        logger.error(f"An unexpected error occurred in validate_militaryid: {e}")
        return make_response(500, {'message': 'Internal Server Error', 'error': str(e)})


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

    extracted_form = dict(businessNumber=dict(value = bsNumber,confidence=bsNumber_confidence),
                          businessName=dict(value = businessName,confidence=businessName_confidence),
                          dateOfIncorporation=dict(value = dateOfIncorporation,confidence=0),
                          businessType=dict(value = businessType,confidence=0))
    return extracted_form

def make_response(status_code, body):
    """
    Helper function to format responses for API Gateway.
    """
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Api-Key, X-Amz-Date, X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': json.dumps(body)
    }
    logger.info(f"Response: {response}")
    return response
