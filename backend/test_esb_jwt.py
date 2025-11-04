#!/usr/bin/env python3
"""
Test script to retrieve and analyze ESB JWT tokens.
This helps us understand the token structure for Lambda Authorizer implementation.
"""

import json
import base64
import boto3
import requests
from datetime import datetime

# Configuration
AWS_PROFILE = None  # Use default credentials (or set to "jubilee-ekyc" if needed)
AWS_REGION = "eu-west-1"

def decode_jwt_without_verification(token: str) -> dict:
    """Decode JWT header and payload without verification"""
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]

        parts = token.split('.')
        if len(parts) != 3:
            print(f"❌ Invalid JWT structure. Expected 3 parts, got {len(parts)}")
            return None

        # Decode header
        header_bytes = base64.urlsafe_b64decode(parts[0] + '==')  # Add padding
        header = json.loads(header_bytes)

        # Decode payload
        payload_bytes = base64.urlsafe_b64decode(parts[1] + '==')  # Add padding
        payload = json.loads(payload_bytes)

        return {
            'header': header,
            'payload': payload,
            'signature': parts[2][:20] + '...'  # First 20 chars of signature
        }
    except Exception as e:
        print(f"❌ Error decoding JWT: {e}")
        return None

def get_esb_credentials():
    """Retrieve ESB credentials from Secrets Manager"""
    try:
        if AWS_PROFILE:
            session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
        else:
            session = boto3.Session(region_name=AWS_REGION)
        secrets_client = session.client('secretsmanager')

        # First, we need to find the secret ARN
        # Let's list secrets to find it
        print("📋 Searching for Jubilee ESB secret...")
        paginator = secrets_client.get_paginator('list_secrets')

        esb_secret_arn = None
        for page in paginator.paginate():
            for secret in page['SecretList']:
                if 'jubilee-esb' in secret['Name'].lower() or 'esb-api' in secret['Name'].lower():
                    esb_secret_arn = secret['ARN']
                    print(f"✅ Found ESB secret: {secret['Name']}")
                    print(f"   ARN: {esb_secret_arn}")
                    break
            if esb_secret_arn:
                break

        if not esb_secret_arn:
            print("❌ ESB secret not found. Looking for secrets with 'jubilee-esb' in name.")
            print("\nAvailable secrets:")
            for page in paginator.paginate():
                for secret in page['SecretList']:
                    print(f"  - {secret['Name']}")
            return None

        # Get the secret value
        response = secrets_client.get_secret_value(SecretId=esb_secret_arn)
        credentials = json.loads(response['SecretString'])

        print(f"\n📦 Retrieved ESB credentials:")
        print(f"   Base URL: {credentials.get('baseurl', 'N/A')}")
        print(f"   Business: {credentials.get('business', 'N/A')}")
        print(f"   Username: {credentials.get('username', 'N/A')[:5]}...")

        return credentials

    except Exception as e:
        print(f"❌ Error retrieving credentials: {e}")
        return None

def retrieve_esb_jwt_token(credentials: dict) -> str:
    """Retrieve JWT token from ESB"""
    try:
        auth_url = f"{credentials['baseurl']}/api/auth/signin"

        login_data = {
            "username": credentials['username'],
            "password": credentials['password']
        }

        headers = {
            "Content-Type": "application/json"
        }

        print(f"\n🔐 Authenticating with ESB...")
        print(f"   URL: {auth_url}")

        response = requests.post(
            auth_url,
            json=login_data,
            headers=headers,
            timeout=15
        )

        print(f"   Status: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Authentication failed:")
            print(f"   Response: {response.text}")
            return None

        token_data = response.json()
        print(f"\n✅ Authentication successful!")
        print(f"   Token Type: {token_data.get('tokenType', 'N/A')}")

        # Return full JWT string
        full_token = f"{token_data['tokenType']} {token_data['accessToken']}"
        return full_token

    except Exception as e:
        print(f"❌ Error retrieving JWT token: {e}")
        return None

def analyze_jwt_token(jwt_token: str):
    """Analyze and display JWT token details"""
    print("\n" + "="*70)
    print("JWT TOKEN ANALYSIS")
    print("="*70)

    decoded = decode_jwt_without_verification(jwt_token)

    if not decoded:
        return

    print("\n📋 HEADER:")
    print(json.dumps(decoded['header'], indent=2))

    print("\n📋 PAYLOAD:")
    payload = decoded['payload']
    print(json.dumps(payload, indent=2))

    print("\n🔍 KEY CLAIMS:")

    # Common JWT claims
    if 'iss' in payload:
        print(f"   Issuer (iss): {payload['iss']}")
    if 'sub' in payload:
        print(f"   Subject (sub): {payload['sub']}")
    if 'aud' in payload:
        print(f"   Audience (aud): {payload['aud']}")
    if 'exp' in payload:
        exp_time = datetime.fromtimestamp(payload['exp'])
        now = datetime.now()
        time_left = (exp_time - now).total_seconds() / 60
        print(f"   Expiration (exp): {exp_time} ({time_left:.1f} minutes from now)")
    if 'iat' in payload:
        iat_time = datetime.fromtimestamp(payload['iat'])
        print(f"   Issued At (iat): {iat_time}")
    if 'nbf' in payload:
        nbf_time = datetime.fromtimestamp(payload['nbf'])
        print(f"   Not Before (nbf): {nbf_time}")

    print(f"\n🔒 SIGNATURE (first 20 chars): {decoded['signature']}")

    print("\n" + "="*70)
    print("LAMBDA AUTHORIZER REQUIREMENTS")
    print("="*70)
    print("\nBased on this token, the Lambda Authorizer should:")
    print("1. Extract token from Authorization header")
    print("2. Verify token structure (3 parts separated by dots)")

    if 'exp' in payload:
        print("3. ✅ Verify expiration claim exists - CHECK expiration")
    else:
        print("3. ⚠️  No expiration claim found - CHECK if this is expected")

    if 'iss' in payload:
        print(f"4. ✅ Verify issuer: {payload['iss']}")
    else:
        print("4. ⚠️  No issuer claim - May need to validate differently")

    print("\n💡 RECOMMENDATIONS:")
    if 'iss' in payload and 'cognito' in payload['iss'].lower():
        print("   - Token appears to be from Cognito")
        print("   - Can use Cognito JWKS for signature verification")
    else:
        print("   - Token is NOT from Cognito")
        print("   - May need custom validation logic or shared secret")
        print("   - Since ESB already authenticated, Lambda may only need basic validation")

def main():
    print("🚀 ESB JWT Token Test Script")
    print("="*70)

    # Step 1: Get ESB credentials
    credentials = get_esb_credentials()
    if not credentials:
        print("\n❌ Failed to retrieve ESB credentials. Exiting.")
        return 1

    # Step 2: Get JWT token
    jwt_token = retrieve_esb_jwt_token(credentials)
    if not jwt_token:
        print("\n❌ Failed to retrieve JWT token. Exiting.")
        return 1

    # Step 3: Analyze token
    analyze_jwt_token(jwt_token)

    print("\n✅ Test complete!")
    return 0

if __name__ == "__main__":
    exit(main())
