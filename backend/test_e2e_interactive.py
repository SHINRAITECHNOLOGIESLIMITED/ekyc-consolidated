#!/usr/bin/env python3
"""
Interactive E2E Test for National ID validation.
Prompts user for ID number and document path, then runs validation.
"""

import boto3
import json
import requests
import sys
import os
from pprint import pprint

# Configuration
AWS_PROFILE = "pasha-eu"
AWS_REGION = "eu-west-1"
APIGW_URL = "https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage"
S3_BUCKET = "maisha-verification-dev-686255958278"


def upload_to_s3(file_path: str, bucket: str, key: str) -> str:
    """Upload a file to S3 and return the S3 URI"""
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    s3_client = session.client('s3')
    
    print(f"[UPLOAD] Uploading {os.path.basename(file_path)} to S3...")
    
    # Determine content type
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
    
    s3_uri = f"s3://{bucket}/{key}"
    print(f"[OK] Uploaded to: {s3_uri}")
    return s3_uri


def validate_nationalid(s3_uri: str, id_number: str) -> dict:
    """Call the National ID validation API"""
    url = f"{APIGW_URL}/document/nationalid"
    
    payload = {
        "uploadedDocumentUrl": s3_uri,
        "idNumber": id_number
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-token-for-stage"
    }
    
    print(f"\n[VALIDATE] Validating National ID...")
    print(f"   URL: {url}")
    print(f"   ID Number: {id_number}")
    
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    print(f"   Status: {response.status_code}")
    
    return response


def analyze_results(results: dict):
    """Analyze and display validation results"""
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    
    if "results" not in results:
        print("[FAIL] No results in response")
        return
    
    match_results = results["results"].get("matchResults", {})
    
    # Standard field matching
    print("\n[INFO] Standard Field Matching:")
    standard_fields = ['serialNumber', 'idNumber', 'fullNames', 'dateOfBirth', 
                       'dateOfIssue', 'gender', 'districtOfBirth', 'placeOfIssue']
    
    for field in standard_fields:
        if field in match_results:
            result = match_results[field]
            status = result.get('status', 'Unknown')
            if status == 'Matched':
                print(f"   [OK] {field}: {status}")
            elif status == 'Not Matched':
                details = result.get('details', {})
                print(f"   [FAIL] {field}: {status}")
                print(f"      Expected: {details.get('expected', 'N/A')}")
                print(f"      Actual: {details.get('actual', 'N/A')}")
            else:
                print(f"   [WARN] {field}: {status}")
    
    # v1.2 IPRS Validation Results
    print("\n[INFO] v1.2 IPRS Validation:")
    
    if 'serialNumberValidation' in match_results:
        sn_result = match_results['serialNumberValidation']
        status = sn_result.get('status', 'Unknown')
        icon = '[OK]' if status == 'MATCH' else '[FAIL]' if status == 'MISMATCH' else '[WARN]'
        print(f"   {icon} Serial Number Validation: {status}")
        print(f"      Document: {sn_result.get('extracted_serial_number', 'N/A')}")
        print(f"      IPRS: {sn_result.get('iprs_serial_number', 'N/A')}")
        if sn_result.get('reason'):
            print(f"      Reason: {sn_result.get('reason')}")
    else:
        print("   [WARN] Serial Number Validation: Not present in response")
    
    if 'genderValidation' in match_results:
        g_result = match_results['genderValidation']
        status = g_result.get('status', 'Unknown')
        icon = '[OK]' if status == 'MATCH' else '[FAIL]' if status == 'MISMATCH' else '[WARN]'
        print(f"   {icon} Gender Validation: {status}")
        print(f"      Document: {g_result.get('extracted_gender', 'N/A')}")
        print(f"      IPRS: {g_result.get('iprs_gender', 'N/A')}")
        if g_result.get('reason'):
            print(f"      Reason: {g_result.get('reason')}")
    else:
        print("   [WARN] Gender Validation: Not present in response")


def test_iprs_only(id_number: str):
    """Test IPRS lookup only (no document validation)"""
    print("\n[INFO] Testing IPRS lookup only...")
    
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    secrets_client = session.client('secretsmanager')
    
    # Get ESB credentials
    secret_name = "jubilee-ekyc-dev-jubilee-esb-ApiGateway-credentials"
    response = secrets_client.get_secret_value(SecretId=secret_name)
    credentials = json.loads(response['SecretString'])
    
    # Authenticate
    auth_url = "https://jubipay.jubileeinsurance.com/api/auth/signin"
    login_data = {"username": credentials['username'], "password": credentials['password']}
    
    auth_response = requests.post(auth_url, json=login_data, headers={"Content-Type": "application/json"}, timeout=30)
    if auth_response.status_code != 200:
        print(f"[FAIL] Authentication failed: {auth_response.text}")
        return
    
    token_data = auth_response.json()
    token = f"{token_data['tokenType']} {token_data['accessToken']}"
    print("[OK] Authentication successful!")
    
    # IPRS search
    url = "https://jubipay.jubileeinsurance.com/iprs/searchV2/LIFE_BUSINESS"
    headers = {"Content-Type": "application/json", "Authorization": token}
    data = {"identifier": "ID_NUMBER", "value": id_number}
    
    print(f"\n[SEARCH] Searching IPRS for ID: {id_number}")
    response = requests.post(url, json=data, headers=headers, timeout=30)
    
    if response.status_code != 200:
        print(f"[FAIL] IPRS search failed: {response.text}")
        return
    
    result = response.json()
    
    if not result.get('success'):
        print(f"[FAIL] IPRS lookup unsuccessful: {result.get('error')}")
        return
    
    iprs_data = result.get('data', {})
    
    print(f"\n[OK] IPRS Response:")
    print(f"   ID Number: {iprs_data.get('idNumber')}")
    print(f"   Serial Number: {iprs_data.get('serialNumber')} {'[OK]' if iprs_data.get('serialNumber') else '[FAIL] MISSING'}")
    print(f"   Gender: {iprs_data.get('gender')} {'[OK]' if iprs_data.get('gender') else '[FAIL] MISSING'}")
    print(f"   First Name: {iprs_data.get('firstName')}")
    print(f"   Other Name: {iprs_data.get('otherName')}")
    print(f"   Surname: {iprs_data.get('surname')}")
    print(f"   Date of Birth: {iprs_data.get('dateOfBirth')}")
    print(f"   Date of Issue: {iprs_data.get('dateOfIssue')}")
    print(f"   Place of Birth: {iprs_data.get('placeOfBirth')}")
    print(f"   Photo Available: {'Yes' if iprs_data.get('photo') else 'No'}")
    
    return result


def main():
    print("=" * 70)
    print("Interactive E2E National ID Validation Test")
    print("=" * 70)
    
    # Menu
    print("\nSelect test type:")
    print("1. IPRS lookup only (no document)")
    print("2. Full document validation (requires document file)")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '3':
        print("Exiting...")
        return 0
    
    # Get ID number
    id_number = input("\nEnter ID Number: ").strip()
    if not id_number:
        print("[FAIL] ID number is required")
        return 1
    
    if choice == '1':
        # IPRS only
        test_iprs_only(id_number)
        return 0
    
    elif choice == '2':
        # Full validation
        doc_path = input("Enter document path (image/PDF): ").strip()
        
        if not doc_path:
            print("[FAIL] Document path is required")
            return 1
        
        # Expand ~ to home directory
        doc_path = os.path.expanduser(doc_path)
        
        if not os.path.exists(doc_path):
            print(f"[FAIL] File not found: {doc_path}")
            return 1
        
        print(f"\n[FILE] Document: {doc_path}")
        print(f"[FILE] ID Number: {id_number}")
        
        # Upload to S3
        s3_key = f"uploaded_kyc_docs/test_{id_number}_{os.path.basename(doc_path)}"
        try:
            s3_uri = upload_to_s3(doc_path, S3_BUCKET, s3_key)
        except Exception as e:
            print(f"[FAIL] Failed to upload to S3: {e}")
            return 1
        
        # Validate
        try:
            response = validate_nationalid(s3_uri, id_number)
            
            if response.status_code == 200:
                results = response.json()
                print("\n[OK] Validation completed successfully!")
                analyze_results(results)
                
                # Print full response
                print("\n" + "=" * 70)
                print("FULL RESPONSE (for debugging)")
                print("=" * 70)
                pprint(results)
            else:
                print(f"\n[FAIL] Validation failed with status {response.status_code}")
                print(response.text)
                return 1
                
        except Exception as e:
            print(f"[FAIL] Error during validation: {e}")
            return 1
    
    else:
        print("[FAIL] Invalid choice")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
