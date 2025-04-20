import type {Schema} from "@/../amplify/data/resource";
import type {LivenessSession,KYCDocument} from '@/types/models';
import {generateClient} from 'aws-amplify/api';

export const client = generateClient<Schema>();


export const fetchLivenessSessions = async (): Promise<LivenessSession[]> => {
    const response = await client.models.LivenessSession.list({
        limit: 5000
    });
    const sortedData = response.data.sort((a, b) => {
        return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
    });
    return sortedData;
};

export const fetchLivenessSession = async (sessionId: string): Promise<LivenessSession | null> => {
    const response = await client.models.LivenessSession.get({
        sessionId: sessionId
    });
    return response.data;
};

export const fetchKYCDocuments = async (): Promise<KYCDocument[]> => {
    const response = await client.models.KYCDocument.list({
        limit: 5000
    });
    return response.data;
};
export const fetchDocument = async (documentId: string): Promise<KYCDocument | null> => {
    const response = await client.models.KYCDocument.get({
        documentId: documentId
    });
    return response.data;
};