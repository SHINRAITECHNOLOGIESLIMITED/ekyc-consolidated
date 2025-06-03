"use client";

import { Details, DetailsProps } from "@/components/Details";
import { fetchAgent } from "@/services/DataService";
import { Agent } from "@/types/models";
import { Alert } from "@cloudscape-design/components";
import { useParams } from "next/navigation";
import React from "react";
import AgentDetails from "../AgentDetails";

const AgentDetailsPage: React.FC = () => {
  const params = useParams();
  const agentId = Array.isArray(params.agentId)
    ? params.agentId[0]
    : params.agentId;

  if (!agentId) {
    return (
      <Alert type="error" header="Error" dismissible={false}>
        DocumentId not specified
      </Alert>
    );
  }
  const detailsParams: DetailsProps<Agent> = {
    title: "Agent",
    primaryKey: agentId,
    fetcher: (agentId: string) => fetchAgent(agentId),
    itemDetails: AgentDetails,
  };

  return <Details {...detailsParams} />;
};

export default AgentDetailsPage;
