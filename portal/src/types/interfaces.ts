export interface CognitoUser {
    username: string;
    email?: string;
    enabled: boolean;
    userStatus: string;
    userCreateDate: string;
}
export interface DashboardMetrics {
    documentValidations:number;
    documentVerifications:number;
    apiCalls: number;
    faceLivenessCount: number;
}