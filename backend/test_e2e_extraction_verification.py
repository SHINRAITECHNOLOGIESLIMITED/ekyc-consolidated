#!/usr/bin/env python3
"""
E2E Test: Document Extraction → IPRS Verification

This test simulates the full KYC flow:
1. Upload document to S3
2. Extract data using AWS Textract
3. Verify extracted data against IPRS via ESB

Supports: National ID, Passport, Alien ID
"""

import boto3
import json
import requests
import sys
import os
import time
from datetime import datetime
from pprint import pprint

# Configuration
AWS_PROFILE = "pasha-eu"
AWS_REGION = "eu-west-1"
S3_BUCKET = "maisha-verification-dev-686255958278"
ESB_SECRET_NAME = "jubilee-ekyc-dev-jubilee-esb-ApiGateway-credentials"

# Sample documents folder
SAMPLES_FOLDER = "/Users/timothy/KIRO_PROJECTS/ekyc-consolidated/todo_ekyc_enhancements/Samples eKYC"


class ESBClient:
    """Client for Jubilee ESB API"""
    
    def __init__(self, profile: str, region: str, secret_name: str):
        self.session = boto3.Session(profile_name=profile, region_name=region)
        self.base_url = "https://jubipay.jubileeinsurance.com"
        self.token = None
        self._load_credentials(secret_name)
    
    def _load_credentials(self, secret_name: str):
        """Load ESB credentials from Secrets Manager"""
        secrets_client = self.session.client('secretsmanager')
        response = secrets_client.get_secret_value(SecretId=secret_name)
        self.credentials = json.loads(response['SecretString'])
    
    def authenticate(self) -> bool:
        """Authenticate with ESB and get JWT token"""
        auth_url = f"{self.base_url}/api/auth/signin"
        login_data = {
            "username": self.credentials['username'],
            "password": self.credentials['password']
        }
        
        response = requests.post(
            auth_url,
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"[FAIL] ESB authentication failed: {response.text}")
            return False
        
        token_data = response.json()
        self.token = f"{token_data['tokenType']} {token_data['accessToken']}"
        return True
    
    def verify_national_id(self, id_number: str) -> dict:
        """Verify National ID against IPRS"""
        url = f"{self.base_url}/iprs/searchV2/LIFE_BUSINESS"
        headers = {"Content-Type": "application/json", "Authorization": self.token}
        data = {"identifier": "ID_NUMBER", "value": id_number}
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        return response.json() if response.status_code == 200 else None
    
    def verify_passport(self, passport_number: str, id_number: str = None) -> dict:
        """Verify Passport against IPRS"""
        url = f"{self.base_url}/iprs/searchUsingPassportNumber/LIFE_BUSINESS"
        headers = {"Content-Type": "application/json", "Authorization": self.token}
        data = {"identifier": "PASSPORT", "value": passport_number}
        if id_number:
            data["idNumber"] = id_number
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        return response.json() if response.status_code == 200 else None


class TextractExtractor:
    """Extract data from documents using AWS Textract"""
    
    def __init__(self, profile: str, region: str):
        self.session = boto3.Session(profile_name=profile, region_name=region)
        self.textract = self.session.client('textract')
        self.s3 = self.session.client('s3')
    
    def upload_to_s3(self, file_path: str, bucket: str, key: str) -> str:
        """Upload file to S3"""
        ext = file_path.lower()
        if ext.endswith('.jpg') or ext.endswith('.jpeg'):
            content_type = 'image/jpeg'
        elif ext.endswith('.png'):
            content_type = 'image/png'
        elif ext.endswith('.pdf'):
            content_type = 'application/pdf'
        else:
            content_type = 'application/octet-stream'
        
        self.s3.upload_file(file_path, bucket, key, ExtraArgs={'ContentType': content_type})
        return f"s3://{bucket}/{key}"
    
    def extract_document(self, bucket: str, key: str) -> dict:
        """Extract text and data from document using Textract"""
        print(f"   [TEXTRACT] Starting document analysis...")
        
        # Start async document analysis
        response = self.textract.start_document_analysis(
            DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': key}},
            FeatureTypes=['FORMS', 'TABLES']
        )
        
        job_id = response['JobId']
        print(f"   [TEXTRACT] Job ID: {job_id}")
        
        # Wait for completion
        status = 'IN_PROGRESS'
        while status == 'IN_PROGRESS':
            time.sleep(2)
            result = self.textract.get_document_analysis(JobId=job_id)
            status = result['JobStatus']
            print(f"   [TEXTRACT] Status: {status}")
        
        if status != 'SUCCEEDED':
            print(f"   [FAIL] Textract failed: {status}")
            return None
        
        # Extract key-value pairs
        extracted = self._parse_textract_response(result)
        return extracted
    
    def extract_document_sync(self, bucket: str, key: str) -> dict:
        """Extract text using synchronous API (for images only)"""
        print(f"   [TEXTRACT] Analyzing document...")
        
        try:
            response = self.textract.analyze_document(
                Document={'S3Object': {'Bucket': bucket, 'Name': key}},
                FeatureTypes=['FORMS']
            )
            return self._parse_textract_response(response)
        except Exception as e:
            print(f"   [FAIL] Textract sync failed: {e}")
            # Fall back to async for PDFs
            return self.extract_document(bucket, key)
    
    def _parse_textract_response(self, response: dict) -> dict:
        """Parse Textract response to extract key-value pairs"""
        extracted = {
            'raw_text': [],
            'key_values': {},
            'id_number': None,
            'serial_number': None,
            'passport_number': None,
            'first_name': None,
            'surname': None,
            'gender': None,
            'date_of_birth': None,
        }
        
        # Get all blocks
        blocks = response.get('Blocks', [])
        
        # Build maps for key-value extraction
        key_map = {}
        value_map = {}
        block_map = {}
        
        for block in blocks:
            block_id = block['Id']
            block_map[block_id] = block
            
            if block['BlockType'] == 'KEY_VALUE_SET':
                if 'KEY' in block.get('EntityTypes', []):
                    key_map[block_id] = block
                else:
                    value_map[block_id] = block
            
            if block['BlockType'] == 'LINE':
                extracted['raw_text'].append(block.get('Text', ''))
        
        # Extract key-value pairs
        for key_id, key_block in key_map.items():
            key_text = self._get_text(key_block, block_map)
            value_text = ''
            
            for relationship in key_block.get('Relationships', []):
                if relationship['Type'] == 'VALUE':
                    for value_id in relationship['Ids']:
                        value_block = block_map.get(value_id)
                        if value_block:
                            value_text = self._get_text(value_block, block_map)
            
            if key_text and value_text:
                extracted['key_values'][key_text.strip()] = value_text.strip()
        
        # Try to identify specific fields from raw text and key-values
        self._identify_fields(extracted)
        
        return extracted
    
    def _get_text(self, block: dict, block_map: dict) -> str:
        """Get text from a block"""
        text = ''
        if 'Relationships' in block:
            for relationship in block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        child = block_map.get(child_id)
                        if child and child['BlockType'] == 'WORD':
                            text += child.get('Text', '') + ' '
        return text.strip()
    
    def _identify_fields(self, extracted: dict):
        """Identify specific fields from extracted data"""
        raw_text = ' '.join(extracted['raw_text']).upper()
        key_values = extracted['key_values']
        
        # Common field mappings
        id_keys = ['ID NUMBER', 'ID NO', 'NATIONAL ID', 'IDENTITY NUMBER', 'ID.NO']
        serial_keys = ['SERIAL NUMBER', 'SERIAL NO', 'SERIAL', 'S/NO']
        passport_keys = ['PASSPORT NUMBER', 'PASSPORT NO', 'PASSPORT']
        name_keys = ['FULL NAME', 'NAME', 'NAMES', 'FIRST NAME', 'SURNAME']
        gender_keys = ['SEX', 'GENDER']
        dob_keys = ['DATE OF BIRTH', 'DOB', 'BIRTH DATE', 'D.O.B']
        
        # Search in key-values
        for key, value in key_values.items():
            key_upper = key.upper()
            
            for id_key in id_keys:
                if id_key in key_upper:
                    extracted['id_number'] = value
                    break
            
            for serial_key in serial_keys:
                if serial_key in key_upper:
                    extracted['serial_number'] = value
                    break
            
            for passport_key in passport_keys:
                if passport_key in key_upper:
                    extracted['passport_number'] = value
                    break
            
            for gender_key in gender_keys:
                if gender_key in key_upper:
                    extracted['gender'] = value
                    break
            
            for dob_key in dob_keys:
                if dob_key in key_upper:
                    extracted['date_of_birth'] = value
                    break
        
        # Try to extract 8-digit ID number from raw text if not found
        if not extracted['id_number']:
            import re
            id_match = re.search(r'\b(\d{7,8})\b', raw_text)
            if id_match:
                extracted['id_number'] = id_match.group(1)
        
        # Try to extract serial number (typically 9 digits)
        if not extracted['serial_number']:
            import re
            serial_match = re.search(r'\b(\d{9})\b', raw_text)
            if serial_match:
                extracted['serial_number'] = serial_match.group(1)


def compare_results(extracted: dict, iprs_data: dict) -> dict:
    """Compare extracted data with IPRS data"""
    comparison = {
        'id_number': {'extracted': None, 'iprs': None, 'match': None},
        'serial_number': {'extracted': None, 'iprs': None, 'match': None},
        'gender': {'extracted': None, 'iprs': None, 'match': None},
        'first_name': {'extracted': None, 'iprs': None, 'match': None},
    }
    
    # ID Number
    ext_id = extracted.get('id_number')
    iprs_id = iprs_data.get('idNumber')
    comparison['id_number'] = {
        'extracted': ext_id,
        'iprs': iprs_id,
        'match': 'MATCH' if ext_id and iprs_id and str(ext_id) == str(iprs_id) else 'MISMATCH' if ext_id and iprs_id else 'INCONCLUSIVE'
    }
    
    # Serial Number
    ext_serial = extracted.get('serial_number')
    iprs_serial = iprs_data.get('serialNumber')
    comparison['serial_number'] = {
        'extracted': ext_serial,
        'iprs': iprs_serial,
        'match': 'MATCH' if ext_serial and iprs_serial and str(ext_serial) == str(iprs_serial) else 'MISMATCH' if ext_serial and iprs_serial else 'INCONCLUSIVE'
    }
    
    # Gender
    ext_gender = extracted.get('gender', '').upper()[:1] if extracted.get('gender') else None
    iprs_gender = iprs_data.get('gender', '').upper()[:1] if iprs_data.get('gender') else None
    comparison['gender'] = {
        'extracted': ext_gender,
        'iprs': iprs_gender,
        'match': 'MATCH' if ext_gender and iprs_gender and ext_gender == iprs_gender else 'MISMATCH' if ext_gender and iprs_gender else 'INCONCLUSIVE'
    }
    
    return comparison


def run_e2e_test(file_path: str, doc_type: str = 'nationalid'):
    """Run full E2E test for a document"""
    print(f"\n{'='*70}")
    print(f"E2E Test: {os.path.basename(file_path)}")
    print(f"Document Type: {doc_type}")
    print(f"{'='*70}")
    
    # Initialize clients
    print("\n[STEP 1] Initializing clients...")
    extractor = TextractExtractor(AWS_PROFILE, AWS_REGION)
    esb = ESBClient(AWS_PROFILE, AWS_REGION, ESB_SECRET_NAME)
    
    # Authenticate with ESB
    print("[STEP 2] Authenticating with ESB...")
    if not esb.authenticate():
        return {'status': 'FAILED', 'error': 'ESB authentication failed'}
    print("   [OK] ESB authenticated")
    
    # Upload to S3
    print("[STEP 3] Uploading document to S3...")
    s3_key = f"e2e_test/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(file_path)}"
    try:
        s3_uri = extractor.upload_to_s3(file_path, S3_BUCKET, s3_key)
        print(f"   [OK] Uploaded to: {s3_uri}")
    except Exception as e:
        return {'status': 'FAILED', 'error': f'S3 upload failed: {e}'}
    
    # Extract with Textract
    print("[STEP 4] Extracting data with Textract...")
    try:
        extracted = extractor.extract_document(S3_BUCKET, s3_key)
        if not extracted:
            return {'status': 'FAILED', 'error': 'Textract extraction failed'}
        
        print(f"   [OK] Extraction complete")
        print(f"   Extracted ID Number: {extracted.get('id_number', 'Not found')}")
        print(f"   Extracted Serial: {extracted.get('serial_number', 'Not found')}")
        print(f"   Extracted Gender: {extracted.get('gender', 'Not found')}")
    except Exception as e:
        return {'status': 'FAILED', 'error': f'Textract failed: {e}'}
    
    # Verify against IPRS
    print("[STEP 5] Verifying against IPRS...")
    id_number = extracted.get('id_number')
    
    if not id_number:
        print("   [WARN] No ID number extracted - cannot verify against IPRS")
        return {
            'status': 'PARTIAL',
            'extracted': extracted,
            'iprs': None,
            'comparison': None,
            'error': 'No ID number extracted'
        }
    
    try:
        if doc_type == 'passport':
            passport_num = extracted.get('passport_number')
            iprs_response = esb.verify_passport(passport_num, id_number) if passport_num else esb.verify_national_id(id_number)
        else:
            iprs_response = esb.verify_national_id(id_number)
        
        if not iprs_response or not iprs_response.get('success'):
            error = iprs_response.get('error') if iprs_response else 'No response'
            print(f"   [FAIL] IPRS verification failed: {error}")
            return {
                'status': 'FAILED',
                'extracted': extracted,
                'iprs': None,
                'comparison': None,
                'error': f'IPRS verification failed: {error}'
            }
        
        iprs_data = iprs_response.get('data', {})
        print(f"   [OK] IPRS verification successful")
        print(f"   IPRS ID Number: {iprs_data.get('idNumber')}")
        print(f"   IPRS Serial: {iprs_data.get('serialNumber')}")
        print(f"   IPRS Gender: {iprs_data.get('gender')}")
        print(f"   IPRS Name: {iprs_data.get('firstName')} {iprs_data.get('surname')}")
    except Exception as e:
        return {'status': 'FAILED', 'error': f'IPRS verification failed: {e}'}
    
    # Compare results
    print("[STEP 6] Comparing extracted vs IPRS data...")
    comparison = compare_results(extracted, iprs_data)
    
    print("\n[RESULTS] Comparison:")
    for field, result in comparison.items():
        icon = '[OK]' if result['match'] == 'MATCH' else '[FAIL]' if result['match'] == 'MISMATCH' else '[WARN]'
        print(f"   {icon} {field}: {result['match']}")
        print(f"       Extracted: {result['extracted']}")
        print(f"       IPRS: {result['iprs']}")
    
    return {
        'status': 'SUCCESS',
        'extracted': extracted,
        'iprs': iprs_data,
        'comparison': comparison
    }


def main():
    print("=" * 70)
    print("E2E Test: Document Extraction → IPRS Verification")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Menu
    print("\nSelect test mode:")
    print("1. Test single document")
    print("2. Test all documents in folder")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '3':
        print("Exiting...")
        return 0
    
    if choice == '1':
        # Single document test
        file_path = input("\nEnter document path: ").strip()
        file_path = os.path.expanduser(file_path)
        
        if not os.path.exists(file_path):
            print(f"[FAIL] File not found: {file_path}")
            return 1
        
        # Determine document type
        filename = os.path.basename(file_path).upper()
        if 'PASSPORT' in filename:
            doc_type = 'passport'
        elif 'ALIEN' in filename:
            doc_type = 'alienid'
        else:
            doc_type = 'nationalid'
        
        result = run_e2e_test(file_path, doc_type)
        
        print("\n" + "=" * 70)
        print("FINAL RESULT")
        print("=" * 70)
        print(f"Status: {result['status']}")
        if result.get('error'):
            print(f"Error: {result['error']}")
        
        return 0 if result['status'] == 'SUCCESS' else 1
    
    elif choice == '2':
        # Batch test
        folder = input(f"\nEnter folder path (or Enter for default):\n[{SAMPLES_FOLDER}]: ").strip()
        if not folder:
            folder = SAMPLES_FOLDER
        
        if not os.path.exists(folder):
            print(f"[FAIL] Folder not found: {folder}")
            return 1
        
        # Get document files (exclude Image files)
        files = [f for f in os.listdir(folder) 
                 if f.endswith('.pdf') and 'Image' not in f and not f.startswith('.')]
        
        print(f"\nFound {len(files)} documents to test")
        
        results = []
        for filename in sorted(files):
            file_path = os.path.join(folder, filename)
            
            # Determine document type
            if 'PASSPORT' in filename.upper():
                doc_type = 'passport'
            elif 'ALIEN' in filename.upper():
                doc_type = 'alienid'
            else:
                doc_type = 'nationalid'
            
            result = run_e2e_test(file_path, doc_type)
            results.append({'file': filename, 'result': result})
        
        # Summary
        print("\n" + "=" * 70)
        print("BATCH TEST SUMMARY")
        print("=" * 70)
        
        success = sum(1 for r in results if r['result']['status'] == 'SUCCESS')
        partial = sum(1 for r in results if r['result']['status'] == 'PARTIAL')
        failed = sum(1 for r in results if r['result']['status'] == 'FAILED')
        
        print(f"Total: {len(results)}")
        print(f"Success: {success}")
        print(f"Partial: {partial}")
        print(f"Failed: {failed}")
        
        return 0
    
    else:
        print("[FAIL] Invalid choice")
        return 1


if __name__ == "__main__":
    exit(main())
