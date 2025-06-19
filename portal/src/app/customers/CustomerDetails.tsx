"use client";

import { Customer } from "@/types/models";
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

const CustomerDetails = (customer: Customer) => {
  const hasDocuments = customer.kycCertificateS3Path;
  return (
    <SpaceBetween size="l">
      <Header variant="h1">Customer Registration</Header>
      <Header variant="h3">ID: {customer.customerId}</Header>

      <ColumnLayout columns={3} variant="text-grid">
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Name</Box>
          <Box fontWeight="bold">{customer.name}</Box>
        </SpaceBetween>

        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Gender</Box>
          <Box>{customer.gender}</Box>
        </SpaceBetween>

        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Date of Birth</Box>
          <Box>{customer.dateOfBirth}</Box>
        </SpaceBetween>
      </ColumnLayout>

      <Tabs
        tabs={[
          {
            id: "details",
            label: "Customer Details",
            content: (
              <SpaceBetween size="l">
                {/* Identification Details */}
                <Container
                  header={<Header variant="h2">Identification Details</Header>}
                >
                  <ColumnLayout columns={3} variant="text-grid">
                    <SpaceBetween size="xs">
                      <Box variant="awsui-key-label">PIN Number</Box>
                      <Box>{customer.pinNumber}</Box>
                    </SpaceBetween>

                    <SpaceBetween size="xs">
                      <Box variant="awsui-key-label">ID Number</Box>
                      <Box>{customer.idNumber}</Box>
                    </SpaceBetween>

                    <SpaceBetween size="xs">
                      <Box variant="awsui-key-label">Passport Number</Box>
                      <Box>{customer.passportNumber || "-"}</Box>
                    </SpaceBetween>
                  </ColumnLayout>
                </Container>

                {/* Documents */}
                <Container header={<Header variant="h2">Documents</Header>}>
                  <ColumnLayout columns={2} variant="text-grid">
                    <SpaceBetween size="xs">
                      <Box variant="awsui-key-label">Passport Photo</Box>
                      <Box>
                        {customer.passportPhotoUrl ? (
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
                        {customer.nationalIdCardUrl ? (
                          <div>Available</div>
                        ) : (
                          <StatusIndicator type="stopped">
                            Not available
                          </StatusIndicator>
                        )}
                      </Box>
                    </SpaceBetween>

                    <SpaceBetween size="xs">
                      <Box variant="awsui-key-label">Passport Document</Box>
                      <Box>
                        {customer.passportUrl ? (
                          <div>Available</div>
                        ) : (
                          <StatusIndicator type="stopped">
                            Not available
                          </StatusIndicator>
                        )}
                      </Box>
                    </SpaceBetween>

                    <SpaceBetween size="xs">
                      <Box variant="awsui-key-label">KRA PIN Card</Box>
                      <Box>
                        {customer.kraPinCardUrl ? (
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
                          customer.kycStatus === "VERIFIED"
                            ? "success"
                            : "pending"
                        }
                      >
                        {customer.kycStatus}
                      </StatusIndicator>
                    </SpaceBetween>

                    <SpaceBetween size="xs">
                      <Box variant="awsui-key-label">KYC Certificate</Box>
                      <Box>
                        {customer.kycCertificateS3Path ? (
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
                {customer.kycCertificateS3Path && (
                  <Container
                    header={<Header variant="h2">KYC Certificate</Header>}
                  >
                    <DocumentViewer
                      objectKey={customer.kycCertificateS3Path}
                      bucketType={"certification"}
                    />
                  </Container>
                )}

                {!hasDocuments && (
                  <Box textAlign="center" padding="l">
                    KYC Certificate not available this customer.
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

export default CustomerDetails;
