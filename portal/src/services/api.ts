import {DocumentResponse, LivenessResponse, SessionResponse} from "@/types/liveness";

import {API_CONFIG} from "@/constants/api";

import { fetchAuthSession } from 'aws-amplify/auth';

const getAuthHeaders = async () => {
    try {
        const session = await fetchAuthSession();
        // const accessToken = `${session.tokens?.accessToken.toString()}`;
        // console.log("Access Token:", accessToken);
        const idToken = session.tokens?.idToken?.toString() ?? "";
        // console.log("Id Token",idToken);
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


export const documentApi = {
    uploadDocument: async (documentDetails: {
        customerId: string,
        url: string
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
