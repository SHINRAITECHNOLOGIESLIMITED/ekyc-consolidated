"use client";

import { Agent } from "@/types/models";
import {
  Box,
  ColumnLayout,
  Header,
  SpaceBetween,
} from "@cloudscape-design/components";

const AgentDetails = (agent: Agent) => (
  <SpaceBetween size="l">
    <Header variant="h1">Agent Details</Header>
    <ColumnLayout columns={4} variant="text-grid">
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">Agent Type</Box>
        <Box>{agent.agentType}</Box>
      </SpaceBetween>
      
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">Name</Box>
        <Box>{agent.name}</Box>
      </SpaceBetween>
      
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">PIN Number</Box>
        <Box>{agent.pinNumber}</Box>
      </SpaceBetween>
      
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">ID Number</Box>
        <Box>{agent.idNumber || "-"}</Box>
      </SpaceBetween>
      
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">Date of Birth</Box>
        <Box>{agent.dateOfBirth || "-"}</Box>
      </SpaceBetween>
      
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">Business Number</Box>
        <Box>{agent.businessNumber || "-"}</Box>
      </SpaceBetween>
      
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">Passport Photo</Box>
        <Box>{agent.passportPhotoUrl ? "Available" : "-"}</Box>
      </SpaceBetween>
      
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">National ID Card</Box>
        <Box>{agent.nationalIdCardUrl ? "Available" : "-"}</Box>
      </SpaceBetween>
      
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">Company Certificate</Box>
        <Box>{agent.companyCertificateUrl ? "Available" : "-"}</Box>
      </SpaceBetween>
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">KYC Status</Box>
        <Box>{agent.kycStatus}</Box>
      </SpaceBetween>
    </ColumnLayout>
  </SpaceBetween>
);

export default AgentDetails;