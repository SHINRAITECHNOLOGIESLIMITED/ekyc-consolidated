#!/usr/bin/env python3
"""
E2E Test for National ID validation with v1.2 Serial Number and Gender validation.
Tests a local image file by uploading to S3 and calling the validation API.
"""

import boto3
import json
import requests
import sys
import os
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from pprint import pprint

# Configuration
AWS_PROFILE = "pasha-eu"
AWS_REGION = "eu-west-1"
APIGW_URL = "https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage"
# Use maisha bucket which exists
S3_BUCKET = "maisha-verification-dev-686255958278"

# Test image path
IMAGE_PATH = "/Users/timothy/KIRO_PROJECTS/ekyc-consolidated/todo_ekyc_enhancements/TIM.jpg"


def upload_to_s3(file_path: str, bucket: str, key: str) -> str:
    """Upload a file to S3 and return the S3 URI"""
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    s3_client = session.client('s3')
    
    print(f"📤 Uploading {os.path.basename(file_path)} to S3...")
    
    # Determine content type
    if file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
        content_type = 'image/jpeg'
    elif file_path.lower().endswith('.png'):
        content_type = 'image/png'
    elif file_path.lower().endswith('.pdf'):
        content_type = 'application/pdf'
    else:
        content_type = 'application/octet-stream'
    
    s3_client.upload_file(
        file_path, 
        bucket, 
        key,
        ExtraArgs={'ContentType': content_type}
    )
    
    s3_uri = f"s3://{bucket}/{key}"
    print(f"✅ Uploaded to: {s3_uri}")
    return s3_uri


def get_auth_headers(method: str, url: str, body: str = None) -> dict:
    """Generate authentication headers for API Gateway"""
    # For Stage environment, use a dummy Bearer token
    # The authorizer auto-approves Stage requests
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-token-for-stage"
    }


def validate_nationalid(s3_uri: str, id_data: dict) -> dict:
    """Call the National ID validation API"""
    url = f"{APIGW_URL}/document/nationalid"
    
    payload = {
        "uploadedDocumentUrl": s3_uri,
        **id_data
    }
    
    print(f"\n🔍 Validating National ID...")
    print(f"   URL: {url}")
    print(f"   ID Number: {id_data.get('idNumber', 'N/A')}")
    
    body = json.dumps(payload)
    headers = get_auth_headers('POST', url, body)
    
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    
    print(f"   Status: {response.status_code}")
    
    return response


def analyze_results(results: dict):
    """Analyze and display validation results"""
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    
    if "results" not in results:
        print("❌ No results in response")
        return
    
    match_results = results["results"].get("matchResults", {})
    
    # Standard field matching
    print("\n📋 Standard Field Matching:")
    standard_fields = ['serialNumber', 'idNumber', 'fullNames', 'dateOfBirth', 
                       'dateOfIssue', 'gender', 'districtOfBirth', 'placeOfIssue']
    
    for field in standard_fields:
        if field in match_results:
            result = match_results[field]
            status = result.get('status', 'Unknown')
            if status == 'Matched':
                print(f"   ✅ {field}: {status}")
            elif status == 'Not Matched':
                details = result.get('details', {})
                print(f"   ❌ {field}: {status}")
                print(f"      Expected: {details.get('expected', 'N/A')}")
                print(f"      Actual: {details.get('actual', 'N/A')}")
            else:
                print(f"   ⚠️  {field}: {status}")
    
    # v1.2 IPRS Validation Results
    print("\n📋 v1.2 IPRS Validation:")
    
    if 'serialNumberValidation' in match_results:
        sn_result = match_results['serialNumberValidation']
        status = sn_result.get('status', 'Unknown')
        icon = '✅' if status == 'MATCH' else '❌' if status == 'MISMATCH' else '⚠️'
        print(f"   {icon} Serial Number Validation: {status}")
        print(f"      Document: {sn_result.get('extracted_serial_number', 'N/A')}")
        print(f"      IPRS: {sn_result.get('iprs_serial_number', 'N/A')}")
        if sn_result.get('reason'):
            print(f"      Reason: {sn_result.get('reason')}")
    else:
        print("   ⚠️  Serial Number Validation: Not present in response")
    
    if 'genderValidation' in match_results:
        g_result = match_results['genderValidation']
        status = g_result.get('status', 'Unknown')
        icon = '✅' if status == 'MATCH' else '❌' if status == 'MISMATCH' else '⚠️'
        print(f"   {icon} Gender Validation: {status}")
        print(f"      Document: {g_result.get('extracted_gender', 'N/A')}")
        print(f"      IPRS: {g_result.get('iprs_gender', 'N/A')}")
        if g_result.get('reason'):
            print(f"      Reason: {g_result.get('reason')}")
    else:
        print("   ⚠️  Gender Validation: Not present in response")
    
    # Keywords checks
    if "keywords_checks" in results["results"]:
        print("\n📋 Keyword Checks:")
        for check in results["results"]["keywords_checks"]:
            icon = '✅' if check.get('result') else '❌'
            print(f"   {icon} {check.get('check')}")


def main():
    print("=" * 70)
    print("E2E National ID Validation Test - v1.2 Features")
    print("=" * 70)
    
    # Check if image exists
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Image not found: {IMAGE_PATH}")
        return 1
    
    print(f"📁 Image: {IMAGE_PATH}")
    
    # ID data for TIM.jpg - ID number 26465570
    id_data = {
        "idNumber": "26465570",
    }
    
    # Upload to S3
    s3_key = f"uploaded_kyc_docs/test_tim_{id_data.get('idNumber', 'unknown')}.jpg"
    try:
        s3_uri = upload_to_s3(IMAGE_PATH, S3_BUCKET, s3_key)
    except Exception as e:
        print(f"❌ Failed to upload to S3: {e}")
        return 1
    
    # Validate
    try:
        response = validate_nationalid(s3_uri, id_data)
        
        if response.status_code == 200:
            results = response.json()
            print("\n✅ Validation completed successfully!")
            analyze_results(results)
            
            # Print full response for debugging
            print("\n" + "=" * 70)
            print("FULL RESPONSE (for debugging)")
            print("=" * 70)
            pprint(results)
        else:
            print(f"\n❌ Validation failed with status {response.status_code}")
            print(response.text)
            return 1
            
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
