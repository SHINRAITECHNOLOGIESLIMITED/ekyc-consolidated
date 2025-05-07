import {DocumentResponse, LivenessResponse, SessionResponse} from "@/types/liveness";

import {API_CONFIG} from "@/constants/api";

import { fetchAuthSession } from 'aws-amplify/auth';

const getAuthHeaders = async () => {
    try {
        const session = await fetchAuthSession();
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.tokens?.accessToken.toString()}`,
            'X-Amz-Security-Token': session.tokens?.idToken?.toString() ?? "",
            'X-Api-Key': process.env.REACT_APP_API_KEY || ''
        };
    } catch (error) {
        console.error('Error getting authentication tokens:', error);
        throw new Error('Authentication failed. Please sign in again.');
    }
};

export const livenessApi = {
    createSession: async (): Promise<SessionResponse> => {
        const headers = await getAuthHeaders();
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
        const headers = await getAuthHeaders();
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
        s3Path: string
    }): Promise<DocumentResponse> => {
        const headers = await getAuthHeaders();
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
