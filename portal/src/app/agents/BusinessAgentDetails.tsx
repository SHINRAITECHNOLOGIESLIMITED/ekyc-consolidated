"use client";

import { Agent } from "@/types/models";
import {
  Box,
  ColumnLayout,
  Container,
  Header,
  Link,
  SpaceBetween,
} from "@cloudscape-design/components";

const BusinessAgentDetails = (agent: Agent) => (
  <SpaceBetween size="l">
    <Header variant="h1">Business Agent Details</Header>
    
    {/* Basic Information */}
    <Container header={<Header variant="h2">Basic Information</Header>}>
      <ColumnLayout columns={2} variant="text-grid">
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Company Name</Box>
          <Box>{agent.name}</Box>
        </SpaceBetween>
        
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Agent Type</Box>
          <Box>{agent.agentType}</Box>
        </SpaceBetween>
      </ColumnLayout>
    </Container>

    {/* Business Registration */}
    <Container header={<Header variant="h2">Business Registration</Header>}>
      <ColumnLayout columns={2} variant="text-grid">
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">PIN Number</Box>
          <Box>{agent.pinNumber}</Box>
        </SpaceBetween>
        
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Business Number</Box>
          <Box>{agent.businessNumber || "-"}</Box>
        </SpaceBetween>
      </ColumnLayout>
    </Container>

    {/* Documents */}
    <Container header={<Header variant="h2">Documents</Header>}>
      <ColumnLayout columns={1} variant="text-grid">
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Company Certificate</Box>
          <Box>
            {agent.companyCertificateUrl ? (
              <Link external href={agent.companyCertificateUrl}>
                View Certificate
              </Link>
            ) : (
              "-"
            )}
          </Box>
        </SpaceBetween>
      </ColumnLayout>
    </Container>

    {/* KYC Information */}
    <Container header={<Header variant="h2">KYC Information</Header>}>
      <ColumnLayout columns={2} variant="text-grid">
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">KYC Status</Box>
          <Box>{agent.kycStatus}</Box>
        </SpaceBetween>
        
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">KYC Certificate</Box>
          <Box>
            {agent.kycCertificateS3Path ? (
              <Link external href={agent.kycCertificateS3Path}>
                View Certificate
              </Link>
            ) : (
              "-"
            )}
          </Box>
        </SpaceBetween>
      </ColumnLayout>
    </Container>
  </SpaceBetween>
);

export default BusinessAgentDetails;