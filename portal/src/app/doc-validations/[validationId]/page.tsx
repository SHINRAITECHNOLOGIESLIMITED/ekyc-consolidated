"use client";

import { Details, DetailsProps } from "@/components/Details";
import { fetchDocumentValidation } from "@/services/DataService";
import { DocumentValidation } from "@/types/models";
import { CodeView } from "@cloudscape-design/code-view";
import {
  Alert,
  Box,
  ColumnLayout,
  Container,
  Header,
  SpaceBetween,
  Tabs,
} from "@cloudscape-design/components";
import { useParams } from "next/navigation";
import React from "react";

const itemDetails = (documentValidation: DocumentValidation) => (
  <Container>
    <SpaceBetween size="l">
      <Header variant="h1">Document Details</Header>

      <ColumnLayout columns={2} variant="text-grid">
        <SpaceBetween size="l">
          <div>
            <Box variant="awsui-key-label">Validation ID</Box>
            <div>{documentValidation.validationId}</div>
          </div>

          <div>
            <Box variant="awsui-key-label">Document Type</Box>
            <div>{documentValidation.documentType}</div>
          </div>

          <div>
            <Box variant="awsui-key-label">Identifier</Box>
            <div>{documentValidation.validationIdentifier}</div>
          </div>
          <div>
            <Box variant="awsui-key-label">S3 Path</Box>
            <div>{documentValidation.s3Path}</div>
          </div>
        </SpaceBetween>
      </ColumnLayout>

      {(documentValidation.keywords_checks ||
        documentValidation.matchResults) && (
        <Container header={<Header variant="h2">Keyword Checks</Header>}>
          <Tabs
            tabs={[
              {
                label: "Keywords Checks",
                id: "keywordchecks",
                content: documentValidation.keywords_checks ? (
                  <CodeView
                    content={documentValidation.keywords_checks.toString()}
                    lineNumbers={true}
                    wrapLines={true}
                  />
                ) : (
                  <Box>No extracted data available</Box>
                ),
                disabled: !documentValidation.keywords_checks,
              },
              {
                label: "MatchResults",
                id: "searchedData",
                content: documentValidation.matchResults ? (
                  <CodeView
                    content={documentValidation.matchResults.toString()}
                    lineNumbers={true}
                    wrapLines={true}
                  />
                ) : (
                  <Box>No searched data available</Box>
                ),
                disabled: !documentValidation.matchResults,
              },
            ]}
          />
        </Container>
      )}
    </SpaceBetween>
  </Container>
);

const DocumentDetailsPageValidation: React.FC = () => {
  const params = useParams();
  const validationId = Array.isArray(params.validationId)
    ? params.validationId[0]
    : params.validationId;

  if (!validationId) {
    return (
      <Alert type="error" header="Error" dismissible={false}>
        DocumentId not specified
      </Alert>
    );
  }
  const detailsParams: DetailsProps<DocumentValidation> = {
    title: "Contract",
    primaryKey: validationId,
    fetcher: (validationId: string) => fetchDocumentValidation(validationId),
    itemDetails: itemDetails,
  };

  return <Details {...detailsParams} />;
};

export default DocumentDetailsPageValidation;
