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
    DocumentValidation: a.model({
        validationId: a.id().required(),
        documentType: a.string().required(),
        s3Path: a.string().required(),
        documentIdentifier: a.string(),
        matchResults: a.json(),
        keywords_checks: a.json()
    }).authorization(authorize => [
        authorize.authenticated().to(['read']),
        authorize.publicApiKey().to(['create', 'read', 'update', 'delete'])
    ]).identifier(['validationId']),
    DocumentVerification: a.model({
        verificationId: a.id().required(),
        documentType: a.string().required(),
        documentIdentifier: a.string(),
        matchResults: a.json()
    }).authorization(authorize => [
        authorize.authenticated().to(['read']),
        authorize.publicApiKey().to(['create', 'read', 'update', 'delete'])
    ]).identifier(['verificationId']),
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
