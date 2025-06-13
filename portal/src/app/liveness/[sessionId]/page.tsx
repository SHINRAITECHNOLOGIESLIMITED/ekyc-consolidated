"use client";

import { Details, DetailsProps } from "@/components/Details";
import { fetchLivenessSession } from "@/services/DataService";
import { LivenessSession } from "@/types/models";
import { Alert } from "@cloudscape-design/components";
import { useParams } from "next/navigation";
import React from "react";
import LivenessSessionDetails from "../LivenessDetails";


const LivenessSessionDetailsPage: React.FC = () => {
  const params = useParams();
  const backGroundCheckId = Array.isArray(params.backGroundCheckId)
    ? params.backGroundCheckId[0]
    : params.backGroundCheckId;

  if (!backGroundCheckId) {
    return (
      <Alert type="error" header="Error" dismissible={false}>
        DocumentId not specified
      </Alert>
    );
  }
  const detailsParams: DetailsProps<LivenessSession> = {
    title: "LivenessSession",
    primaryKey: backGroundCheckId,
    fetcher: (backGroundCheckId: string) => fetchLivenessSession(backGroundCheckId),
    itemDetails: LivenessSessionDetails,
  };

  return <Details {...detailsParams} />;
};

export default LivenessSessionDetailsPage;
