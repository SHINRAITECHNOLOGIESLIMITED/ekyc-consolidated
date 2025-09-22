"""
Core KYC orchestration logic.
Manages the complete KYC workflow by invoking existing Lambda functions
and aggregating results into a consolidated response.
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

import boto3
from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()


class KYCOrchestrator:
    """
    Orchestrates the complete KYC verification workflow.
    """

    def __init__(self):
        self.lambda_client = boto3.client('lambda')
        self.start_time = None
        self.function_arns = self._get_function_arns()

    def _get_function_arns(self) -> Dict[str, str]:
        """
        Get Lambda function ARNs from environment variables.
        """
        return {
            'document_validation': os.environ.get('DOCUMENT_VALIDATION_FUNCTION'),
            'government_verification': os.environ.get('GOVERNMENT_VERIFICATION_FUNCTION'),
            'background_check': os.environ.get('BACKGROUND_CHECK_FUNCTION'),
            'face_liveness': os.environ.get('FACE_LIVENESS_FUNCTION'),
            'certification': os.environ.get('CERTIFICATION_FUNCTION')
        }

    @tracer.capture_method
    def process_kyc(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main orchestration method for KYC processing.

        Args:
            request_data: Consolidated KYC request data

        Returns:
            Consolidated KYC response with all verification results
        """
        self.start_time = time.time()
        kyc_id = str(uuid.uuid4())

        logger.info(f"Starting KYC processing for ID: {kyc_id}")

        # Initialize response structure
        response = {
            'kycId': kyc_id,
            'overallStatus': 'processing',
            'processType': request_data.get('processType'),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'processingTime': 0,
            'results': {},
            'errors': [],
            'metadata': {
                'functionsInvoked': [],
                'totalSteps': 0,
                'successfulSteps': 0
            }
        }

        try:
            # Extract configuration
            options = request_data.get('options', {})

            # Step 1: Document Validation
            doc_results = self._process_document_validation(request_data, response)

            # Step 2: Government Verification
            gov_results = self._process_government_verification(request_data, response)

            # Step 3: Background Check (optional)
            bg_results = {}
            if options.get('includeBackgroundCheck', False):
                bg_results = self._process_background_check(request_data, response)

            # Step 4: Face Liveness (optional)
            liveness_results = {}
            if options.get('includeFaceLiveness', False):
                liveness_results = self._process_face_liveness(request_data, response)

            # Step 5: Certification (optional)
            if options.get('generateCertificate', True):
                self._process_certification(
                    request_data, response, doc_results, gov_results, bg_results, liveness_results
                )

            # Calculate final status and response
            response = self._finalize_response(response)

            return response

        except Exception as e:
            logger.error(f"Fatal error in KYC processing: {e}")
            response['overallStatus'] = 'failed'
            response['errors'].append({
                'step': 'orchestration',
                'code': 'FATAL_ERROR',
                'message': 'Fatal error occurred during KYC processing',
                'details': str(e)
            })
            return self._finalize_response(response)

    @tracer.capture_method
    def _process_document_validation(self, request_data: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process document validation steps.
        """
        logger.info("Starting document validation phase")

        documents = request_data.get('documents', {})
        personal_data = request_data.get('personalData', {})
        process_type = request_data.get('processType')

        validation_results = {}

        try:
            # National ID validation (for customers and individual agents)
            if process_type in ['customer', 'individual_agent'] and documents.get('nationalIdUrl'):
                national_id_result = self._invoke_document_validation(
                    'nationalid',
                    {
                        'uploadedDocumentUrl': documents['nationalIdUrl'],
                        'idNumber': personal_data['idNumber'],
                        'fullNames': personal_data['name'],
                        'dateOfBirth': personal_data['dateOfBirth']
                    }
                )
                validation_results['nationalId'] = national_id_result
                response['metadata']['functionsInvoked'].append('DocumentValidation-NationalID')

            # Passport validation (if provided)
            if documents.get('passportUrl'):
                passport_result = self._invoke_document_validation(
                    'passport',
                    {
                        'uploadedDocumentUrl': documents['passportUrl'],
                        'passportNumber': personal_data.get('passportNumber', ''),
                        'fullNames': personal_data['name'],
                        'dateOfBirth': personal_data['dateOfBirth']
                    }
                )
                validation_results['passport'] = passport_result
                response['metadata']['functionsInvoked'].append('DocumentValidation-Passport')

            # KRA validation (if provided)
            if documents.get('kraUrl'):
                kra_result = self._invoke_document_validation(
                    'krapincertificate',
                    {
                        'uploadedDocumentUrl': documents['kraUrl'],
                        'kraPin': personal_data['pinNumber'],
                        'fullNames': personal_data['name'],
                        'idNumber': personal_data['idNumber']
                    }
                )
                validation_results['kraPin'] = kra_result
                response['metadata']['functionsInvoked'].append('DocumentValidation-KRA')

            # Company certificate validation (for business agents)
            if process_type == 'business_agent' and documents.get('companyCertificateUrl'):
                company_result = self._invoke_document_validation(
                    'cr12',
                    {
                        'uploadedDocumentUrl': documents['companyCertificateUrl'],
                        'businessNumber': personal_data.get('businessNumber', ''),
                        'businessName': personal_data['name']
                    }
                )
                validation_results['companyCertificate'] = company_result
                response['metadata']['functionsInvoked'].append('DocumentValidation-Company')

            # Determine overall document validation status
            doc_status = self._determine_step_status(validation_results)
            response['results']['documentValidation'] = {
                'status': doc_status,
                **validation_results
            }

            if doc_status == 'success':
                response['metadata']['successfulSteps'] += 1

            logger.info(f"Document validation completed with status: {doc_status}")
            return validation_results

        except Exception as e:
            logger.error(f"Error in document validation phase: {e}")
            response['results']['documentValidation'] = {
                'status': 'failed',
                'error': str(e)
            }
            response['errors'].append({
                'step': 'document_validation',
                'code': 'DOCUMENT_VALIDATION_ERROR',
                'message': 'Document validation phase failed',
                'details': str(e)
            })
            return {}

    @tracer.capture_method
    def _process_government_verification(self, request_data: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process government verification steps.
        """
        logger.info("Starting government verification phase")

        personal_data = request_data.get('personalData', {})
        process_type = request_data.get('processType')

        verification_results = {}

        try:
            # National ID verification (for customers and individual agents)
            if process_type in ['customer', 'individual_agent']:
                national_id_verification = self._invoke_government_verification(
                    'nationalid',
                    {
                        'idNumber': personal_data['idNumber'],
                        'fullNames': personal_data['name'],
                        'dateOfBirth': personal_data['dateOfBirth'],
                        'gender': personal_data.get('gender', '')
                    }
                )
                verification_results['nationalIdVerification'] = national_id_verification
                response['metadata']['functionsInvoked'].append('GovernmentVerification-NationalID')

            # KRA verification
            kra_verification = self._invoke_government_verification(
                'kra',
                {
                    'idNumber': personal_data['idNumber'],
                    'pin': personal_data['pinNumber'],
                    'taxPayerName': personal_data['name']
                }
            )
            verification_results['kraVerification'] = kra_verification
            response['metadata']['functionsInvoked'].append('GovernmentVerification-KRA')

            # Determine overall government verification status
            gov_status = self._determine_step_status(verification_results)
            response['results']['governmentVerification'] = {
                'status': gov_status,
                **verification_results
            }

            if gov_status == 'success':
                response['metadata']['successfulSteps'] += 1

            logger.info(f"Government verification completed with status: {gov_status}")
            return verification_results

        except Exception as e:
            logger.error(f"Error in government verification phase: {e}")
            response['results']['governmentVerification'] = {
                'status': 'failed',
                'error': str(e)
            }
            response['errors'].append({
                'step': 'government_verification',
                'code': 'GOVERNMENT_VERIFICATION_ERROR',
                'message': 'Government verification phase failed',
                'details': str(e)
            })
            return {}

    @tracer.capture_method
    def _process_background_check(self, request_data: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process background check step.
        """
        logger.info("Starting background check phase")

        personal_data = request_data.get('personalData', {})

        try:
            # Split name into first and last name for LexisNexis
            name_parts = personal_data['name'].split()
            first_name = name_parts[0]
            last_name = name_parts[-1] if len(name_parts) > 1 else name_parts[0]
            middle_name = ' '.join(name_parts[1:-1]) if len(name_parts) > 2 else ''

            background_check_data = {
                'firstName': first_name,
                'lastName': last_name,
                'gender': personal_data.get('gender', ''),
                'dateOfBirth': personal_data['dateOfBirth'],
                'nationalIdentificationNumber': personal_data['idNumber']
            }

            if middle_name:
                background_check_data['middleName'] = middle_name

            bg_result = self._invoke_background_check(background_check_data)

            response['results']['backgroundCheck'] = {
                'status': 'success' if bg_result.get('success', False) else 'failed',
                **bg_result
            }
            response['metadata']['functionsInvoked'].append('BackgroundCheck')

            if bg_result.get('success', False):
                response['metadata']['successfulSteps'] += 1

            logger.info("Background check completed")
            return bg_result

        except Exception as e:
            logger.error(f"Error in background check phase: {e}")
            response['results']['backgroundCheck'] = {
                'status': 'failed',
                'error': str(e)
            }
            response['errors'].append({
                'step': 'background_check',
                'code': 'BACKGROUND_CHECK_ERROR',
                'message': 'Background check phase failed',
                'details': str(e)
            })
            return {}

    @tracer.capture_method
    def _process_face_liveness(self, request_data: Dict[str, Any], response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process face liveness step.
        """
        logger.info("Starting face liveness phase")

        try:
            # Create face liveness session
            liveness_data = {
                'action': 'create',
                'userId': response['kycId']  # Use KYC ID as user identifier
            }

            liveness_result = self._invoke_face_liveness(liveness_data)

            response['results']['faceLiveness'] = {
                'status': 'success' if liveness_result.get('sessionId') else 'failed',
                **liveness_result
            }
            response['metadata']['functionsInvoked'].append('FaceLiveness')

            if liveness_result.get('sessionId'):
                response['metadata']['successfulSteps'] += 1

            logger.info("Face liveness processing completed")
            return liveness_result

        except Exception as e:
            logger.error(f"Error in face liveness phase: {e}")
            response['results']['faceLiveness'] = {
                'status': 'failed',
                'error': str(e)
            }
            response['errors'].append({
                'step': 'face_liveness',
                'code': 'FACE_LIVENESS_ERROR',
                'message': 'Face liveness phase failed',
                'details': str(e)
            })
            return {}

    @tracer.capture_method
    def _process_certification(self, request_data: Dict[str, Any], response: Dict[str, Any],
                              doc_results: Dict, gov_results: Dict, bg_results: Dict,
                              liveness_results: Dict) -> Dict[str, Any]:
        """
        Process certification step.
        """
        logger.info("Starting certification phase")

        process_type = request_data.get('processType')

        try:
            # Determine certification path based on process type
            if process_type == 'customer':
                cert_path = '/certification/customer_registration'
            elif process_type == 'individual_agent':
                cert_path = '/certification/individual_agent_registration'
            elif process_type == 'business_agent':
                cert_path = '/certification/business_agent_registration'
            else:
                raise ValueError(f"Unknown process type: {process_type}")

            # Prepare certification data
            cert_data = {
                'registration': request_data,
                'documentValidation': doc_results,
                'governmentVerification': gov_results,
                'backgroundCheck': bg_results,
                'faceLiveness': liveness_results
            }

            cert_result = self._invoke_certification(cert_path, cert_data)

            response['results']['certification'] = {
                'status': 'success' if cert_result.get('s3Path') else 'failed',
                **cert_result
            }
            response['metadata']['functionsInvoked'].append('Certification')

            if cert_result.get('s3Path'):
                response['metadata']['successfulSteps'] += 1
                # Add certificate URL to top-level response
                response['certificateUrl'] = cert_result.get('certificateUrl', '')

            logger.info("Certification processing completed")
            return cert_result

        except Exception as e:
            logger.error(f"Error in certification phase: {e}")
            response['results']['certification'] = {
                'status': 'failed',
                'error': str(e)
            }
            response['errors'].append({
                'step': 'certification',
                'code': 'CERTIFICATION_ERROR',
                'message': 'Certification phase failed',
                'details': str(e)
            })
            return {}

    def _invoke_document_validation(self, doc_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke document validation Lambda function.
        """
        function_arn = self.function_arns['document_validation']

        lambda_payload = {
            'httpMethod': 'POST',
            'path': f'/document/{doc_type}',
            'body': json.dumps(payload)
        }

        return self._invoke_lambda_function(function_arn, lambda_payload)

    def _invoke_government_verification(self, verification_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke government verification Lambda function.
        """
        function_arn = self.function_arns['government_verification']

        lambda_payload = {
            'httpMethod': 'POST',
            'path': f'/government/{verification_type}',
            'body': json.dumps(payload)
        }

        return self._invoke_lambda_function(function_arn, lambda_payload)

    def _invoke_background_check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke background check Lambda function.
        """
        function_arn = self.function_arns['background_check']

        lambda_payload = {
            'httpMethod': 'POST',
            'path': '/backgroundcheck',
            'body': json.dumps(payload)
        }

        return self._invoke_lambda_function(function_arn, lambda_payload)

    def _invoke_face_liveness(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke face liveness Lambda function.
        """
        function_arn = self.function_arns['face_liveness']

        lambda_payload = {
            'httpMethod': 'POST',
            'path': '/faceliveness',
            'body': json.dumps(payload)
        }

        return self._invoke_lambda_function(function_arn, lambda_payload)

    def _invoke_certification(self, cert_path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke certification Lambda function.
        """
        function_arn = self.function_arns['certification']

        lambda_payload = {
            'httpMethod': 'POST',
            'path': cert_path,
            'body': json.dumps(payload)
        }

        return self._invoke_lambda_function(function_arn, lambda_payload)

    def _invoke_lambda_function(self, function_arn: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generic Lambda function invocation with error handling.
        """
        try:
            logger.info(f"Invoking Lambda function: {function_arn}")

            response = self.lambda_client.invoke(
                FunctionName=function_arn,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )

            # Parse response
            response_payload = json.loads(response['Payload'].read())

            # Check if the Lambda function returned an error
            if response_payload.get('statusCode', 200) >= 400:
                error_body = json.loads(response_payload.get('body', '{}'))
                logger.error(f"Lambda function returned error: {error_body}")
                return {
                    'success': False,
                    'error': error_body.get('message', 'Lambda function error'),
                    'statusCode': response_payload.get('statusCode')
                }

            # Parse successful response
            if 'body' in response_payload:
                body = json.loads(response_payload['body'])
                result = {
                    'success': True,
                    **body
                }
                # If body doesn't have 'success' field but we got here, it's successful
                if 'success' not in body:
                    result['success'] = True
                return result

            result = {
                'success': True,
                **response_payload
            }
            # If payload doesn't have 'success' field but we got here, it's successful
            if 'success' not in response_payload:
                result['success'] = True
            return result

        except Exception as e:
            logger.error(f"Error invoking Lambda function {function_arn}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _determine_step_status(self, results: Dict[str, Any]) -> str:
        """
        Determine the overall status of a processing step based on individual results.
        """
        if not results:
            return 'failed'

        successful_count = 0
        total_count = len(results)

        for result in results.values():
            if result.get('success', False) or result.get('status') == 'Valid':
                successful_count += 1

        if successful_count == total_count:
            return 'success'
        elif successful_count > 0:
            return 'partial'
        else:
            return 'failed'

    def _finalize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Finalize the response with processing time and overall status.
        """
        # Calculate processing time
        if self.start_time:
            response['processingTime'] = round((time.time() - self.start_time) * 1000)  # in milliseconds

        # Update metadata
        response['metadata']['totalSteps'] = len(response['results'])

        # Determine overall status
        if response['overallStatus'] == 'processing':
            successful_steps = response['metadata']['successfulSteps']
            total_steps = response['metadata']['totalSteps']

            if successful_steps == total_steps and len(response['errors']) == 0:
                response['overallStatus'] = 'success'
            elif successful_steps > 0:
                response['overallStatus'] = 'partial'
            else:
                response['overallStatus'] = 'failed'

        logger.info(f"KYC processing finalized with status: {response['overallStatus']}")
        return response