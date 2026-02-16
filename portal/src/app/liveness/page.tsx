"use client";

import { useState } from "react";
import Listing, { ListingProps } from "@/components/Listing";
import LivenessDetection from "@/components/LivenessDetection";
import FaceMatching from "@/components/FaceMatching";
import { fetchLivenessSessions } from "@/services/DataService";
import type { LivenessSession } from "@/types/models";
import { formatDateTime, formatPercentage } from "@/utils/formatters";
import LivenessSessionDetails from "./LivenessDetails";
import {
  Button,
  Container,
  FormField,
  Input,
  SpaceBetween,
  StatusIndicator,
} from "@cloudscape-design/components";

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
  renderItemDetails: (item: LivenessSession) => <LivenessSessionDetails {...item} />,
  actions: [
    {
      id: "new-liveness",
      label: "Capture New Liveness Check",
      render: () => {
        return <LivenessDetection />;
      },
    },
    {
      id: "face-match",
      label: "Run Face Match",
      render: () => {
        return <FaceMatchPrompt />;
      },
    },
  ],
};

const FaceLivenessListing: React.FC = () => {
  return <Listing {...listingProps} />;
};

const FaceMatchPrompt: React.FC = () => {
  const [sessionId, setSessionId] = useState("");
  const [started, setStarted] = useState(false);

  if (started && sessionId.trim()) {
    return <FaceMatching sessionId={sessionId.trim()} />;
  }

  return (
    <Container>
      <SpaceBetween size="m">
        <FormField label="Liveness Session ID" description="Enter the session ID from a completed liveness check">
          <Input
            value={sessionId}
            onChange={({ detail }) => setSessionId(detail.value)}
            placeholder="e.g. abc123-def456-..."
          />
        </FormField>
        <Button variant="primary" onClick={() => setStarted(true)} disabled={!sessionId.trim()}>
          Start Face Match
        </Button>
      </SpaceBetween>
    </Container>
  );
};

export default FaceLivenessListing;
