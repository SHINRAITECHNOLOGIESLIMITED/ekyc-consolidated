import {defineStorage} from '@aws-amplify/backend';

export const storage = defineStorage({
    name: 'kyc_documents',
    access: (allow) => ({
        // Allow authenticated users full access to their own folder structure
        '${cognito:username}/*': [
            allow.authenticated.to([
                'read',
                'write',
            ])
        ],
        // Allow listing of the user's root folder
        '*': [
            allow.authenticated.to([
                'read'
            ])
        ]
    }),
    isDefault: true
});