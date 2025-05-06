"use client";

import Listing, {ListingProps} from '@/components/Listing';
import {fetchKYCDocuments} from '@/services/DataService';
import type {KYCDocument} from '@/types/models';
import {formatDateTime} from "@/utils/formatters";

const columnDefinitions =
    [
        {
            id: "customerId",
            header: "Customer ID",
            cell: (item: KYCDocument) => item.customerId
        },
        {
            id: "documentType",
            header: "Document Type",
            cell: (item: KYCDocument) => item.documentType
        },
        {
            id: "documentStatus",
            header: "Status",
            cell: (item: KYCDocument) => item.documentType
        },
        {
            id: "updatedAt",
            header: "Updated At",
            cell: (item: KYCDocument) => formatDateTime(item.updatedAt)
        },
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
