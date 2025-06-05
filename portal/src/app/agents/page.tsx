"use client";

import Listing, { ListingProps } from "@/components/Listing";
import NotImplemented from "@/components/NotImplemented";
import { fetchAgents } from "@/services/DataService";
import type { Agent } from "@/types/models";
import { SpaceBetween } from "@cloudscape-design/components";
import AgentDetails from "./AgentDetails";

const columnDefinitions = [
  {
    id: "agentId",
    header: "Agent ID",
    cell: (item: Agent) => item.agentId,
  },
  {
    id: "agentType",
    header: "Agent Type",
    cell: (item: Agent) => item.agentType,
  },
  {
    id: "name",
    header: "Name",
    cell: (item: Agent) => item.name,
  },
  {
    id: "pinNumber",
    header: "PIN Number",
    cell: (item: Agent) => item.pinNumber,
  },
  {
    id: "idNumber",
    header: "ID Number",
    cell: (item: Agent) => item.idNumber || "-",
  },
  {
    id: "dateOfBirth",
    header: "Date of Birth",
    cell: (item: Agent) => item.dateOfBirth || "-",
  },
  {
    id: "businessNumber",
    header: "Business Number",
    cell: (item: Agent) => item.businessNumber || "-",
  },
  {
    id: "kycStatus",
    header: "KYC Status",
    cell: (item: Agent) => item.kycStatus,
  }
];

const listingProps: ListingProps<Agent> = {
  title: "Agents",
  getAll: fetchAgents,
  pageSize: 100,
  columnDefinitions,
  itemKey: (item: Agent) => item.agentId.toString(),
  itemDetailsLink: (item: Agent) =>
    `agents/${item.agentId}`,
  renderItemDetails: (item: Agent) => AgentDetails(item),
  actions: [
    {
      id: "agent-reg",
      label: "New Agent Registration",
      render: () => (
        <SpaceBetween size={"s"}>
          <NotImplemented title={"Agent Registration"} />
        </SpaceBetween>
      ),
    },
  ],
};

const AgentsListing: React.FC = () => {
  return <Listing {...listingProps} />;
};

export default AgentsListing;
