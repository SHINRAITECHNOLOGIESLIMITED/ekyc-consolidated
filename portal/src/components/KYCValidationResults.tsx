import React from "react";
import {
  Table,
  Box,
  StatusIndicator,
  Header,
  Container,
} from "@cloudscape-design/components";
import { formatPercentage } from "@/utils/formatters";

export interface ValidationDetail {
  editdistance: number;
  actual: string;
  expected: string;
  confidence: number;
}

export interface ValidationResult {
  details?: ValidationDetail;
  status: string;
}

export interface ValidationResults {
  [key: string]: ValidationResult;
}

interface KYCValidationResultsProps {
  results: ValidationResults;
}

const KYCValidationResults: React.FC<KYCValidationResultsProps> = ({
  results,
}) => {
  const items = Object.entries(results || {}).map(([field, validation]) => {
    console.log(field, validation);
    const item = {
      field: field.replace(/([A-Z])/g, " $1").trim(),
      status: validation.status,
      actual: validation.details?.actual ?? "-",
      expected: validation.details?.expected ?? "-",
      difference: validation.details?.editdistance?.toString() ?? "-",
      confidence: validation.details?.confidence ?? 0
    };
    return item;
  });

  return (
    <Container>
      <Header variant="h2">Results</Header>
      <Table
        columnDefinitions={[
          {
            id: "field",
            header: "Field",
            cell: (item) => item.field,
          },
          {
            id: "status",
            header: "Status",
            cell: (item) => (
              <StatusIndicator
                type={
                  item.status.toLowerCase() === "not matched"
                    ? "warning"
                    : item.status.toLowerCase() === "not found"
                      ? "error"
                      : item.status.toLowerCase() === "not provided"
                        ? "info"
                        : "success"
                }
              >
                {item.status}
              </StatusIndicator>
            ),
          },
          {
            id: "actual",
            header: "Actual Value",
            cell: (item) =>  item.actual,
          },
          
          {
            id: "confidence",
            header: "Confidence",
            cell: (item) =>  formatPercentage(item.confidence),
          },
          {
            id: "expected",
            header: "Expected Value",
            cell: (item) => item.expected,
          },
          {
            id: "difference",
            header: "Edit Distance",
            cell: (item) => item.difference,
          },
        ]}
        items={items}
        variant="embedded"
        stripedRows
        empty={
          <Box textAlign="center" color="inherit">
            <b>No validation results available</b>
          </Box>
        }
      />
    </Container>
  );
};

export default KYCValidationResults;
