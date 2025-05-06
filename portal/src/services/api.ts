import {DocumentResponse, LivenessResponse, SessionResponse} from "@/types/liveness";

import {API_CONFIG} from "@/constants/api";

const headers = {
    'Content-Type': 'application/json'
};

export const livenessApi = {
    createSession: async (): Promise<SessionResponse> => {
        const response = await fetch(API_CONFIG.API_ENDPOINTS.CREATE_SESSION, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                action: 'create'
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response.json();
    },

    getResults: async (sessionId: string): Promise<LivenessResponse> => {
        const response = await fetch(API_CONFIG.API_ENDPOINTS.GET_RESULTS, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                action: 'get_results',
                sessionId: sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response.json();
    }
};


export const documentApi = {
    uploadDocument: async (documentDetails: {
        customerId: string,
        documentType: string,
        s3Path: string,
        bucket: string
    }): Promise<DocumentResponse> => {
        const response = await fetch(API_CONFIG.API_ENDPOINTS.UPLOAD_DOCUMENT, {
            method: 'POST',
            headers,
            body: JSON.stringify(documentDetails)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response.json();
    },

};
