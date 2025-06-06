const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://ukj5fnux32.execute-api.eu-west-1.amazonaws.com/Prod';
const VALIDATED_DOCS_BASE_S3_PATH = process.env.NEXT_PUBLIC_API_URL || 's3://jubilee-ekyc-backend-kycdocume-842206816107';
const API_HEADERS = {
    'Content-Type': 'application/json'
};

export const API_CONFIG = {
    BASE_URL: API_BASE_URL,
    REGION: process.env.NEXT_PUBLIC_AWS_REGION || 'eu-west-1',
    API_HEADERS: API_HEADERS,
    VALIDATED_DOCS_BASE_S3_PATH:VALIDATED_DOCS_BASE_S3_PATH,
    SWAGGER_UI_URL: `${API_BASE_URL}/swagger-ui/`,
    API_ENDPOINTS: {
        CREATE_SESSION: `${API_BASE_URL}/faceliveness`,
        GET_RESULTS: `${API_BASE_URL}/faceliveness`,
        VALIDATION: `${API_BASE_URL}/document`
    }
};
