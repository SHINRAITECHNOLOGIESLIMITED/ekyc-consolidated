"use client";

import Listing, {ListingProps} from '@/components/Listing';
import {fetchDocumentVerifications} from '@/services/DataService';
import type {DocumentVerification} from '@/types/models';
import {formatDateTime} from "@/utils/formatters";

const columnDefinitions =
    [
        {
            id: "VerificationId",
            header: "Verification ID",
            cell: (item: DocumentVerification) => item.verificationId
        },
        {
            id: "documentType",
            header: "Document Type",
            cell: (item: DocumentVerification) => item.documentType
        },
        {
            id: "documentIdentifier",
            header: "Identifier",
            cell: (item: DocumentVerification) => item.documentIdentifier ?? ""
        },
        {
            id: "updatedAt",
            header: "Updated At",
            cell: (item: DocumentVerification) => formatDateTime(item.updatedAt)
        }
    ];


const listingProps: ListingProps<DocumentVerification> = {
    title: "Validated Documents",
    getAll: fetchDocumentVerifications,
    pageSize: 100,
    columnDefinitions,
    itemKey: (item: DocumentVerification) => item.verificationId.toString(),
    itemDetailsLink: (item: DocumentVerification) => `doc-verifications/${item.verificationId}`
};

const DocumentsListing: React.FC = () => {
    return <Listing {...listingProps} />;
};

export default DocumentsListing;
