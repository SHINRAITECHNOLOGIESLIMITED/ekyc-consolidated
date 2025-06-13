import {defineBackend} from '@aws-amplify/backend';
import {auth} from './auth/resource';
import {data} from './data/resource';
import {storage} from './storage/resource';
import { Policy, PolicyStatement } from 'aws-cdk-lib/aws-iam';

const backend = defineBackend({
    auth,
    data,
    storage
});

// Define a new stack for the liveness detection policy
const livenessStack = backend.createStack("liveness-stack");
const livenessPolicy = new Policy(livenessStack, "LivenessPolicy", {
  statements: [
    new PolicyStatement({
      actions: ["rekognition:StartFaceLivenessSession"],
      resources: ["*"],
    }),
  ],
});
// backend.auth.resources.unauthenticatedUserIamRole.attachInlinePolicy(livenessPolicy); // allows guest user access
backend.auth.resources.authenticatedUserIamRole.attachInlinePolicy(livenessPolicy); // allows logged in user access