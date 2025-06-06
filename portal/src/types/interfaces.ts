export interface CognitoUser {
    username: string;
    email?: string;
    enabled: boolean;
    userStatus: string;
    userCreateDate: string;
}
export interface DashboardMetrics {
    documentValidations: number;
    documentVerifications: number;
    backGroundChecks: number;
    agentRegistrations: number;
    customerRegistrations: number;
    apiCalls: number;
    apiCallsCachehits: number;
    faceLivenessCount: number;
}