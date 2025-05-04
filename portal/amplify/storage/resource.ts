import {defineStorage} from '@aws-amplify/backend';

export const eKycDocumentStorage = defineStorage({
    name: 'kyc_documents',
    access: (allow) => ({
        'kycdocuments/{entity_id}/*': [
            allow.authenticated.to(['read']),
            allow.entity('identity').to(['read', 'write'])
        ]
    })

});
export const eKycCertificateStorage = defineStorage({
    name: 'kyc_certificates',
    access: (allow) => ({
        'kyccertificates/*': [
            allow.authenticated.to(['read'])
        ]
    })
});