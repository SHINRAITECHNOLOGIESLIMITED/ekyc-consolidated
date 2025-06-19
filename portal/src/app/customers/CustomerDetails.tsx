"use client";

import { Customer } from "@/types/models";
import {
  Box,
  ColumnLayout,
  Container,
  Header,
  Link,
  SpaceBetween,
  StatusIndicator,
} from "@cloudscape-design/components";

const CustomerDetails = (customer: Customer) => (
  <SpaceBetween size="l">
    <Header variant="h1">Customer Details</Header>
    <Header variant="h3">ID: {customer.customerId}</Header>
    
    {/* Personal Information */}
    <Container header={<Header variant="h2">Personal Information</Header>}>
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
    </Container>

    {/* Identification Details */}
    <Container header={<Header variant="h2">Identification Details</Header>}>
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
              <Link external href={customer.passportPhotoUrl}>
                View Photo
              </Link>
            ) : (
              <StatusIndicator type="stopped">Not available</StatusIndicator>
            )}
          </Box>
        </SpaceBetween>

        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">National ID Card</Box>
          <Box>
            {customer.nationalIdCardUrl ? (
              <Link external href={customer.nationalIdCardUrl}>
                View ID Card
              </Link>
            ) : (
              <StatusIndicator type="stopped">Not available</StatusIndicator>
            )}
          </Box>
        </SpaceBetween>
        
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Passport Document</Box>
          <Box>
            {customer.passportUrl ? (
              <Link external href={customer.passportUrl}>
                View Passport
              </Link>
            ) : (
              <StatusIndicator type="stopped">Not available</StatusIndicator>
            )}
          </Box>
        </SpaceBetween>
        
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">KRA PIN Card</Box>
          <Box>
            {customer.kraPinCardUrl ? (
              <Link external href={customer.kraPinCardUrl}>
                View PIN Card
              </Link>
            ) : (
              <StatusIndicator type="stopped">Not available</StatusIndicator>
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
          <StatusIndicator type={customer.kycStatus === "VERIFIED" ? "success" : "pending"}>
            {customer.kycStatus}
          </StatusIndicator>
        </SpaceBetween>
        
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">KYC Certificate</Box>
          <Box>
            {customer.kycCertificateS3Path ? (
              <Link external href={customer.kycCertificateS3Path}>
                View Certificate
              </Link>
            ) : (
              <StatusIndicator type="stopped">Not available</StatusIndicator>
            )}
          </Box>
        </SpaceBetween>
      </ColumnLayout>
    </Container>
  </SpaceBetween>
);

export default CustomerDetails;