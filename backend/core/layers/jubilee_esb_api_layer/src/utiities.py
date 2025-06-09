import json
import os
import time
import hashlib
from http import HTTPStatus
from typing import Dict, Any

import boto3
import requests
from aws_lambda_powertools import Logger, Tracer
from aws_xray_sdk.core import xray_recorder
from botocore.exceptions import ClientError

logger = Logger()
tracer = Tracer()

JUBILEE_ESB_API_SECRET_ARN = os.getenv('JUBILEE_ESB_API_SECRET_ARN', None)
assert JUBILEE_ESB_API_SECRET_ARN, "JUBILEE_ESB_API_SECRET_ARN environment variable is not set"
JUBILEE_ESB_TOKEN_VALIDITY_MINS = 4.5

JUBILEEAPICACHE_TABLE_NAME = os.getenv('JUBILEEAPICACHE_TABLE_NAME', None)
assert JUBILEEAPICACHE_TABLE_NAME, "JUBILEEAPICACHE_TABLE_NAME environment variable is not set"

JUBILEEAPICACHE_TABLE_ARN = os.getenv('JUBILEEAPICACHE_TABLE_ARN', None)
assert JUBILEEAPICACHE_TABLE_ARN, "JUBILEEAPICACHE_TABLE_ARN environment variable is not set"

#cache table
dynamodb = boto3.resource('dynamodb')
cache_table = dynamodb.Table(JUBILEEAPICACHE_TABLE_NAME)

class JubileeESBError(Exception):
    """Custom exception for ESB validation errors"""
    pass


class JubileeESBUtilities:

    def __init__(self,portal):
        """Initialize Jubilee ESB API with AWS Secrets Manager configuration"""
        self.secrets_client = boto3.client('secretsmanager')
        self.portal = portal
        self.authorization_jwt = None
        self.authorization_jwt_time = None
        self._load_jubilee_esb_credentials()
    def _retrieve_jwt_token(self, username: str, password: str) -> str:
        try:
            login_data = {
                "username": username,
                "password": password
            }

            headers = {
                "Content-Type": "application/json"
            }
            # logger.info(f"Attempting to retrieve JWT token for {login_data}")
            start_time = time.time() * 1000
            response = requests.post(
                self.AUTH_URL,
                json=login_data,
                headers=headers,
                timeout=15
            )
            if response.status_code == HTTPStatus.OK:
                logger.info(f"Authentication response: {response.status_code}")
            else:
                logger.info(f"Authentication response: {response.text}")
            duration_ms = round(time.time() * 1000 - start_time)
            current_segment = xray_recorder.current_segment()
            trace_id = current_segment.trace_id if current_segment else ""
            self.portal.log_api_call(response, api_name="ESB", api_method="auth/signin",
                                     duration_ms=duration_ms,
                                     trace_id=trace_id, capture_data=False)
            response.raise_for_status()

            token_data = response.json()
            if not token_data.get('tokenType'):
                raise JubileeESBError("No tokenType received in authentication response")
            if not token_data.get('accessToken'):
                raise JubileeESBError("No accessToken received in authentication response")
            logger.info("Successfully retrieved ESB JWT token")
            return f"{token_data['tokenType']} {token_data['accessToken']}"

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve JWT token: {str(e)}")
            raise JubileeESBError(f"Authentication failed: {str(e)}")

    def _load_jubilee_esb_credentials(self) -> None:
        """Load API credentials from AWS Secrets Manager"""
        try:
            jubilee_esb_response = self.secrets_client.get_secret_value(
                SecretId=JUBILEE_ESB_API_SECRET_ARN
            )

            if 'SecretString' not in jubilee_esb_response:
                logger.error("Failed to load ESB credentials: SecretString not found")
                raise JubileeESBError("Failed to initialize ESB service: Secret value not found")
            secretString = jubilee_esb_response['SecretString']
            # logger.info(f"Successfully retrieved ESB credentials: {secretString}")
            credentials = json.loads(secretString)
            self.base_url = credentials['baseurl']
            self.business = credentials['business']
            self.AUTH_URL = f"{self.base_url}/api/auth/signin"
            username = credentials['username']
            password = credentials['password']

            if not username or not password:
                raise JubileeESBError("Missing username or password in credentials")
            logger.info("Successfully loaded Jubilee ESB credentials")
            return username, password
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                logger.error(f"Access denied to secret {JUBILEE_ESB_API_SECRET_ARN}: {str(e)}")
                raise JubileeESBError(f"Failed to initialize ESB service: Access denied to secret")
            elif e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.error(f"Secret {JUBILEE_ESB_API_SECRET_ARN} not found: {str(e)}")
                raise JubileeESBError(f"Failed to initialize ESB service: Secret not found")
            else:
                logger.error(f"Failed to load ESB credentials: {str(e)}")
                raise JubileeESBError(f"Failed to initialize ESB service: {str(e)}")

    @tracer.capture_method
    def make_api_call(self,
                      service: str,
                      api_method: str,
                      url: str,
                      data: Dict[str, Any], 
                      is_post: bool = True,
                      cache_ttl_seconds: int = 3600 * 24* 7):  # Default TTL of 1 week
        """
        Make API call with error handling and logging

        Args:
            service: Service name for logging eg IPRS,KRA,NexisLexis,
            api_method: Method of API being called for logging eg SearchById,validate_id
            url: API endpoint URL
            data: Request payload
            is_post: true if http method is POST other it will call GET
            cache_ttl_seconds: Time to live for cache in seconds (default: 1 hour)
        """
        try:            
            # Cache miss or error, proceed with API call
            current_segment = xray_recorder.current_segment()
            trace_id = current_segment.trace_id if current_segment else None

            # Create a cache key based on the request parameters and hash it
            raw_key = f"{service}:{api_method}:{url}:{json.dumps(data, sort_keys=True)}"
            cache_key = hashlib.sha256(raw_key.encode()).hexdigest()
            
            if url != self.AUTH_URL:
                try:
                    cache_response = cache_table.get_item(Key={'cache_key': cache_key})
                    
                    # If item exists in cache and hasn't expired
                    if 'Item' in cache_response:
                        item = cache_response['Item']
                        expiry_time = item.get('expiry_time', 0)
                        
                        # Check if cache is still valid
                        if int(time.time()) < expiry_time:
                            logger.info(f"Jubilee ESB: {service} API call retrieved from cache")
                            cached_data = json.loads(item['response_data'])
                            response = requests.Response()
                            response.status_code = HTTPStatus.OK
                            response.headers = {
                                "Content-Type": "application/json"
                            }
                            response._content = json.dumps(cached_data).encode('utf-8')
                            logger.info(response.json())
                            self.portal.log_api_call(None, api_name=service, api_method=api_method, duration_ms=0,
                                     trace_id=trace_id,cacheHit=True, capture_data=True)
                            return response
                except ClientError as e:
                    logger.warning(f"Cache retrieval error: {str(e)}")
            
            # re-authenticating every four and half a minute as JWT access tokens are valid for 5 mins only
            new_jwt = False
            if self.authorization_jwt is None or self.authorization_jwt_time is None:
                new_jwt = True
            elif int(time.time()) - self.authorization_jwt_time > 60 * JUBILEE_ESB_TOKEN_VALIDITY_MINS:
                new_jwt = True
                
            if new_jwt:
                username,password =   self._load_jubilee_esb_credentials()
                self.authorization_jwt = self._retrieve_jwt_token(username, password)
                self.authorization_jwt_time = int(time.time())
            headers = {
                "Authorization": self.authorization_jwt,
                "Content-Type": "application/json"
            }
            start_time = time.time() * 1000
            if is_post:
                response = requests.post(
                    f"{self.base_url}{url}",
                    json=data,
                    headers=headers,
                    timeout=240
                )
            else:
                response = requests.get(
                    f"{self.base_url}{url}",
                    headers=headers,
                    timeout=240
                )
            duration_ms = round(time.time() * 1000 - start_time)
            self.portal.log_api_call(response, api_name=service, api_method=api_method, duration_ms=duration_ms,
                                     trace_id=trace_id, capture_data=True)
            # response.raise_for_status()
            
            # Store in cache if successful
            if url != self.AUTH_URL:
                if response.status_code in [HTTPStatus.OK,HTTPStatus.CREATED, HTTPStatus.ACCEPTED]:
                    try:
                        response_data = response.json()
                        expiry_time = int(time.time()) + cache_ttl_seconds
                        cache_table.put_item(
                            Item={
                                'cache_key': cache_key,
                                'service': service,
                                'api_method': api_method,
                                'response_data': json.dumps(response_data),
                                'expiry_time': expiry_time,
                                'cached_at': int(time.time())
                            }
                        )
                    except ClientError as e:
                        logger.warning(f"Cache storage error: {str(e)}")

            logger.info(f"Jubilee ESB: {service} API call successful")
            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Jubilee ESB: {service} API call failed: {str(e)}")
            raise JubileeESBError(f"{service} API call failed: {str(e)}")
