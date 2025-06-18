"use client";

import { Customer } from "@/types/models";
import {
  Box,
  ColumnLayout,
  Header,
  Link,
  SpaceBetween,
  StatusIndicator,
  Container,
} from "@cloudscape-design/components";

const CustomerDetails = (customer: Customer) => {
  const renderDocumentLink = (url: string | null | undefined, label: string = "View") => {
    if (!url) return <StatusIndicator type="stopped">Not available</StatusIndicator>;
    return <Link href={url} external>{label}</Link>;
  };

  return (
    <SpaceBetween size="l">
      <Header variant="h1">Customer Registration Details</Header>
      <Header variant="h3">{customer.customerId}</Header>
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

      <Container header={<Header variant="h2">Identification</Header>}>
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
            <Box>{customer.passportNumber ?? "-"}</Box>
          </SpaceBetween>
        </ColumnLayout>
      </Container>

      <Container header={<Header variant="h2">Documents</Header>}>
        <ColumnLayout columns={3} variant="text-grid">
          <SpaceBetween size="xs">
            <Box variant="awsui-key-label">Passport Photo</Box>
            {renderDocumentLink(customer.passportPhotoUrl)}
          </SpaceBetween>

          <SpaceBetween size="xs">
            <Box variant="awsui-key-label">National ID</Box>
            {renderDocumentLink(customer.nationalIdCardUrl)}
          </SpaceBetween>
          
          <SpaceBetween size="xs">
            <Box variant="awsui-key-label">Passport</Box>
            {renderDocumentLink(customer.passportUrl)}
          </SpaceBetween>
          
          <SpaceBetween size="xs">
            <Box variant="awsui-key-label">KRA PIN Card</Box>
            {renderDocumentLink(customer.kraPinCardUrl)}
          </SpaceBetween>
        </ColumnLayout>
      </Container>

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
            {renderDocumentLink(customer.kycCertificateS3Path, "Download Certificate")}
          </SpaceBetween>
        </ColumnLayout>
      </Container>
    </SpaceBetween>
  );
};

export default CustomerDetails;