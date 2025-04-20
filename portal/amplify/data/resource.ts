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
    ]).identifier(['documentId'])
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
