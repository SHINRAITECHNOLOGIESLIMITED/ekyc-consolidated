import type {Schema} from "@/../amplify/data/resource";
import type {KYCDocument, LivenessSession} from '@/types/models';
import {generateClient} from 'aws-amplify/api';
import {CognitoUser} from "@/types/interfaces";
import { CognitoIdentityProviderClient, ListUsersCommand } from '@aws-sdk/client-cognito-identity-provider';
import {fetchAuthSession} from 'aws-amplify/auth';
import amplifyConfig from '@/../amplify_outputs.json' assert { type: 'json' };
interface AmplifyConfig {
    auth: {
        user_pool_id: string;
        aws_region: string;
        user_pool_client_id: string;
        identity_pool_id: string;
        mfa_methods: string[];
        standard_required_attributes: string[];
        username_attributes: string[];
        unauthenticated_identities_enabled: boolean;
    };
    data: {
        // Add data structure if needed
    };
    version: string;
}
const config = amplifyConfig as AmplifyConfig;

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
const listUsers = async (limit = 20, paginationToken?: string): Promise<{
    users: CognitoUser[],
    nextToken?: string
}> => {
    try {
        // Get values from Amplify configuration
        const userPoolId = config.auth.user_pool_id;
        const region = config.auth.aws_region;

        if (!userPoolId) {
            throw new Error('UserPoolId not found in Amplify configuration');
        }

        if (!region) {
            throw new Error('Region not found in Amplify configuration');
        }

        const { credentials } = await fetchAuthSession();

        const client = new CognitoIdentityProviderClient({
            credentials,
            region
        });

        const command = new ListUsersCommand({
            UserPoolId: userPoolId,
            Limit: limit,
            PaginationToken: paginationToken
        });

        const response = await client.send(command);

        const formattedUsers: CognitoUser[] = response.Users?.map(user => ({
            username: user.Username || '',
            email: user.Attributes?.find(attr => attr.Name === 'email')?.Value,
            enabled: user.Enabled || false,
            userStatus: user.UserStatus || '',
            userCreateDate: user.UserCreateDate ?
                new Date(user.UserCreateDate).toLocaleString() : ''
        })) || [];

        return {
            users: formattedUsers,
            nextToken: response.PaginationToken
        };

    } catch (error) {
        console.error('Error fetching users:', error);
        throw error;
    }
};
export const fetchUsers = async (): Promise<CognitoUser[]> => {
    try {
        const {users} = await listUsers(5000);
        return users
    } catch (error) {
        // Handle error
        console.log(error);
        return []
    }
};