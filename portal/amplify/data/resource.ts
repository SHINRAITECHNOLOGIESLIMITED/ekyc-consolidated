import { a, type ClientSchema, defineData } from "@aws-amplify/backend";

const schema = a.schema({
  LivenessSession: a
    .model({
      sessionId: a.string().required(),
      userId: a.string().required(),
      confidence: a.float(),
      status: a.string(),
    })
    .authorization((authorize) => [
      authorize.authenticated().to(["read"]),
      authorize.publicApiKey().to(["create", "read", "update", "delete"]),
    ])
    .identifier(["sessionId"]),
  DocumentValidation: a
    .model({
      validationId: a.id().required(),
      documentType: a.string().required(),
      s3Path: a.string().required(),
      overall_confidence: a.float().required(),
      validation_accuracy: a.float().required(),
      processing_accuracy: a.float().required(),
      documentIdentifier: a.string(),
      matchResults: a.json(),
      keywords_checks: a.json(),
    })
    .authorization((authorize) => [
      authorize.authenticated().to(["read"]),
      authorize.publicApiKey().to(["create", "read", "update", "delete"]),
    ])
    .identifier(["validationId"]),
  DocumentVerification: a
    .model({
      verificationId: a.id().required(),
      documentType: a.string().required(),
      validation_accuracy: a.float().required(),
      processing_accuracy: a.float().required(),
      documentIdentifier: a.string().required(),
      matchResults: a.json(),
    })
    .authorization((authorize) => [
      authorize.authenticated().to(["read"]),
      authorize.publicApiKey().to(["create", "read", "update", "delete"]),
    ])
    .identifier(["verificationId"]),
  BackGroundCheck: a
    .model({
      backGroundCheckId: a.id().required(),
      firstName: a.string().required(),
      middleName: a.string(),
      lastName: a.string().required(),
      gender: a.string().required(),
      dob: a.string().required(),
      nationalIdentificationNumber: a.string().required(),
      countryCode: a.string().required(),
      entityType: a.string().required(),
      sourceName: a.string().required(),
      results: a.json(),
    })
    .authorization((authorize) => [
      authorize.authenticated().to(["read"]),
      authorize.publicApiKey().to(["create", "read", "update", "delete"]),
    ])
    .identifier(["backGroundCheckId"]),
  Agent: a
    .model({
      agentId: a.id().required(),
      agentType: a.string().required(),
      name: a.string().required(),
      pinNumber: a.string().required(),
      idNumber: a.string(),
      passportPhotoUrl: a.string().required(),
      nationalIdCardUrl: a.string(),
      companyCertificateUrl: a.string(),
      dateOfBirth: a.string(),
      businessNumber: a.string(),
      kycStatus: a.string().required(),
    })
    .authorization((authorize) => [
      authorize.authenticated().to(["read"]),
      authorize.publicApiKey().to(["create", "read", "update", "delete"]),
    ])
    .identifier(["agentId"]),
  Customer: a
    .model({
      customerId: a.id().required(),
      name: a.string().required(),
      pinNumber: a.string().required(),
      idNumber: a.string().required(),
      gender: a.string().required(),
      dateOfBirth: a.string().required(),
      passportPhotoUrl: a.string().required(),
      nationalIdOrPassportUrl: a.string().required(),
      kraPinCardUrl: a.string().required(),
      kycStatus: a.string().required()
    })
    .authorization((authorize) => [
      authorize.authenticated().to(["read"]),
      authorize.publicApiKey().to(["create", "read", "update", "delete"]),
    ])
    .identifier(["customerId"]),

  APICall: a
    .model({
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
      responseData: a.json(),
    })
    .authorization((authorize) => [
      authorize.authenticated().to(["read"]),
      authorize.publicApiKey().to(["create", "read", "update", "delete"]),
    ])
    .identifier(["apiCallId"]),
});

export const data = defineData({
  schema,
  authorizationModes: {
    defaultAuthorizationMode: "userPool",
    apiKeyAuthorizationMode: {
      expiresInDays: 365,
    },
  },
});

export default schema;

export type Schema = ClientSchema<typeof schema>;
