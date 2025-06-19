const API_BASE_URL = 'https://65mz46ka57.execute-api.eu-west-1.amazonaws.com/Prod';
const VALIDATED_DOCS_BASE_S3_PATH = 's3://jubilee-ekyc-backend-kycdocume-842206816107';
const UPLOADED_DOCS_BASE_S3_PATH = 's3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq';
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
