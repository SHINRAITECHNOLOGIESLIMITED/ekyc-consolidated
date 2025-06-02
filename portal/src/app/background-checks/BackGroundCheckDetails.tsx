"use client";

import { BackGroundCheck } from "@/types/models";
import {
  Box,
  ColumnLayout,
  Container,
  ExpandableSection,
  Header,
  SpaceBetween,
  StatusIndicator,
  Table,
} from "@cloudscape-design/components";

interface BackgroundCheckResultsProps {
    BestCountryScore: number;
    BestNameScore: number;
    EntityScore: number;
    ReasonListed: string;
    entityDetails: Array<{
      Comments: string | null;
      ID: number;
      Type: string;
      Value: string;
    }>;
}

const BackgroundCheckResults = ({ data }: { data: BackgroundCheckResultsProps }) => {
  // Helper function to determine risk level based on score
  // Define proper type for status
  type StatusIndicatorType = "success" | "warning" | "error" | "info" | "pending";
  
  const getRiskLevel = (score: number) => {
    if (score < 0) return { status: "pending" as StatusIndicatorType, label: "Pending" };
    if (score < 50) return { status: "success" as StatusIndicatorType, label: "Low Risk" };
    if (score < 80) return { status: "warning" as StatusIndicatorType, label: "Medium Risk" };
    return { status: "error" as StatusIndicatorType, label: "High Risk" };
  };

  const entityRisk = getRiskLevel(data.EntityScore);

  return (
    <Container header={<Header variant="h2">Background Check Results</Header>}>
      <SpaceBetween size="l">
        {/* Summary section */}
        <ColumnLayout columns={2} variant="text-grid">
          <SpaceBetween size="xs">
            <Box variant="awsui-key-label">Risk Level</Box>
            <StatusIndicator type={entityRisk.status}>
              {entityRisk.label} ({data.EntityScore})
            </StatusIndicator>
          </SpaceBetween>

          <SpaceBetween size="xs">
            <Box variant="awsui-key-label">Reason Listed</Box>
            <Box>{data.ReasonListed}</Box>
          </SpaceBetween>

          <SpaceBetween size="xs">
            <Box variant="awsui-key-label">Name Match Score</Box>
            <Box>{data.BestNameScore}</Box>
          </SpaceBetween>

          <SpaceBetween size="xs">
            <Box variant="awsui-key-label">Country Match Score</Box>
            <Box>{data.BestCountryScore}</Box>
          </SpaceBetween>
        </ColumnLayout>

        {/* Entity details section */}
        <ExpandableSection headerText="Entity Details">
          <Table
            columnDefinitions={[
              {
                id: "type",
                header: "Type",
                cell: (item) => item.Type,
                sortingField: "Type",
              },
              {
                id: "value",
                header: "Value",
                cell: (item) => item.Value,
              },
              {
                id: "comments",
                header: "Comments",
                cell: (item) => item.Comments || "-",
              },
            ]}
            items={data.entityDetails}
            sortingDisabled={false}
            variant="embedded"
            stickyHeader
          />
        </ExpandableSection>
      </SpaceBetween>
    </Container>
  );
};


const BackGroundCheckDetails = (backgroundCheck : BackGroundCheck) => (
  <SpaceBetween size="l">
    <Header variant="h1">Background Check</Header>
    <ColumnLayout columns={4} variant="text-grid">
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">First Name</Box>
        <Box>{backgroundCheck.firstName}</Box>
      </SpaceBetween>
      
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">Middle Name</Box>
        <Box>{backgroundCheck.middleName || "-"}</Box>
      </SpaceBetween>
      
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">Last Name</Box>
        <Box>{backgroundCheck.lastName}</Box>
      </SpaceBetween>
      
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">Gender</Box>
        <Box>{backgroundCheck.gender}</Box>
      </SpaceBetween>
      
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">Date Of Birth</Box>
        <Box>{backgroundCheck.dob}</Box>
      </SpaceBetween>
      
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">ID Number</Box>
        <Box>{backgroundCheck.nationalIdentificationNumber}</Box>
      </SpaceBetween>
      
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">Country Code</Box>
        <Box>{backgroundCheck.countryCode}</Box>
      </SpaceBetween>
      
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">Entity Type</Box>
        <Box>{backgroundCheck.entityType}</Box>
      </SpaceBetween>
      
      <SpaceBetween size="xs">
        <Box variant="awsui-key-label">Source Name</Box>
        <Box>{backgroundCheck.sourceName}</Box>
      </SpaceBetween>
    </ColumnLayout>

    {backgroundCheck.results && (
      <BackgroundCheckResults data={
                  typeof backgroundCheck.results === "string"
                    ? JSON.parse(backgroundCheck.results)
                    : (backgroundCheck.results as BackgroundCheckResultsProps)
                }
      />
    )}
  </SpaceBetween>
);

export default BackGroundCheckDetails;
