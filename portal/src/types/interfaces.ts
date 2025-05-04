export interface CognitoUser {
    username: string;
    email?: string;
    enabled: boolean;
    userStatus: string;
    userCreateDate: string;
}
export interface DashboardMetrics {
    kycDocuments: number;
    apiCalls: number;
    faceLivenessCount: number;
}