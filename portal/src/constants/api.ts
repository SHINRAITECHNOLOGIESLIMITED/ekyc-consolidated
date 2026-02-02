// API Gateway URLs for jubilee-ekyc-dev stack (pasha-eu account)
// Stage endpoint auto-approves requests for testing (no auth required)
// Prod endpoint requires JWT Bearer token from ESB
const API_BASE_URL = 'https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage';
const UNIFIED_KYC_API_URL = 'https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc';
const VALIDATED_DOCS_BASE_S3_PATH = 's3://kyc-raw-documents-jubilee-ekyc-dev-686255958278';
const UPLOADED_DOCS_BASE_S3_PATH = 's3://maisha-verification-dev-686255958278';
const API_HEADERS = {
    'Content-Type': 'application/json'
};

export const API_CONFIG = {
    REGION: process.env.NEXT_PUBLIC_AWS_REGION || 'eu-west-1',
    API_HEADERS: API_HEADERS,
    VALIDATED_DOCS_BASE_S3_PATH:VALIDATED_DOCS_BASE_S3_PATH,
    UPLOADED_DOCS_BASE_S3_PATH:UPLOADED_DOCS_BASE_S3_PATH,
    SWAGGER_UI_URL: `${API_BASE_URL}/swagger-ui/`,
    API_BASE_URL: API_BASE_URL,
    UNIFIED_KYC_API_URL: UNIFIED_KYC_API_URL,
    API_ENDPOINTS: {
        CREATE_SESSION: `${API_BASE_URL}/faceliveness`,
        GET_RESULTS: `${API_BASE_URL}/faceliveness`,
        UNIFIED_KYC: UNIFIED_KYC_API_URL
    }
};
