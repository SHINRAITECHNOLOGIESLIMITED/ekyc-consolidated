"use client";

import CertificateViewer from "@/components/CertificateViewer";
import { Agent } from "@/types/models";
import {
  Box,
  ColumnLayout,
  Container,
  Header,
  SpaceBetween,
  StatusIndicator,
  Tabs,
} from "@cloudscape-design/components";

const IndividualAgentDetails = (agent: Agent) => {
  const hasDocuments = agent.kycCertificateS3Path;

  return (
    <SpaceBetween size="l">
      <Header variant="h1">Individual Agent Registration</Header>
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

      <Tabs
        tabs={[
          {
            id: "details",
            label: "Agent Details",
            content: (
              <SpaceBetween size="l">
                {/* Identification Details */}
                <Container
                  header={<Header variant="h2">Identification Details</Header>}
                >
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
                          <div>Available</div>
                        ) : (
                          <StatusIndicator type="stopped">
                            Not available
                          </StatusIndicator>
                        )}
                      </Box>
                    </SpaceBetween>

                    <SpaceBetween size="xs">
                      <Box variant="awsui-key-label">National ID Card</Box>
                      <Box>
                        {agent.nationalIdCardUrl ? (
                          <div>Available</div>
                        ) : (
                          <StatusIndicator type="stopped">
                            Not available
                          </StatusIndicator>
                        )}
                      </Box>
                    </SpaceBetween>
                  </ColumnLayout>
                </Container>

                {/* KYC Information */}
                <Container
                  header={<Header variant="h2">KYC Information</Header>}
                >
                  <ColumnLayout columns={2} variant="text-grid">
                    <SpaceBetween size="xs">
                      <Box variant="awsui-key-label">KYC Status</Box>
                      <StatusIndicator
                        type={
                          agent.kycStatus === "VERIFIED" ? "success" : "pending"
                        }
                      >
                        {agent.kycStatus}
                      </StatusIndicator>
                    </SpaceBetween>

                    <SpaceBetween size="xs">
                      <Box variant="awsui-key-label">KYC Certificate</Box>
                      <Box>
                        {agent.kycCertificateS3Path ? (
                          <div>Available</div>
                        ) : (
                          <StatusIndicator type="stopped">
                            Not available
                          </StatusIndicator>
                        )}
                      </Box>
                    </SpaceBetween>
                  </ColumnLayout>
                </Container>
              </SpaceBetween>
            ),
          },
          {
            id: "documents",
            label: "KYC Certificate",
            content: (
              <SpaceBetween size="l">
                {agent.kycCertificateS3Path && (
                  <Container
                    header={<Header variant="h2">KYC Certificate</Header>}
                  >
                    <CertificateViewer
                      certificateKey={agent.kycCertificateS3Path}
                    />
                  </Container>
                )}
                {!hasDocuments && (
                  <Box textAlign="center" padding="l">
                    No documents available for this agent.
                  </Box>
                )}
              </SpaceBetween>
            ),
            disabled: !hasDocuments,
          },
        ]}
      />
    </SpaceBetween>
  );
};

export default IndividualAgentDetails;
