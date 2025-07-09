const API_BASE_URL = 'https://k4m88497ad.execute-api.eu-west-1.amazonaws.com/Prod';
const VALIDATED_DOCS_BASE_S3_PATH = 's3://kyc-raw-documents-jubilee-ekyc-backend-851725215817';
const UPLOADED_DOCS_BASE_S3_PATH = 's3://amplify-dnw02dhxhpu7h-mai-kycdocumentsbucketa4bf11-wxhjqijfdzdz';
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
    API_ENDPOINTS: {
        CREATE_SESSION: `${API_BASE_URL}/faceliveness`,
        GET_RESULTS: `${API_BASE_URL}/faceliveness`
    }
};
