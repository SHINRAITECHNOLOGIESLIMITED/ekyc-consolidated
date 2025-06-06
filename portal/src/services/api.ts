import {DocumentValidationResponse, LivenessResponse, SessionResponse} from "@/types/liveness";

import {API_CONFIG} from "@/constants/api";

import { fetchAuthSession } from 'aws-amplify/auth';

const getAuthHeaders = async () => {
    try {
        const session = await fetchAuthSession();
        const idToken = session.tokens?.idToken?.toString() ?? "";
        console.log("Id Token",idToken);
        return {
            'Content-Type': 'application/json',
            'Authorization': idToken

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

export const eKYCApi = {
    validateDocument: async (document: string,payload: string): Promise<DocumentValidationResponse> => {
        const headers = await getAuthHeaders();
        const response = await fetch(`${API_CONFIG.API_ENDPOINTS.VALIDATION}/${document}`, {
            method: 'POST',
            headers,
            body: payload
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response.json();
    },

    
};

