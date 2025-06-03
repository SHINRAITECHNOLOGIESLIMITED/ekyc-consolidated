"use client";

import { Customer } from "@/types/models";
import {
  Box,
  ColumnLayout,
  Header,
  SpaceBetween,
} from "@cloudscape-design/components";

const CustomerDetails = (customer: Customer) => (
  <SpaceBetween size="l">
    <Header variant="h1">Customer Details</Header>
    <ColumnLayout columns={2} variant="text-grid">
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">Name</Box>
        <Box>{customer.name}</Box>
      </SpaceBetween>

      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">PIN Number</Box>
        <Box>{customer.pinNumber}</Box>
      </SpaceBetween>

      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">ID Number</Box>
        <Box>{customer.idNumber}</Box>
      </SpaceBetween>

      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">Gender</Box>
        <Box>{customer.gender}</Box>
      </SpaceBetween>

      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">Date of Birth</Box>
        <Box>{customer.dateOfBirth}</Box>
      </SpaceBetween>

      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">Passport Photo</Box>
        <Box>{customer.passportPhotoUrl ? "Available" : "-"}</Box>
      </SpaceBetween>

      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">National ID/Passport</Box>
        <Box>{customer.nationalIdOrPassportUrl ? "Available" : "-"}</Box>
      </SpaceBetween>

      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">KRA PIN Card</Box>
        <Box>{customer.kraPinCardUrl ? "Available" : "-"}</Box>
      </SpaceBetween>
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">KYC Status</Box>
        <Box>{customer.kycStatus}</Box>
      </SpaceBetween>
    </ColumnLayout>
  </SpaceBetween>
);

export default CustomerDetails;
