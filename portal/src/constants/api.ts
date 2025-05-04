const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://uvm0nml9b4.execute-api.eu-west-1.amazonaws.com/stage';
const API_HEADERS = {
    'Content-Type': 'application/json'
};

export const API_CONFIG = {
    BASE_URL: process.env.NEXT_PUBLIC_API_URL!,
    REGION: process.env.NEXT_PUBLIC_AWS_REGION || 'eu-west-1',
    API_HEADERS: API_HEADERS,
    API_ENDPOINTS: {
        CREATE_SESSION: `${API_BASE_URL}/faceliveness`,
        GET_RESULTS: `${API_BASE_URL}/faceliveness`,
        UPLOAD_DOCUMENT: `${API_BASE_URL}/uploaddocument`,
    }
};
