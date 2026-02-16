#!/usr/bin/env python3
"""
E2E Test: Full KYC Flow (Document Validation + IPRS Verification)

This test uses the deployed KYC API to:
1. Upload document to S3
2. Call /document/nationalid for extraction + validation
3. Call /government/nationalid for IPRS verification
4. Compare and display results

Supports: National ID, Passport
"""

import boto3
import json
import requests
import sys
import os
from datetime import datetime
from pprint import pprint

# Configuration
AWS_PROFILE = "pasha-eu"
AWS_REGION = "eu-west-1"
APIGW_URL = "https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage"
S3_BUCKET = "maisha-verification-dev-686255958278"

# Sample documents folder
SAMPLES_FOLDER = "/Users/timothy/KIRO_PROJECTS/ekyc-consolidated/todo_ekyc_enhancements/Samples eKYC"


def upload_to_s3(file_path: str, bucket: str, key: str) -> str:
    """Upload file to S3"""
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    s3 = session.client('s3')
    
    ext = file_path.lower()
    if ext.endswith('.jpg') or ext.endswith('.jpeg'):
        content_type = 'image/jpeg'
    elif ext.endswith('.png'):
        content_type = 'image/png'
    elif ext.endswith('.pdf'):
        content_type = 'application/pdf'
    else:
        content_type = 'application/octet-stream'
    
    s3.upload_file(file_path, bucket, key, ExtraArgs={'ContentType': content_type})
    return f"s3://{bucket}/{key}"


def call_document_validation(s3_uri: str, doc_type: str, identifier: str = None) -> dict:
    """Call document validation API"""
    endpoints = {
        'nationalid': '/document/nationalid',
        'passport': '/document/passport',
    }
    
    endpoint = endpoints.get(doc_type)
    if not endpoint:
        return None
    
    url = f"{APIGW_URL}{endpoint}"
    
    payload = {"uploadedDocumentUrl": s3_uri}
    if identifier:
        if doc_type == 'passport':
            payload["passportNumber"] = identifier
        else:
            payload["idNumber"] = identifier
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-token-for-stage"
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=180)
    return response


def call_government_verification(doc_type: str, identifier: str, id_number: str = None) -> dict:
    """Call government verification API
    
    Args:
        doc_type: 'nationalid' or 'passport'
        identifier: ID number for nationalid, passport number for passport
        id_number: Required for passport verification (the person's national ID)
    """
    endpoints = {
        'nationalid': '/government/nationalid',
        'passport': '/government/passport',
    }
    
    endpoint = endpoints.get(doc_type)
    if not endpoint:
        return None
    
    url = f"{APIGW_URL}{endpoint}"
    
    if doc_type == 'passport':
        # Passport verification requires BOTH passportNumber AND idNumber
        if not id_number:
            print(f"   [WARN] Passport verification requires ID number - skipping")
            return None
        payload = {"passportNumber": identifier, "idNumber": id_number}
    else:
        payload = {"idNumber": identifier}
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-token-for-stage"
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    return response


def run_full_flow_test(file_path: str, identifier: str, doc_type: str = 'nationalid', id_number: str = None):
    """Run full KYC flow test
    
    Args:
        file_path: Path to document file
        identifier: ID number for nationalid, passport number for passport
        doc_type: 'nationalid' or 'passport'
        id_number: For passport, the person's national ID number
    """
    print(f"\n{'='*70}")
    print(f"Full KYC Flow Test")
    print(f"{'='*70}")
    print(f"Document: {os.path.basename(file_path)}")
    print(f"Type: {doc_type}")
    print(f"Identifier: {identifier}")
    if id_number:
        print(f"ID Number: {id_number}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    results = {
        'document': os.path.basename(file_path),
        'identifier': identifier,
        'doc_type': doc_type,
        'validation': None,
        'verification': None,
        'status': 'PENDING'
    }
    
    # Step 1: Upload to S3
    print(f"\n[STEP 1] Uploading document to S3...")
    s3_key = f"e2e_test/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(file_path)}"
    try:
        s3_uri = upload_to_s3(file_path, S3_BUCKET, s3_key)
        print(f"   [OK] Uploaded to: {s3_uri}")
    except Exception as e:
        print(f"   [FAIL] Upload failed: {e}")
        results['status'] = 'FAILED'
        results['error'] = str(e)
        return results
    
    # Step 2: Document Validation (Textract extraction + field matching)
    print(f"\n[STEP 2] Calling Document Validation API...")
    print(f"   Endpoint: /document/{doc_type}")
    
    try:
        response = call_document_validation(s3_uri, doc_type, identifier)
        
        if response is None:
            print(f"   [FAIL] No response from API")
            results['status'] = 'FAILED'
            results['error'] = 'No response from validation API'
            return results
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            validation_result = response.json()
            results['validation'] = validation_result
            print(f"   [OK] Validation completed")
            
            # Display match results and extract data from them
            match_results = validation_result.get('results', {}).get('matchResults', {})
            
            # First, show extracted data from match results
            if match_results:
                print(f"\n   [INFO] Extracted Data (from Textract):")
                extracted_fields = {}
                for field, result in match_results.items():
                    if isinstance(result, dict):
                        details = result.get('details')
                        if details and isinstance(details, dict):
                            expected = details.get('expected')
                            if expected:
                                extracted_fields[field] = expected
                        # v1.2 fields have different structure
                        if 'extractedSerialNumber' in result:
                            extracted_fields['serialNumber (v1.2)'] = result.get('extractedSerialNumber')
                        if 'extractedGender' in result:
                            extracted_fields['gender (v1.2)'] = result.get('extractedGender')
                
                if extracted_fields:
                    for key, value in sorted(extracted_fields.items()):
                        print(f"      {key}: {value}")
                else:
                    print(f"      [WARN] No extracted values found")
                
                # Show match results
                print(f"\n   [INFO] Match Results:")
                for field, result in match_results.items():
                    if isinstance(result, dict):
                        status = result.get('status', 'Unknown')
                        icon = '[OK]' if status in ['Matched', 'MATCH'] else '[FAIL]' if status in ['Not Matched', 'MISMATCH'] else '[WARN]'
                        print(f"      {icon} {field}: {status}")
                        # Show details for matched fields
                        details = result.get('details')
                        if details and isinstance(details, dict):
                            if details.get('expected'):
                                print(f"          Document: {details.get('expected')}")
                            if details.get('actual'):
                                print(f"          Input: {details.get('actual')}")
                        # Show v1.2 validation details
                        if 'extractedSerialNumber' in result or 'extractedGender' in result:
                            for k, v in result.items():
                                if k != 'status' and v is not None:
                                    print(f"          {k}: {v}")
        else:
            print(f"   [FAIL] Validation failed")
            print(f"   Response: {response.text[:500]}")
            results['validation'] = {'error': response.text}
    except Exception as e:
        print(f"   [FAIL] Validation error: {e}")
        results['validation'] = {'error': str(e)}
    
    # Step 3: Government Verification (IPRS lookup)
    print(f"\n[STEP 3] Calling Government Verification API...")
    print(f"   Endpoint: /government/{doc_type}")
    print(f"   Identifier: {identifier}")
    if id_number:
        print(f"   ID Number: {id_number}")
    
    try:
        response = call_government_verification(doc_type, identifier, id_number)
        
        if response is None:
            print(f"   [FAIL] No response from API")
            results['verification'] = {'error': 'No response'}
        elif response.status_code == 200:
            verification_result = response.json()
            results['verification'] = verification_result
            print(f"   [OK] Verification completed")
            
            # Display verification results
            verify_results = verification_result.get('results', {})
            if verify_results:
                print(f"\n   [INFO] IPRS Verification Results:")
                for field, result in verify_results.items():
                    if isinstance(result, dict):
                        status = result.get('status', 'Unknown')
                        icon = '[OK]' if status == 'Matched' else '[FAIL]' if status == 'Not Matched' else '[WARN]'
                        print(f"      {icon} {field}: {status}")
                        details = result.get('details')
                        if details and status == 'Matched':
                            print(f"          Value: {details.get('actual', details.get('expected', 'N/A'))}")
        else:
            print(f"   [FAIL] Verification failed")
            print(f"   Response: {response.text[:500]}")
            results['verification'] = {'error': response.text}
    except Exception as e:
        print(f"   [FAIL] Verification error: {e}")
        results['verification'] = {'error': str(e)}
    
    # Determine overall status
    if results['validation'] and not results['validation'].get('error'):
        if results['verification'] and not results['verification'].get('error'):
            results['status'] = 'SUCCESS'
        else:
            results['status'] = 'PARTIAL'
    else:
        results['status'] = 'FAILED'
    
    return results


def main():
    print("=" * 70)
    print("E2E Test: Full KYC Flow")
    print("(Document Validation + IPRS Verification)")
    print("=" * 70)
    
    # Get document type
    print("\nSelect document type:")
    print("1. National ID")
    print("2. Passport")
    print("3. Exit")
    
    type_choice = input("\nEnter choice (1-3): ").strip()
    
    if type_choice == '3':
        print("Exiting...")
        return 0
    
    doc_type = 'nationalid' if type_choice == '1' else 'passport' if type_choice == '2' else None
    if not doc_type:
        print("[FAIL] Invalid choice")
        return 1
    
    # Get identifier
    id_number = None
    if doc_type == 'nationalid':
        identifier = input("\nEnter ID Number: ").strip()
    else:
        identifier = input("\nEnter Passport Number: ").strip()
        id_number = input("Enter ID Number (required for IPRS verification): ").strip()
    
    if not identifier:
        print("[FAIL] Identifier is required")
        return 1
    
    # Get document path
    file_path = input("\nEnter document path (or press Enter to skip validation): ").strip()
    
    if file_path:
        file_path = os.path.expanduser(file_path)
        if not os.path.exists(file_path):
            print(f"[FAIL] File not found: {file_path}")
            return 1
        
        # Run full flow
        result = run_full_flow_test(file_path, identifier, doc_type, id_number)
    else:
        # Just run verification
        print(f"\n[INFO] Skipping document validation, running IPRS verification only...")
        result = {'status': 'VERIFICATION_ONLY', 'verification': None}
        
        response = call_government_verification(doc_type, identifier, id_number)
        if response and response.status_code == 200:
            result['verification'] = response.json()
            result['status'] = 'SUCCESS'
            
            iprs_data = result['verification'].get('data', {})
            print(f"\n[OK] IPRS Verification Result:")
            print(f"   ID Number: {iprs_data.get('idNumber')}")
            print(f"   Serial Number: {iprs_data.get('serialNumber')}")
            print(f"   Gender: {iprs_data.get('gender')}")
            print(f"   Name: {iprs_data.get('firstName')} {iprs_data.get('surname')}")
            print(f"   DOB: {iprs_data.get('dateOfBirth')}")
        else:
            print(f"[FAIL] Verification failed: {response.text if response else 'No response'}")
            result['status'] = 'FAILED'
    
    # Final summary
    print(f"\n{'='*70}")
    print("FINAL RESULT")
    print(f"{'='*70}")
    print(f"Status: {result['status']}")
    
    return 0 if result['status'] in ['SUCCESS', 'VERIFICATION_ONLY'] else 1


if __name__ == "__main__":
    exit(main())
