export interface CognitoUser {
    username: string;
    email?: string;
    enabled: boolean;
    userStatus: string;
    userCreateDate: string;
}
