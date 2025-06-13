import {defineAuth} from '@aws-amplify/backend';
export const auth = defineAuth({
    loginWith: {
        email: {
            verificationEmailStyle: "CODE",
            verificationEmailSubject: "Welcome to Shinrai Jubilee eKYC portal!",
            verificationEmailBody: (code) => `Hi there,
To verify your account please enter the following verification code:
${code()}
If you didn't request this verification code, please ignore this email.
Thanks,
Shinrai Team`,
        },
    },

    userAttributes: {}
});


