"use client";

import Listing, {ListingProps} from '@/components/Listing';
import {fetchLivenessSessions} from '@/services/DataService';
import type {LivenessSession} from '@/types/models';
import LivenessDetection from "@/components/LivenessDetection";

const columnDefinitions =
    [
        {
            id: "sessionId",
            header: "Session ID",
            cell: (item: LivenessSession) => item.sessionId
        },
        {
            id: "userId",
            header: "User Id",
            cell: (item: LivenessSession) => item.userId
        },
        {
            id: "status",
            header: "Status",
            cell: (item: LivenessSession) => item.status?.toString() ?? "-"
        },
        {
            id: "confidence",
            header: "Confidence",
            cell: (item: LivenessSession) => item.confidence?.toString() ?? "-"
        }
    ];


const listingProps: ListingProps<LivenessSession> = {
    title: "FaceLiveness Sessions",
    getAll: fetchLivenessSessions,
    pageSize: 100,
    columnDefinitions,
    itemKey: (item: LivenessSession) => item.sessionId.toString(),
    actions: [
        {
            id: "new-liveness",
            label: "Capture New Liveness Check",
            render: () => {
                return <LivenessDetection />
            }
        }
    ],
};

const FaceLivenessListing: React.FC = () => {
    return <Listing {...listingProps} />;
};

export default FaceLivenessListing;
