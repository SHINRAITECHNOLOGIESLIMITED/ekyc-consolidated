"use client";

import React from "react";
import {
  Table,
  Box,
  StatusIndicator,
  Header,
  Container,
  SpaceBetween,
  Badge,
} from "@cloudscape-design/components";

export interface IPRSValidationResult {
  status: "MATCH" | "MISMATCH" | "INCONCLUSIVE";
  extracted_serial_number?: string;
  iprs_serial_number?: string;
  extracted_gender?: string;
  iprs_gender?: string;
  normalized_comparison: boolean;
  reason?: string | null;
}

export interface IPRSValidationResults {
  serialNumberValidation?: IPRSValidationResult;
  genderValidation?: IPRSValidationResult;
}

interface IPRSValidationResultsProps {
  serialNumberValidation?: IPRSValidationResult;
  genderValidation?: IPRSValidationResult;
}

interface IPRSValidationItem {
  field: string;
  status: string;
  extractedValue: string;
  iprsValue: string;
  normalized: boolean;
  reason?: string | null;
}

const getStatusIndicatorType = (status: string): "success" | "error" | "warning" | "info" => {
  switch (status?.toUpperCase()) {
    case "MATCH":
      return "success";
    case "MISMATCH":
      return "error";
    case "INCONCLUSIVE":
      return "warning";
    default:
      return "info";
  }
};

const getStatusLabel = (status: string): string => {
  switch (status?.toUpperCase()) {
    case "MATCH":
      return "Verified";
    case "MISMATCH":
      return "Mismatch";
    case "INCONCLUSIVE":
      return "Inconclusive";
    default:
      return status || "Unknown";
  }
};

const IPRSValidationResults: React.FC<IPRSValidationResultsProps> = ({
  serialNumberValidation,
  genderValidation,
}) => {
  const items: IPRSValidationItem[] = [];

  if (serialNumberValidation) {
    items.push({
      field: "Serial Number (IPRS)",
      status: serialNumberValidation.status,
      extractedValue: serialNumberValidation.extracted_serial_number || "-",
      iprsValue: serialNumberValidation.iprs_serial_number || "-",
      normalized: serialNumberValidation.normalized_comparison,
      reason: serialNumberValidation.reason,
    });
  }

  if (genderValidation) {
    items.push({
      field: "Gender (IPRS)",
      status: genderValidation.status,
      extractedValue: genderValidation.extracted_gender || "-",
      iprsValue: genderValidation.iprs_gender || "-",
      normalized: genderValidation.normalized_comparison,
      reason: genderValidation.reason,
    });
  }

  if (items.length === 0) {
    return null;
  }

  return (
    <Container>
      <Header
        variant="h2"
        description="Cross-validation of document data against IPRS government records"
      >
        IPRS Validation Results
      </Header>
      <SpaceBetween size="m">
        <Table
          columnDefinitions={[
            {
              id: "field",
              header: "Validation Type",
              cell: (item: IPRSValidationItem) => <strong>{item.field}</strong>,
              width: 180,
            },
            {
              id: "status",
              header: "Status",
              cell: (item: IPRSValidationItem) => (
                <StatusIndicator type={getStatusIndicatorType(item.status)}>
                  {getStatusLabel(item.status)}
                </StatusIndicator>
              ),
              width: 140,
            },
            {
              id: "extractedValue",
              header: "Document Value",
              cell: (item: IPRSValidationItem) => (
                <Box>
                  <code>{item.extractedValue}</code>
                </Box>
              ),
            },
            {
              id: "iprsValue",
              header: "IPRS Value",
              cell: (item: IPRSValidationItem) => (
                <Box>
                  <code>{item.iprsValue}</code>
                </Box>
              ),
            },
            {
              id: "normalized",
              header: "Normalized",
              cell: (item: IPRSValidationItem) => (
                <Badge color={item.normalized ? "green" : "grey"}>
                  {item.normalized ? "Yes" : "No"}
                </Badge>
              ),
              width: 100,
            },
            {
              id: "reason",
              header: "Notes",
              cell: (item: IPRSValidationItem) => item.reason || "-",
            },
          ]}
          items={items}
          variant="embedded"
          stripedRows
          empty={
            <Box textAlign="center" color="inherit">
              <b>No IPRS validation results available</b>
            </Box>
          }
        />
      </SpaceBetween>
    </Container>
  );
};

export default IPRSValidationResults;
