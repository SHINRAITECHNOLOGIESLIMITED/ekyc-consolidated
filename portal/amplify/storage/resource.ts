import {defineStorage} from '@aws-amplify/backend';

export const eKycDocumentStorage = defineStorage({
    name: 'kyc_documents',
    access: (allow) => ({
        '{entity_id}/*': [
            allow.authenticated.to(['read', 'write']),
            allow.entity('identity').to(['read', 'write'])
        ]
    }), isDefault: true
});