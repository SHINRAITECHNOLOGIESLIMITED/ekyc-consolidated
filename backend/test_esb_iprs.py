#!/usr/bin/env python3
"""
Test script to verify ESB IPRS connection and validate serial number/gender fields.
Tests the v1.2 feature requirements for Serial Number and Gender validation.
"""

import json
import boto3
import requests
from datetime import datetime

# Configuration
AWS_PROFILE = "pasha-eu"
AWS_REGION = "eu-west-1"
ESB_SECRET_NAME = "jubilee-ekyc-dev-jubilee-esb-ApiGateway-credentials"

# Test IDs from E2E tests
TEST_IDS = [
    {"id": "23667272", "name": "JANE WAIRIMU MAINA", "expected_gender": "F"},
    {"id": "32140017", "name": "EFFIE NJOKI NYAMBURA", "expected_gender": "F"},
    {"id": "36296352", "name": "JOEL MUUO", "expected_gender": "M"},
    {"id": "23224868", "name": "STEPHEN BIKO NYAMAI", "expected_gender": "M"},
]


def get_esb_credentials():
    """Retrieve ESB credentials from Secrets Manager"""
    try:
        session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
        secrets_client = session.client('secretsmanager')
        
        print(f"📋 Retrieving ESB credentials from: {ESB_SECRET_NAME}")
        response = secrets_client.get_secret_value(SecretId=ESB_SECRET_NAME)
        credentials = json.loads(response['SecretString'])
        
        print(f"✅ Retrieved credentials for: {credentials.get('username', 'N/A')}")
        return credentials
        
    except Exception as e:
        print(f"❌ Error retrieving credentials: {e}")
        return None


def get_esb_token(credentials: dict) -> str:
    """Authenticate with ESB and get JWT token"""
    try:
        # ESB base URL
        base_url = "https://jubipay.jubileeinsurance.com"
        auth_url = f"{base_url}/api/auth/signin"
        
        login_data = {
            "username": credentials['username'],
            "password": credentials['password']
        }
        
        print(f"\n🔐 Authenticating with ESB...")
        print(f"   URL: {auth_url}")
        
        response = requests.post(
            auth_url,
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Authentication failed: {response.text}")
            return None
        
        token_data = response.json()
        full_token = f"{token_data['tokenType']} {token_data['accessToken']}"
        print(f"✅ Authentication successful!")
        return full_token
        
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return None


def test_iprs_search(token: str, id_number: str, expected_name: str = None):
    """Test IPRS search and validate response fields"""
    try:
        base_url = "https://jubipay.jubileeinsurance.com"
        business = "LIFE_BUSINESS"
        url = f"{base_url}/iprs/searchV2/{business}"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": token
        }
        
        data = {
            "identifier": "ID_NUMBER",
            "value": id_number
        }
        
        print(f"\n🔍 Testing IPRS search for ID: {id_number}")
        print(f"   URL: {url}")
        
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ IPRS search failed: {response.text}")
            return None
        
        result = response.json()
        
        if not result.get('success'):
            print(f"❌ IPRS lookup unsuccessful: {result.get('error')}")
            return result
        
        iprs_data = result.get('data', {})
        
        print(f"\n✅ IPRS Response:")
        print(f"   ID Number: {iprs_data.get('idNumber')}")
        print(f"   Serial Number: {iprs_data.get('serialNumber')} {'✅' if iprs_data.get('serialNumber') else '❌ MISSING'}")
        print(f"   Gender: {iprs_data.get('gender')} {'✅' if iprs_data.get('gender') else '❌ MISSING'}")
        print(f"   First Name: {iprs_data.get('firstName')}")
        print(f"   Surname: {iprs_data.get('surname')}")
        print(f"   Date of Birth: {iprs_data.get('dateOfBirth')}")
        print(f"   Place of Birth: {iprs_data.get('placeOfBirth')}")
        print(f"   Photo Available: {'Yes' if iprs_data.get('photo') else 'No'}")
        
        # Validate v1.2 required fields
        print(f"\n📋 v1.2 Field Validation:")
        serial_ok = iprs_data.get('serialNumber') is not None
        gender_ok = iprs_data.get('gender') is not None
        print(f"   Serial Number field: {'✅ Present' if serial_ok else '❌ Missing'}")
        print(f"   Gender field: {'✅ Present' if gender_ok else '❌ Missing'}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in IPRS search: {e}")
        return None


def test_iprs_ping(token: str):
    """Test IPRS ping endpoint"""
    try:
        base_url = "https://jubipay.jubileeinsurance.com"
        business = "LIFE_BUSINESS"
        url = f"{base_url}/iprs/pingIprs/{business}"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": token
        }
        
        print(f"\n🏓 Testing IPRS ping...")
        print(f"   URL: {url}")
        
        response = requests.post(url, json={}, headers=headers, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ IPRS service is available!")
            return True
        else:
            print(f"❌ IPRS ping failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error pinging IPRS: {e}")
        return False


def main():
    print("=" * 70)
    print("ESB IPRS Connection Test - v1.2 Feature Validation")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Step 1: Get credentials
    credentials = get_esb_credentials()
    if not credentials:
        print("\n❌ Failed to retrieve credentials. Exiting.")
        return 1
    
    # Step 2: Get token
    token = get_esb_token(credentials)
    if not token:
        print("\n❌ Failed to get ESB token. Exiting.")
        return 1
    
    # Step 3: Test IPRS ping
    ping_ok = test_iprs_ping(token)
    
    # Step 4: Test IPRS search with known IDs
    print("\n" + "=" * 70)
    print("Testing IPRS Search with Known IDs")
    print("=" * 70)
    
    results = []
    for test_case in TEST_IDS:  # Test all IDs
        result = test_iprs_search(
            token, 
            test_case['id'], 
            test_case['name']
        )
        if result:
            results.append({
                "id": test_case['id'],
                "success": result.get('success', False),
                "has_serial": result.get('data', {}).get('serialNumber') is not None,
                "has_gender": result.get('data', {}).get('gender') is not None,
            })
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"IPRS Ping: {'✅ OK' if ping_ok else '❌ Failed'}")
    print(f"Tests Run: {len(results)}")
    
    all_have_serial = all(r['has_serial'] for r in results)
    all_have_gender = all(r['has_gender'] for r in results)
    
    print(f"\nv1.2 Feature Readiness:")
    print(f"   Serial Number Validation: {'✅ Ready' if all_have_serial else '❌ Not Ready'}")
    print(f"   Gender Validation: {'✅ Ready' if all_have_gender else '❌ Not Ready'}")
    
    if all_have_serial and all_have_gender:
        print(f"\n🎉 ESB is ready for v1.2 Serial Number and Gender validation!")
    else:
        print(f"\n⚠️  Some required fields are missing from IPRS response.")
    
    return 0


if __name__ == "__main__":
    exit(main())
