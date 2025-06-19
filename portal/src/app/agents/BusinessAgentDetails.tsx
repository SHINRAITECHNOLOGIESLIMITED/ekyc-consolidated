"use client";

import { Agent } from "@/types/models";
import DocumentViewer from "@/components/CertificateViewer";
import {
  Box,
  ColumnLayout,
  Container,
  Header,
  SpaceBetween,
  StatusIndicator,
  Tabs,
} from "@cloudscape-design/components";

const BusinessAgentDetails = (agent: Agent) => {
  const hasDocuments = agent.kycCertificateS3Path;

  return (
    <SpaceBetween size="l">
      <Header variant="h1">Business Agent Registration</Header>
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

      <Tabs
        tabs={[
          {
            id: "details",
            label: "Agent Details",
            content: (
              <SpaceBetween size="l">
                {/* Business Registration */}
                <Container
                  header={<Header variant="h2">Business Registration</Header>}
                >
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
                    <DocumentViewer
                      objectKey={agent.kycCertificateS3Path}
                      bucketType={"certification"}
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

export default BusinessAgentDetails;
