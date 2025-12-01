// Jubilee eKYC Backend API Configuration
// Uses environment variables for flexibility across environments
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://28q8ss40v1.execute-api.eu-west-1.amazonaws.com/Stage';
const UNIFIED_KYC_API_URL = `${API_BASE_URL}/kyc`;
const VALIDATED_DOCS_BASE_S3_PATH = process.env.NEXT_PUBLIC_VALIDATED_DOCS_BASE_S3_PATH || 's3://kyc-raw-documents-jubilee-ekyc-backend-339712884722';
const UPLOADED_DOCS_BASE_S3_PATH = process.env.NEXT_PUBLIC_UPLOADED_DOCS_BASE_S3_PATH || 's3://amplify-dnw02dhxhpu7h-mai-kycdocumentsbucketa4bf11-wxhjqijfdzdz';
const API_HEADERS = {
    'Content-Type': 'application/json'
};

export const API_CONFIG = {
    REGION: process.env.NEXT_PUBLIC_AWS_REGION || 'eu-west-1',
    API_HEADERS: API_HEADERS,
    VALIDATED_DOCS_BASE_S3_PATH: VALIDATED_DOCS_BASE_S3_PATH,
    UPLOADED_DOCS_BASE_S3_PATH: UPLOADED_DOCS_BASE_S3_PATH,
    SWAGGER_UI_URL: `${API_BASE_URL}/swagger-ui/`,
    API_BASE_URL: API_BASE_URL,
    UNIFIED_KYC_API_URL: UNIFIED_KYC_API_URL,
    API_ENDPOINTS: {
        CREATE_SESSION: `${API_BASE_URL}/faceliveness`,
        GET_RESULTS: `${API_BASE_URL}/faceliveness`,
        UNIFIED_KYC: UNIFIED_KYC_API_URL,
        // Legacy endpoints
        LEGACY_KYC_PROCESS: `${API_BASE_URL}/kyc/process`,
        VALIDATE_NATIONAL_ID: `${API_BASE_URL}/document/nationalid`,
        VALIDATE_PASSPORT: `${API_BASE_URL}/document/passport`,
        VALIDATE_KRA: `${API_BASE_URL}/document/krapincertificate`,
        VALIDATE_CR12: `${API_BASE_URL}/document/cr12`,
        VERIFY_NATIONAL_ID: `${API_BASE_URL}/government/nationalid`,
        VERIFY_PASSPORT: `${API_BASE_URL}/government/passport`,
        VERIFY_KRA: `${API_BASE_URL}/government/kra`,
        BACKGROUND_CHECK: `${API_BASE_URL}/backgroundcheck`,
        AGENT_REGISTRATION: `${API_BASE_URL}/agent-registration`,
        CUSTOMER_REGISTRATION: `${API_BASE_URL}/customer-registration`,
        STREAM_DOCUMENT: `${API_BASE_URL}/stream`
    }
};
