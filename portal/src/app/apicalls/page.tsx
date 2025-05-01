"use client";

import Listing, {ListingProps} from '@/components/Listing';
import {fetchAPICalls} from '@/services/DataService';
import type {APICall} from '@/types/models';
import {formatTimeStamp} from "@/utils/formatters";

const columnDefinitions =
    [
        {
            id: "apiCallId",
            header: "API Call ID",
            cell: (item: APICall) => item.apiCallId
        },
        {
            id: "userId",
            header: "User Id",
            cell: (item: APICall) => item.userId
        },
        {
            id: "apiName",
            header: "API",
            cell: (item: APICall) => item.apiName
        },
        {
            id: "apiMethod",
            header: "API Method",
            cell: (item: APICall) => item.apiMethod
        },
        {
            id: "requestIPAddress",
            header: "requestIPAddress",
            cell: (item: APICall) => item.requestIPAddress ?? ""
        },
        {
            id: "requestHttpMethod",
            header: "Http Method",
            cell: (item: APICall) => item.requestHttpMethod ?? ""
        },
        {
            id: "requestTimestamp",
            header: "Time",
            cell: (item: APICall) => item.requestTimestamp ? formatTimeStamp(item.requestTimestamp) : "-"
        },
        {
            id: "responseStatusCode",
            header: "Status Code",
            cell: (item: APICall) => item.responseStatusCode ?? ""
        },
        {
            id: "responseResult",
            header: "Response Result",
            cell: (item: APICall) => item.responseResult ?? ""
        }
    ];


const listingProps: ListingProps<APICall> = {
    title: "API Calls",
    getAll: fetchAPICalls,
    pageSize: 100,
    columnDefinitions,
    itemKey: (item: APICall) => item.apiCallId
};

const DocumentsListing: React.FC = () => {
    return <Listing {...listingProps} />;
};

export default DocumentsListing;
