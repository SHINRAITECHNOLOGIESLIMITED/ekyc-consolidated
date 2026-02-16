#!/usr/bin/env python3
"""
Batch E2E Test for document validation.
Tests multiple documents from a folder against the validation API.
Supports National ID, Passport, and Alien ID document types.
"""

import boto3
import json
import requests
import sys
import os
from pprint import pprint
from datetime import datetime

# Configuration
AWS_PROFILE = "pasha-eu"
AWS_REGION = "eu-west-1"
APIGW_URL = "https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage"
S3_BUCKET = "maisha-verification-dev-686255958278"

# Sample folder path
SAMPLES_FOLDER = "/Users/timothy/KIRO_PROJECTS/ekyc-consolidated/todo_ekyc_enhancements/Samples eKYC"


def upload_to_s3(file_path: str, bucket: str, key: str) -> str:
    """Upload a file to S3 and return the S3 URI"""
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    s3_client = session.client('s3')
    
    ext = file_path.lower()
    if ext.endswith('.jpg') or ext.endswith('.jpeg'):
        content_type = 'image/jpeg'
    elif ext.endswith('.png'):
        content_type = 'image/png'
    elif ext.endswith('.pdf'):
        content_type = 'application/pdf'
    else:
        content_type = 'application/octet-stream'
    
    s3_client.upload_file(file_path, bucket, key, ExtraArgs={'ContentType': content_type})
    return f"s3://{bucket}/{key}"


def validate_document(s3_uri: str, doc_type: str, identifier: str = None) -> dict:
    """Call the document validation API"""
    
    # Map document type to endpoint
    # Note: Alien ID is not supported - use nationalid endpoint as fallback
    endpoints = {
        'nationalid': '/document/nationalid',
        'passport': '/document/passport',
        'alienid': None,  # Not supported
        'krapincertificate': '/document/krapincertificate',
        'cr12': '/document/cr12',
    }
    
    endpoint = endpoints.get(doc_type.lower())
    if endpoint is None:
        print(f"   [SKIP] Document type '{doc_type}' not supported by API")
        return None
    
    url = f"{APIGW_URL}{endpoint}"
    
    payload = {"uploadedDocumentUrl": s3_uri}
    if identifier:
        if doc_type.lower() == 'passport':
            payload["passportNumber"] = identifier
        else:
            payload["idNumber"] = identifier
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-token-for-stage"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        return response
    except requests.exceptions.Timeout:
        print(f"   [FAIL] Request timed out after 120 seconds")
        return None
    except Exception as e:
        print(f"   [FAIL] Request error: {e}")
        return None


def analyze_extraction(results: dict, doc_name: str):
    """Analyze and display extraction results"""
    print(f"\n{'='*60}")
    print(f"Document: {doc_name}")
    print('='*60)
    
    if not results:
        print("[FAIL] No response")
        return
    
    if "results" not in results:
        print(f"[FAIL] No results - Error: {results.get('message', 'Unknown')}")
        return
    
    extracted = results.get("results", {}).get("extractedData", {})
    
    if extracted:
        print("\n[INFO] Extracted Data:")
        for key, value in extracted.items():
            if value:
                print(f"   {key}: {value}")
    
    # Check for validation results
    match_results = results.get("results", {}).get("matchResults", {})
    if match_results:
        print("\n[INFO] Match Results:")
        for field, result in match_results.items():
            if isinstance(result, dict):
                status = result.get('status', 'Unknown')
                icon = '[OK]' if status in ['Matched', 'MATCH'] else '[FAIL]' if status in ['Not Matched', 'MISMATCH'] else '[WARN]'
                print(f"   {icon} {field}: {status}")


def test_folder(folder_path: str):
    """Test all documents in a folder"""
    print("=" * 70)
    print("Batch Document Validation Test")
    print("=" * 70)
    print(f"Folder: {folder_path}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    if not os.path.exists(folder_path):
        print(f"[FAIL] Folder not found: {folder_path}")
        return 1
    
    # Get all PDF files (excluding Image files which are photos)
    files = [f for f in os.listdir(folder_path) 
             if f.endswith('.pdf') and 'Image' not in f and not f.startswith('.')]
    
    print(f"\nFound {len(files)} document files to test")
    
    results_summary = []
    
    for filename in sorted(files):
        file_path = os.path.join(folder_path, filename)
        
        # Determine document type from filename
        if 'ALIEN' in filename.upper():
            doc_type = 'alienid'
        elif 'PASSPORT' in filename.upper():
            doc_type = 'passport'
        else:
            doc_type = 'nationalid'
        
        print(f"\n[TEST] Processing: {filename} (type: {doc_type})")
        
        # Skip unsupported document types
        if doc_type == 'alienid':
            print(f"   [SKIP] Alien ID validation not supported by API")
            results_summary.append({"file": filename, "status": "SKIPPED", "error": "Alien ID not supported"})
            continue
        
        # Upload to S3
        s3_key = f"uploaded_kyc_docs/batch_test/{filename}"
        try:
            s3_uri = upload_to_s3(file_path, S3_BUCKET, s3_key)
            print(f"   [OK] Uploaded to S3")
        except Exception as e:
            print(f"   [FAIL] Upload failed: {e}")
            results_summary.append({"file": filename, "status": "UPLOAD_FAILED", "error": str(e)})
            continue
        
        # Validate
        try:
            response = validate_document(s3_uri, doc_type)
            
            if response and response.status_code == 200:
                results = response.json()
                analyze_extraction(results, filename)
                results_summary.append({"file": filename, "status": "SUCCESS", "data": results})
            else:
                status_code = response.status_code if response else "No response"
                error_text = response.text if response else "No response"
                print(f"   [FAIL] Validation failed: {status_code}")
                print(f"   Error: {error_text[:200]}...")
                results_summary.append({"file": filename, "status": "FAILED", "error": error_text[:200]})
                
        except Exception as e:
            print(f"   [FAIL] Error: {e}")
            results_summary.append({"file": filename, "status": "ERROR", "error": str(e)})
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    success = sum(1 for r in results_summary if r['status'] == 'SUCCESS')
    failed = len(results_summary) - success
    
    print(f"Total: {len(results_summary)}")
    print(f"Success: {success}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print("\nFailed documents:")
        for r in results_summary:
            if r['status'] != 'SUCCESS':
                print(f"   - {r['file']}: {r['status']} - {r.get('error', 'Unknown')[:50]}")
    
    return 0


def main():
    print("=" * 70)
    print("Batch E2E Document Validation Test")
    print("=" * 70)
    
    # Use default folder or prompt
    folder = input(f"\nEnter folder path (or press Enter for default):\n[{SAMPLES_FOLDER}]: ").strip()
    
    if not folder:
        folder = SAMPLES_FOLDER
    
    return test_folder(folder)


if __name__ == "__main__":
    exit(main())
