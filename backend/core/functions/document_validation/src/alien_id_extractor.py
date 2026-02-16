"""
Kenya Foreigner Certificate (Alien ID) Data Extractor
======================================================
Hybrid extraction using:
  1. Amazon Bedrock Claude Vision — primary structured extraction
  2. MRZ (Machine Readable Zone) parsing — cross-validation & fallback

Designed for real-time use (<10s) in AWS Lambda.
"""

import boto3
import base64
import json
import re
import logging
import io
import os
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Configuration
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-sonnet-4-20250514-v1:0')
BEDROCK_REGION = os.environ.get('AWS_REGION', 'eu-west-1')
MAX_TOKENS = 1024

# Extraction prompt for Claude Vision
EXTRACTION_PROMPT = """You are an expert document data extractor. Analyze this Republic of Kenya Foreigner Certificate (Alien ID card) image and extract ALL fields into structured JSON.

The card has a FRONT side and a BACK side. Extract every field you can see.

Return ONLY valid JSON with this exact structure (use null for fields not visible):
{
  "serial_number": "string — 9-digit number from SERIAL NUMBER field",
  "full_names": "string — complete name from FULL NAMES field, preserve original casing",
  "nationality": "string — from NATIONALITY field",
  "place_of_birth": "string — from PLACE OF BIRTH field",
  "place_of_issue": "string — from PLACE OF ISSUE field",
  "date_of_issue": "string — from DATE OF ISSUE field, format as DD.MM.YYYY",
  "date_of_expiry": "string — from DATE OF EXPIRY field, format as DD.MM.YYYY",
  "sex": "string — MALE or FEMALE from SEX field",
  "date_of_birth": "string — from DATE OF BIRTH field, format as DD.MM.YYYY",
  "indiv_number": "string — from INDIV. NUMBER field",
  "residential_address": "string — from RESIDENTIAL ADDRESS field on back",
  "immigration_status": "string — from IMMIGRATION STATUS field on back (e.g., KPR/0002672)",
  "r_number": "string — from R. NUMBER field on back",
  "passport_number": "string — from PASSPORT NUMBER field on back",
  "mrz_line_1": "string — first line of MRZ (Machine Readable Zone) on back, starts with ACKYA",
  "mrz_line_2": "string — second line of MRZ on back",
  "mrz_line_3": "string — third line of MRZ on back (contains name)"
}

Rules:
- Extract text EXACTLY as printed on the card
- Dates must be in DD.MM.YYYY format as shown on the card
- For MRZ lines, include ALL characters including < symbols
- If a field is not visible or unreadable, use null
- Return ONLY the JSON object, no markdown, no explanation"""


@dataclass
class AlienIDExtractionResult:
    """Extracted and validated Foreigner Certificate data."""
    
    # Source metadata
    source_file: str = ""
    processed_at: str = ""
    extraction_method: str = "bedrock_claude_vision"
    
    # Front side fields
    serial_number: Optional[str] = None
    full_names: Optional[str] = None
    nationality: Optional[str] = None
    place_of_birth: Optional[str] = None
    place_of_issue: Optional[str] = None
    date_of_issue: Optional[str] = None
    date_of_expiry: Optional[str] = None
    sex: Optional[str] = None
    date_of_birth: Optional[str] = None
    indiv_number: Optional[str] = None
    
    # Back side fields
    residential_address: Optional[str] = None
    immigration_status: Optional[str] = None
    r_number: Optional[str] = None
    passport_number: Optional[str] = None
    
    # MRZ raw lines
    mrz_line_1: Optional[str] = None
    mrz_line_2: Optional[str] = None
    mrz_line_3: Optional[str] = None
    
    # Validation
    mrz_validated: bool = False
    validation_notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_textract_format(self) -> Dict[str, Dict[str, Any]]:
        """
        Convert to Textract-compatible format for backward compatibility.
        Returns dict matching the format expected by the process() function.
        """
        result = {}
        
        field_mapping = {
            'SERIAL_NUMBER': self.serial_number,
            'FULL_NAMES': self.full_names,
            'NATIONALITY': self.nationality,
            'PLACE_OF_BIRTH': self.place_of_birth,
            'PLACE_OF_ISSUE': self.place_of_issue,
            'DATE_OF_ISSUE': self.date_of_issue,
            'DATE_OF_EXPIRY': self.date_of_expiry,
            'SEX': self.sex,
            'DATE_OF_BIRTH': self.date_of_birth,
            'INDIV_NUMBER': self.indiv_number,
        }
        
        for key, value in field_mapping.items():
            if value is not None:
                result[key] = {
                    'value': value,
                    'confidence': 95.0  # Bedrock doesn't provide confidence, use high default
                }
        
        return result


class MRZParser:
    """Parse and validate MRZ from Kenya Foreigner Certificate."""
    
    WEIGHTS = [7, 3, 1]
    
    # Nationality code mapping
    NATIONALITY_MAP = {
        "IND": "INDIAN", "GBR": "BRITISH", "ITA": "ITALIAN",
        "PAK": "PAKISTANI", "USA": "AMERICAN", "CHN": "CHINESE",
        "KEN": "KENYAN", "ETH": "ETHIOPIAN", "SOM": "SOMALI",
        "UGA": "UGANDAN", "TZA": "TANZANIAN", "BGD": "BANGLADESHI",
        "LKA": "SRI LANKAN", "NGA": "NIGERIAN", "ZAF": "SOUTH AFRICAN",
        "FRA": "FRENCH", "DEU": "GERMAN", "TUR": "TURKISH", "IRN": "IRANIAN",
    }
    
    @classmethod
    def parse(cls, lines: List[str]) -> dict:
        """Parse 3-line MRZ from Kenya Alien ID."""
        result = {
            "valid": False,
            "serial_number": None,
            "date_of_birth": None,
            "sex": None,
            "date_of_expiry": None,
            "nationality": None,
            "indiv_number": None,
            "surname": None,
            "given_names": None,
            "errors": [],
        }
        
        if not lines or len(lines) < 3:
            result["errors"].append("Need 3 MRZ lines")
            return result
        
        lines = [line.strip().upper().replace(" ", "") for line in lines]
        
        try:
            line1, line2, line3 = lines[0], lines[1], lines[2]
            
            # Line 1: Document info - starts with ACKYA
            if line1.startswith("ACKYA"):
                serial_section = line1[5:]
                serial_match = re.match(r"(\d{9})", serial_section)
                if serial_match:
                    result["serial_number"] = serial_match.group(1)
            
            # Line 2: Personal data
            if len(line2) >= 20:
                dob_raw = line2[0:6]
                sex_char = line2[7]
                expiry_raw = line2[8:14]
                nat_raw = line2[15:18]
                remaining = line2[18:]
                indiv_match = re.match(r"(\d+)", remaining)
                
                # Parse date of birth
                try:
                    yy, mm, dd = int(dob_raw[0:2]), int(dob_raw[2:4]), int(dob_raw[4:6])
                    year = 1900 + yy if yy > 50 else 2000 + yy
                    result["date_of_birth"] = f"{dd:02d}.{mm:02d}.{year}"
                except (ValueError, IndexError):
                    result["errors"].append(f"Could not parse DOB from MRZ: {dob_raw}")
                
                # Parse expiry date
                try:
                    yy, mm, dd = int(expiry_raw[0:2]), int(expiry_raw[2:4]), int(expiry_raw[4:6])
                    year = 2000 + yy
                    result["date_of_expiry"] = f"{dd:02d}.{mm:02d}.{year}"
                except (ValueError, IndexError):
                    result["errors"].append(f"Could not parse expiry from MRZ: {expiry_raw}")
                
                # Parse sex
                result["sex"] = "MALE" if sex_char == "M" else "FEMALE" if sex_char == "F" else None
                
                # Parse nationality
                result["nationality"] = cls.NATIONALITY_MAP.get(nat_raw, nat_raw)
                
                # Parse individual number
                if indiv_match:
                    result["indiv_number"] = indiv_match.group(1)
            
            # Line 3: Name
            if "<<" in line3:
                name_parts = line3.rstrip("<").split("<<", 1)
                result["surname"] = name_parts[0].replace("<", " ").strip()
                if len(name_parts) > 1:
                    result["given_names"] = name_parts[1].replace("<", " ").strip()
            
            result["valid"] = len(result["errors"]) == 0
            
        except Exception as e:
            result["errors"].append(f"MRZ parse error: {str(e)}")
        
        return result


def _pdf_to_images_base64(pdf_bytes: bytes) -> List[str]:
    """Convert PDF pages to base64-encoded JPEG images."""
    images_b64 = []
    try:
        # Try pdf2image if available (requires poppler)
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(pdf_bytes, dpi=200, fmt="jpeg")
        for img in images:
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=90)
            images_b64.append(base64.standard_b64encode(buf.getvalue()).decode("utf-8"))
    except ImportError:
        # pdf2image not available - use PIL to try reading as image
        logger.info("pdf2image not available, attempting PIL fallback")
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(pdf_bytes))
            buf = io.BytesIO()
            img.convert('RGB').save(buf, format="JPEG", quality=90)
            images_b64.append(base64.standard_b64encode(buf.getvalue()).decode("utf-8"))
        except Exception as e:
            # Last resort: send raw bytes as document (Bedrock supports PDF)
            logger.warning(f"PIL fallback failed: {e}, sending raw PDF to Bedrock")
            images_b64.append(base64.standard_b64encode(pdf_bytes).decode("utf-8"))
    except Exception as e:
        logger.error(f"Error converting PDF to images: {e}")
        # Fallback: send raw PDF bytes
        images_b64.append(base64.standard_b64encode(pdf_bytes).decode("utf-8"))
    return images_b64


def _image_to_base64(image_bytes: bytes) -> str:
    return base64.standard_b64encode(image_bytes).decode("utf-8")


def _detect_media_type(file_path: str) -> str:
    ext = file_path.lower().split('.')[-1] if '.' in file_path else ''
    type_map = {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "tiff": "image/tiff",
        "tif": "image/tiff",
        "webp": "image/webp",
    }
    return type_map.get(ext, "image/jpeg")


def _call_bedrock_extract(
    image_contents: List[dict],
    bedrock_client=None,
    model_id: str = None,
) -> dict:
    """Call Bedrock Claude Vision to extract fields from Alien ID images."""
    if model_id is None:
        model_id = BEDROCK_MODEL_ID
    
    if bedrock_client is None:
        bedrock_client = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
    
    content = []
    for img in image_contents:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": img["media_type"],
                "data": img["base64"],
            },
        })
    content.append({"type": "text", "text": EXTRACTION_PROMPT})
    
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0,
    })
    
    response = bedrock_client.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=body,
    )
    
    response_body = json.loads(response["body"].read())
    raw_text = response_body["content"][0]["text"]
    
    # Clean up response - remove markdown code blocks if present
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)
    
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Bedrock response as JSON: {e}")
        logger.error(f"Raw response: {raw_text[:500]}")
        return {}


def _cross_validate(bedrock_data: dict, mrz_data: dict) -> List[str]:
    """Cross-validate Bedrock-extracted fields against MRZ-parsed fields."""
    notes = []
    field_mapping = [
        ("serial_number", "serial_number", "Serial Number"),
        ("date_of_birth", "date_of_birth", "Date of Birth"),
        ("sex", "sex", "Sex/Gender"),
        ("date_of_expiry", "date_of_expiry", "Date of Expiry"),
        ("nationality", "nationality", "Nationality"),
        ("indiv_number", "indiv_number", "Individual Number"),
    ]
    
    for bedrock_key, mrz_key, label in field_mapping:
        b_val = bedrock_data.get(bedrock_key)
        m_val = mrz_data.get(mrz_key)
        if b_val and m_val:
            b_norm = str(b_val).strip().upper()
            m_norm = str(m_val).strip().upper()
            if b_norm != m_norm:
                notes.append(f"MISMATCH {label}: Vision='{b_val}' vs MRZ='{m_val}'")
            else:
                notes.append(f"VALIDATED {label}: {b_val}")
        elif not b_val and m_val:
            notes.append(f"FALLBACK {label}: Using MRZ value '{m_val}'")
        elif b_val and not m_val:
            notes.append(f"VISION_ONLY {label}: '{b_val}' (no MRZ to validate)")
    
    return notes


def extract_alien_id_from_s3(
    bucket: str,
    key: str,
    bedrock_client=None,
    s3_client=None,
    model_id: str = None,
) -> AlienIDExtractionResult:
    """
    Extract data from a Kenya Foreigner Certificate stored in S3.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        bedrock_client: Optional pre-configured Bedrock client
        s3_client: Optional pre-configured S3 client
        model_id: Optional Bedrock model ID override
        
    Returns:
        AlienIDExtractionResult with extracted fields
    """
    start_time = datetime.utcnow()
    logger.info(f"Processing Alien ID from S3: s3://{bucket}/{key}")
    
    if s3_client is None:
        s3_client = boto3.client("s3")
    
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    file_bytes = obj["Body"].read()
    
    return _extract_from_bytes(
        file_bytes=file_bytes,
        file_name=key.split("/")[-1],
        media_type=_detect_media_type(key),
        bedrock_client=bedrock_client,
        model_id=model_id,
        start_time=start_time,
    )


def extract_alien_id_from_s3_uri(
    s3_uri: str,
    bedrock_client=None,
    s3_client=None,
    model_id: str = None,
) -> AlienIDExtractionResult:
    """
    Extract data from a Kenya Foreigner Certificate using S3 URI.
    
    Args:
        s3_uri: S3 URI in format s3://bucket/key
        bedrock_client: Optional pre-configured Bedrock client
        s3_client: Optional pre-configured S3 client
        model_id: Optional Bedrock model ID override
        
    Returns:
        AlienIDExtractionResult with extracted fields
    """
    parts = s3_uri.replace("s3://", "").split("/", 1)
    bucket = parts[0]
    key = parts[1] if len(parts) > 1 else ""
    
    return extract_alien_id_from_s3(
        bucket=bucket,
        key=key,
        bedrock_client=bedrock_client,
        s3_client=s3_client,
        model_id=model_id,
    )


def _extract_from_bytes(
    file_bytes: bytes,
    file_name: str,
    media_type: str,
    bedrock_client=None,
    model_id: str = None,
    start_time: datetime = None,
) -> AlienIDExtractionResult:
    """Core extraction logic."""
    if start_time is None:
        start_time = datetime.utcnow()
    
    result = AlienIDExtractionResult(
        source_file=file_name,
        processed_at=start_time.isoformat() + "Z",
    )
    
    # Step 1: Prepare images for Bedrock
    image_contents = []
    if media_type == "application/pdf":
        page_images = _pdf_to_images_base64(file_bytes)
        for img_b64 in page_images:
            image_contents.append({"base64": img_b64, "media_type": "image/jpeg"})
    else:
        image_contents.append({"base64": _image_to_base64(file_bytes), "media_type": media_type})
    
    logger.info(f"Prepared {len(image_contents)} image(s) for Bedrock extraction")
    
    # Step 2: Call Bedrock Claude Vision for extraction
    bedrock_data = _call_bedrock_extract(
        image_contents,
        bedrock_client=bedrock_client,
        model_id=model_id
    )
    logger.info(f"Bedrock extracted fields: {list(bedrock_data.keys())}")
    
    # Step 3: Parse MRZ if available
    mrz_lines = [
        bedrock_data.get(k) for k in ["mrz_line_1", "mrz_line_2", "mrz_line_3"]
        if bedrock_data.get(k)
    ]
    mrz_data = {}
    if len(mrz_lines) == 3:
        mrz_data = MRZParser.parse(mrz_lines)
        result.mrz_validated = mrz_data.get("valid", False)
        logger.info(f"MRZ parsed: valid={mrz_data.get('valid')}, errors={mrz_data.get('errors')}")
    else:
        logger.warning(f"MRZ incomplete — only {len(mrz_lines)} lines extracted")
        result.validation_notes.append(f"MRZ incomplete: {len(mrz_lines)}/3 lines found")
    
    # Step 4: Cross-validate Bedrock vs MRZ
    if mrz_data:
        result.validation_notes.extend(_cross_validate(bedrock_data, mrz_data))
    
    # Step 5: Populate result (Bedrock primary, MRZ fallback)
    def pick(bk: str, mk: str = None) -> Optional[str]:
        val = bedrock_data.get(bk)
        if val:
            return str(val).strip()
        if mk and mrz_data:
            return mrz_data.get(mk)
        return None
    
    result.serial_number = pick("serial_number", "serial_number")
    result.full_names = pick("full_names")
    result.nationality = pick("nationality", "nationality")
    result.place_of_birth = pick("place_of_birth")
    result.place_of_issue = pick("place_of_issue")
    result.date_of_issue = pick("date_of_issue")
    result.date_of_expiry = pick("date_of_expiry", "date_of_expiry")
    result.sex = pick("sex", "sex")
    result.date_of_birth = pick("date_of_birth", "date_of_birth")
    result.indiv_number = pick("indiv_number", "indiv_number")
    result.residential_address = pick("residential_address")
    result.immigration_status = pick("immigration_status")
    result.r_number = pick("r_number")
    result.passport_number = pick("passport_number")
    result.mrz_line_1 = pick("mrz_line_1")
    result.mrz_line_2 = pick("mrz_line_2")
    result.mrz_line_3 = pick("mrz_line_3")
    
    # Reconstruct name from MRZ if needed
    if not result.full_names and mrz_data.get("surname"):
        parts = [mrz_data["surname"]]
        if mrz_data.get("given_names"):
            parts.append(mrz_data["given_names"])
        result.full_names = " ".join(parts)
        result.validation_notes.append("FALLBACK full_names: Reconstructed from MRZ")
    
    elapsed = (datetime.utcnow() - start_time).total_seconds()
    logger.info(f"Alien ID extraction complete in {elapsed:.2f}s: {file_name}")
    
    return result
