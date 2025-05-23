import React from "react";
import {
  Table,
  Box,
  StatusIndicator,
  Header,
  Container,
} from "@cloudscape-design/components";

export interface ValidationDetail {
  editdistance: number;
  actual: string;
  expected: string;
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
    const item = {
      field: field.replace(/([A-Z])/g, " $1").trim(),
      status: validation.status,
      actual: validation.details?.actual ?? "-",
      expected: validation.details?.expected ?? "-",
      difference: validation.details?.editdistance?.toString() ?? "-",
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
                    ? "error"
                    : item.status.toLowerCase() === "not found"
                      ? "warning"
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
            cell: (item) => item.actual,
          },
          {
            id: "expected",
            header: "Expected Value",
            cell: (item) => item.expected,
          },
          {
            id: "difference",
            header: "Difference",
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
