import {a, type ClientSchema, defineData} from '@aws-amplify/backend';

const schema = a.schema({
    LivenessSession: a.model({
        sessionId: a.string().required(),
        userId: a.string().required(),
        confidence: a.float(),
        status: a.string()
    }).authorization(authorize => [
        authorize.authenticated().to(['read']),
        authorize.publicApiKey().to(['create', 'read', 'update', 'delete'])
    ]).identifier(['sessionId'])
    ,
    KYCDocument: a.model({
        documentId: a.string().required(),
        userId: a.string().required(),

    }).authorization(authorize => [
        authorize.authenticated().to(['read']),
        authorize.publicApiKey().to(['create', 'read', 'update', 'delete'])
    ]).identifier(['documentId']),
    APICall: a.model({
        apiCallId: a.id().required(),
        traceId: a.string().required(),
        durationMs: a.integer().required(),
        apiName: a.string().required(),
        apiMethod: a.string().required(),
        requestIPAddress: a.string(),
        requestHttpMethod: a.string(),
        requestTimestamp: a.integer(),
        responseStatusCode: a.string(),
        responseResult: a.string(),
        requestData: a.json(),
        responseData: a.json()
    }).authorization(authorize => [
        authorize.authenticated().to(['read']),
        authorize.publicApiKey().to(['create', 'read', 'update', 'delete'])
    ]).identifier(['apiCallId'])
});

export const data = defineData({
    schema,
    authorizationModes: {
        defaultAuthorizationMode: 'userPool',
        apiKeyAuthorizationMode: {
            expiresInDays: 365
        }
    }
});

export default schema;

export type Schema = ClientSchema<typeof schema>;
