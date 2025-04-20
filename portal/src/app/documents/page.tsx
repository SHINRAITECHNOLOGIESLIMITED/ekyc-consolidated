"use client";

import Listing, {ListingProps} from '@/components/Listing';
import {fetchKYCDocuments} from '@/services/DataService';
import type {KYCDocument} from '@/types/models';

const columnDefinitions =
    [
        {
            id: "documentId",
            header: "Document ID",
            cell: (item: KYCDocument) => item.documentId
        },
        {
            id: "userId",
            header: "User Id",
            cell: (item: KYCDocument) => item.userId
        }
    ];


const listingProps: ListingProps<KYCDocument> = {
    title: "KYC Documents",
    getAll: fetchKYCDocuments,
    pageSize: 100,
    columnDefinitions,
    itemKey: (item: KYCDocument) => item.documentId.toString()
};

const DocumentsListing: React.FC = () => {
    return <Listing {...listingProps} />;
};

export default DocumentsListing;
