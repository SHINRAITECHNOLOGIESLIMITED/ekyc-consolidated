"use client";

import DocumentForm from "@/components/DocumentForm";
import Listing, { ListingProps } from "@/components/Listing";
import { fetchAgents } from "@/services/DataService";
import type { Agent } from "@/types/models";
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
  },
];

const listingProps: ListingProps<Agent> = {
  title: "Agents",
  getAll: fetchAgents,
  pageSize: 100,
  columnDefinitions,
  itemKey: (item: Agent) => item.agentId.toString(),
  itemDetailsLink: (item: Agent) => `agents/${item.agentId}`,
  renderItemDetails: (item: Agent) => AgentDetails(item),
  actions: [
    {
      id: "individual-agent-reg",
      label: "New Individual Agent",
      render: () => {
        return <IndividualAgentForm />;
      },
    },
    {
      id: "company-agent-reg",
      label: "New Business Agent",
      render: () => {
        return <BusinessAgentForm />;
      },
    },
  ],
};

const IndividualAgentForm: React.FC = () => (
  <DocumentForm
    title="Individual Agent Registration"
    documentType="nationalid"
    fields={[
      {
        id: "agentType",
        label: "Agent Type",
        type: "text",
        required: true,
        placeholder: "Individual",
      },
      {
        id: "name",
        label: "Full Name",
        type: "text",
        required: true,
        placeholder: "Jane Wairimu Maina",
      },
      {
        id: "pinNumber",
        label: "PIN Number",
        type: "text",
        required: true,
        placeholder: "A003388522V",
      },
      {
        id: "idNumber",
        label: "ID Number",
        type: "text",
        placeholder: "23667272",
      },
      {
        id: "dateOfBirth",
        label: "Date of Birth",
        type: "date",
        placeholder: "1985-01-01",
      },
      {
        id: "passportPhotoUrl",
        label: "Passport Photo",
        type: "document",
        acceptedFileTypes: [".jpg", ".jpeg", ".png"],
      },
      {
        id: "nationalIdCardUrl",
        label: "National ID Card",
        type: "document",
        acceptedFileTypes: [".jpg", ".jpeg", ".png", ".pdf"],
      },
    ]}
  />
);
const BusinessAgentForm: React.FC = () => (
  <DocumentForm
    title="Agent Registration"
    documentType="nationalid"
    fields={[
      {
        id: "agentType",
        label: "Agent Type",
        type: "text",
        required: true,
        placeholder: "Company",
      },
      {
        id: "name",
        label: "Business Name",
        type: "text",
        required: true,
        placeholder: "DETALI INSURANCE AGENCY LIMITED",
      },
      {
        id: "businessNumber",
        label: "Business Number",
        type: "text",
        placeholder: "PVT-RXUMYGVQ",
      },
      {
        id: "pinNumber",
        label: "PIN Number",
        type: "text",
        required: true,
        placeholder: "A003388522V",
      },
      {
        id: "companyCertificateUrl",
        label: "Certificate of Incorporation",
        type: "document",
        acceptedFileTypes: [".jpg", ".jpeg", ".png", ".pdf"],
      },
    ]}
  />
);
const AgentsListing: React.FC = () => {
  return <Listing {...listingProps} />;
};

export default AgentsListing;
