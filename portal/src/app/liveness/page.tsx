"use client";

import Listing, { ListingProps } from "@/components/Listing";
import LivenessDetection from "@/components/LivenessDetection";
import { fetchLivenessSessions } from "@/services/DataService";
import type { LivenessSession } from "@/types/models";
import { formatDateTime, formatPercentage } from "@/utils/formatters";
import LivenessSessionDetails from "./LivenessDetails";

const columnDefinitions = [
  {
    id: "sessionId",
    header: "Session ID",
    cell: (item: LivenessSession) => item.sessionId,
  },
  {
    id: "status",
    header: "Status",
    cell: (item: LivenessSession) => item.status?.toString() ?? "-",
  },
  {
    id: "confidence",
    header: "Confidence",
    cell: (item: LivenessSession) => formatPercentage(item.confidence ?? 0),
  },
  {
    id: "isLive",
    header: "Live",
    cell: (item: LivenessSession) => (item.is_live ? "Live" : "Not Live"),
  },
  {
    id: "updatedAt",
    header: "Time",
    cell: (item: LivenessSession) => formatDateTime(item.updatedAt),
  }
];

const listingProps: ListingProps<LivenessSession> = {
  title: "FaceLiveness Sessions",
  getAll: fetchLivenessSessions,
  pageSize: 100,
  columnDefinitions,
  itemKey: (item: LivenessSession) => item.sessionId.toString(),
  itemDetailsLink: (item: LivenessSession) => `liveness/${item.sessionId}`,
  renderItemDetails: (item: LivenessSession) => LivenessSessionDetails(item) ,
  actions: [
    {
      id: "new-liveness",
      label: "Capture New Liveness Check",
      render: () => {
        return <LivenessDetection />;
      },
    },
  ],
};

const FaceLivenessListing: React.FC = () => {
  return <Listing {...listingProps} />;
};

export default FaceLivenessListing;
