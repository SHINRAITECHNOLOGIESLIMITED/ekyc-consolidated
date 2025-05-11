import {defineStorage} from '@aws-amplify/backend';

export const storage = defineStorage({
    name: 'kyc_documents',
    access: (allow) => ({
        // Allow authenticated users full access to their own folder structure
        'uploaded_kyc_docs/${cognito:sub}/*': [
            allow.authenticated.to([
                'read',
                'write',
            ])
        ],
        // Allow listing of the user's root folder
        'uploaded_kyc_docs/*': [
            allow.authenticated.to([
                'read'
            ])
        ]
    }),
    isDefault: true
});