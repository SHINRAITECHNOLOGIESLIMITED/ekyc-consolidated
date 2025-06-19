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

const IndividualAgentDetails = (agent: Agent) => (
  <SpaceBetween size="l">
    <Header variant="h1">Individual Agent Details</Header>
    
    {/* Basic Information */}
    <Container header={<Header variant="h2">Basic Information</Header>}>
      <ColumnLayout columns={3} variant="text-grid">
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Name</Box>
          <Box>{agent.name}</Box>
        </SpaceBetween>
        
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Agent Type</Box>
          <Box>{agent.agentType}</Box>
        </SpaceBetween>
        
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Gender</Box>
          <Box>{agent.gender || "-"}</Box>
        </SpaceBetween>
      </ColumnLayout>
    </Container>

    {/* Identification Details */}
    <Container header={<Header variant="h2">Identification Details</Header>}>
      <ColumnLayout columns={3} variant="text-grid">
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
      </ColumnLayout>
    </Container>

    {/* Documents */}
    <Container header={<Header variant="h2">Documents</Header>}>
      <ColumnLayout columns={2} variant="text-grid">
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Passport Photo</Box>
          <Box>
            {agent.passportPhotoUrl ? (
              <Link external href={agent.passportPhotoUrl}>
                View Photo
              </Link>
            ) : (
              "-"
            )}
          </Box>
        </SpaceBetween>
        
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">National ID Card</Box>
          <Box>
            {agent.nationalIdCardUrl ? (
              <Link external href={agent.nationalIdCardUrl}>
                View ID Card
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

export default IndividualAgentDetails;