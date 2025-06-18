"use client";

import Listing, { ListingProps } from "@/components/Listing";
import LivenessDetection from "@/components/LivenessDetection";
import { fetchLivenessSessions } from "@/services/DataService";
import type { LivenessSession } from "@/types/models";
import { formatDateTime, formatPercentage } from "@/utils/formatters";
import LivenessSessionDetails from "./LivenessDetails";
import { StatusIndicator } from "@cloudscape-design/components";

const columnDefinitions = [
  {
    id: "sessionId",
    header: "Session ID",
    cell: (item: LivenessSession) => item.sessionId,
  },
  {
    id: "confidence",
    header: "Confidence",
    cell: (item: LivenessSession) => formatPercentage(item.confidence ?? 0),
  },
  {
    id: "threshhold",
    header: "Threshold",
    cell: (item: LivenessSession) => formatPercentage(item.threshold ?? 85.0),
  },
  {
    id: "updatedAt",
    header: "Time",
    cell: (item: LivenessSession) => formatDateTime(item.updatedAt),
  },
  {
    id: "isLive",
    header: "Status",
    cell: (item: LivenessSession) => (<StatusIndicator type={item.is_live ? "success" : "error"}>
                    {item.is_live ? "Live" : "Not Live"}
                  </StatusIndicator>),
  },

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
