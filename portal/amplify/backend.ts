import {defineBackend} from '@aws-amplify/backend';
import {auth} from './auth/resource';
import {data} from './data/resource';
import {eKycCertificateStorage, eKycDocumentStorage} from './storage/resource';

defineBackend({
    auth,
    data,
    eKycDocumentStorage,
    eKycCertificateStorage
});
