#!/usr/bin/env python3
"""
Script to update Jubilee ESB and Portal secrets in AWS Secrets Manager.
This script reads ARNs and secret values from a .env file in the same directory
and updates the corresponding secrets in AWS Secrets Manager.
"""

import boto3
from dotenv import load_dotenv
from pathlib import Path
import os
import json


session = boto3.Session(profile_name='shinrai.devpost')
secrets_client = session.client('secretsmanager')


def update_secret(secret_arn, new_value: str):
    """
    Update a secret in AWS Secrets Manager.
    
    Args:
        secrets_client: The boto3 secrets manager client
        arn: The ARN of the secret to update
        new_value: The new value for the secret
        
    Returns:
        The response from the update_secret API call or None if an error occurred
    """
    try:
        print(f"\n{secret_arn}")
        response = secrets_client.update_secret(
            SecretId=secret_arn,
            SecretString=new_value
        )
        print(f"\tVersion ID: {response['VersionId']}")
        
        get_secret_value_response = secrets_client.get_secret_value(
            SecretId=secret_arn
        )
        secret = get_secret_value_response['SecretString']
        print(f"\tNewValue: {secret}")
        return response
    except Exception as e:
        print(f"\tError updating secret: {str(e)}")
        return None


def main():
    """Main function to execute the script."""
    # Load environment variables from .env file in the same directory
    script_dir = Path(__file__).parent.absolute()
    env_path = script_dir / '.env'
    load_dotenv(env_path)
    
    # Get secrets and ARNs from environment variables
    JUBILEE_ESB_SECRETS_ARN = os.getenv('JUBILEE_ESB_SECRETS_ARN',None)
    assert JUBILEE_ESB_SECRETS_ARN, "JUBILEE_ESB_SECRETS_ARN not found in .env file"
    
    JUBILEE_ESB_CREDENTIALS = os.getenv('JUBILEE_ESB_CREDENTIALS',None)
    assert JUBILEE_ESB_CREDENTIALS, "JUBILEE_ESB_CREDENTIALS not found in .env file"
    
    
    PORTAL_GRAPHQL_SECRETS_ARN = os.getenv('PORTAL_GRAPHQL_SECRETS_ARN',None)
    assert PORTAL_GRAPHQL_SECRETS_ARN, "PORTAL_GRAPHQL_SECRETS_ARN not found in .env file"
    
    PORTAL_GRAPHQL_CREDENTIALS = os.getenv('PORTAL_GRAPHQL_CREDENTIALS',None)
    assert PORTAL_GRAPHQL_CREDENTIALS, "PORTAL_GRAPHQL_CREDENTIALS not found in .env file"
    
    
    update_secret(JUBILEE_ESB_SECRETS_ARN, JUBILEE_ESB_CREDENTIALS)
    update_secret(PORTAL_GRAPHQL_SECRETS_ARN, PORTAL_GRAPHQL_CREDENTIALS)
    return 0


if __name__ == "__main__":
    exit(main())