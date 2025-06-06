import type { Schema } from "@/../amplify/data/resource";
import type {
  Agent,
  APICall,
  BackGroundCheck,
  Customer,
  DocumentValidation,
  DocumentVerification,
  LivenessSession,
} from "@/types/models";
import { generateClient } from "aws-amplify/api";
import { CognitoUser, DashboardMetrics } from "@/types/interfaces";
import {
  CognitoIdentityProviderClient,
  ListUsersCommand,
} from "@aws-sdk/client-cognito-identity-provider";
import { fetchAuthSession } from "aws-amplify/auth";
import amplifyConfig from "@/../amplify_outputs.json" assert { type: "json" };

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
    aws_region: string;
  };
  version: string;
}

const config = amplifyConfig as AmplifyConfig;

export const client = generateClient<Schema>();

export const fetchLivenessSessions = async (): Promise<LivenessSession[]> => {
  const response = await client.models.LivenessSession.list({
    limit: 5000,
  });
  const sortedData = response.data.sort((a, b) => {
    return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
  });
  return sortedData;
};

export const fetchLivenessSession = async (
  sessionId: string
): Promise<LivenessSession | null> => {
  const response = await client.models.LivenessSession.get({
    sessionId: sessionId,
  });
  return response.data;
};

export const fetchDocumentValidations = async (): Promise<
  DocumentValidation[]
> => {
  const response = await client.models.DocumentValidation.list({
    limit: 5000,
  });
  const sortedData = response.data.sort((a, b) => {
    return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
  });
  return sortedData;
};
export const fetchDocumentValidation = async (
  validationId: string
): Promise<DocumentValidation | null> => {
  const response = await client.models.DocumentValidation.get({
    validationId: validationId,
  });

  return response.data;
};
export const fetchDocumentVerifications = async (): Promise<
  DocumentVerification[]
> => {
  const response = await client.models.DocumentVerification.list({
    limit: 5000,
  });
  const sortedData = response.data.sort((a, b) => {
    return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
  });
  return sortedData;
};
export const fetchDocumentVerification = async (
  verificationId: string
): Promise<DocumentVerification | null> => {
  const response = await client.models.DocumentVerification.get({
    verificationId: verificationId,
  });

  return response.data;
};
export const fetchAPICalls = async (): Promise<APICall[]> => {
  const response = await client.models.APICall.list({
    limit: 5000,
  });
  const sortedData = response.data.sort((a, b) => {
    return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
  });
  return sortedData;
};
export const fetchAPICall = async (
  apiCallId: string
): Promise<APICall | null> => {
  const response = await client.models.APICall.get({
    apiCallId: apiCallId,
  });
  return response.data;
};
export const fetchMetrics = async (): Promise<DashboardMetrics> => {
  const [
    documentValidations,
    documentVerifications,
    backGroundChecks,
    agentRegistrations,
    customerRegistrations,
    apiCalls,
    faceLivenessCount,
  ] = await Promise.all([
    fetchDocumentValidations(),
    fetchDocumentVerifications(),
    fetchBackGroundChecks(),
    fetchAgents(),
    fetchCustomers(),
    fetchAPICalls(),
    fetchLivenessSessions(),
  ]);

  const apiCallsCachehits = apiCalls.filter((apiCall) => apiCall.cacheHit);
  return {
    documentValidations: documentValidations.length,
    documentVerifications: documentVerifications.length,
    backGroundChecks:backGroundChecks.length,
    agentRegistrations:agentRegistrations.length,
    customerRegistrations:customerRegistrations.length,
    apiCalls: apiCalls.length,
    apiCallsCachehits: apiCallsCachehits.length,
    faceLivenessCount: faceLivenessCount.length,
  };
};

const listUsers = async (
  limit = 20,
  paginationToken?: string
): Promise<{
  users: CognitoUser[];
  nextToken?: string;
}> => {
  try {
    // Get values from Amplify configuration
    const userPoolId = config.auth.user_pool_id;
    const region = config.auth.aws_region;

    if (!userPoolId) {
      throw new Error("UserPoolId not found in Amplify configuration");
    }

    if (!region) {
      throw new Error("Region not found in Amplify configuration");
    }

    const { credentials } = await fetchAuthSession();

    const client = new CognitoIdentityProviderClient({
      credentials,
      region,
    });

    const command = new ListUsersCommand({
      UserPoolId: userPoolId,
      Limit: limit,
      PaginationToken: paginationToken,
    });

    const response = await client.send(command);

    const formattedUsers: CognitoUser[] =
      response.Users?.map((user) => ({
        username: user.Username || "",
        email: user.Attributes?.find((attr) => attr.Name === "email")?.Value,
        enabled: user.Enabled || false,
        userStatus: user.UserStatus || "",
        userCreateDate: user.UserCreateDate
          ? new Date(user.UserCreateDate).toLocaleString()
          : "",
      })) || [];

    return {
      users: formattedUsers,
      nextToken: response.PaginationToken,
    };
  } catch (error) {
    console.error("Error fetching users:", error);
    throw error;
  }
};
export const fetchUsers = async (): Promise<CognitoUser[]> => {
  try {
    const { users } = await listUsers(30);
    return users;
  } catch (error) {
    // Handle error
    console.log(error);
    return [];
  }
};

export const fetchBackGroundChecks = async (): Promise<BackGroundCheck[]> => {
  const response = await client.models.BackGroundCheck.list({
    limit: 5000,
  });
  const sortedData = response.data.sort((a, b) => {
    return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
  });
  return sortedData;
};
export const fetchBackGroundCheck = async (
  backGroundCheckId: string
): Promise<BackGroundCheck | null> => {
  const response = await client.models.BackGroundCheck.get({
    backGroundCheckId: backGroundCheckId,
  });

  return response.data;
};

export const fetchAgents = async (): Promise<Agent[]> => {
  const response = await client.models.Agent.list({
    limit: 5000,
  });
  const sortedData = response.data.sort((a, b) => {
    return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
  });
  return sortedData;
};

export const fetchAgent = async (agentId: string): Promise<Agent | null> => {
  const response = await client.models.Agent.get({
    agentId: agentId,
  });
  return response.data;
};

export const fetchCustomers = async (): Promise<Customer[]> => {
  const response = await client.models.Customer.list({
    limit: 5000,
  });
  const sortedData = response.data.sort((a, b) => {
    return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
  });
  return sortedData;
};

export const fetchCustomer = async (
  customerId: string
): Promise<Customer | null> => {
  const response = await client.models.Customer.get({
    customerId: customerId,
  });
  return response.data;
};
