"use client";

import { Details, DetailsProps } from "@/components/Details";
import { fetchDocumentVerification } from "@/services/DataService";
import { DocumentVerification } from "@/types/models";
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

const itemDetails = (documentVerification: DocumentVerification) => (
  <Container>
    <SpaceBetween size="l">
      <Header variant="h1">Document Details</Header>

      <ColumnLayout columns={2} variant="text-grid">
        <SpaceBetween size="l">
          <div>
            <Box variant="awsui-key-label">Verification ID</Box>
            <div>{documentVerification.verificationId}</div>
          </div>

          <div>
            <Box variant="awsui-key-label">Document Type</Box>
            <div>{documentVerification.documentType}</div>
          </div>

          <div>
            <Box variant="awsui-key-label">Identifier</Box>
            <div>{documentVerification.documentIdentifier ?? ""}</div>
          </div>
        </SpaceBetween>
      </ColumnLayout>

      {(
        documentVerification.matchResults) && (
        <Container header={<Header variant="h2">Keyword Checks</Header>}>
          <Tabs
            tabs={[
              {
                label: "MatchResults",
                id: "searchedData",
                content: documentVerification.matchResults ? (
                  <CodeView
                    content={documentVerification.matchResults.toString()}
                    lineNumbers={true}
                    wrapLines={true}
                  />
                ) : (
                  <Box>No searched data available</Box>
                ),
                disabled: !documentVerification.matchResults,
              },
            ]}
          />
        </Container>
      )}
    </SpaceBetween>
  </Container>
);

const DocumentDetailsPageVerification: React.FC = () => {
  const params = useParams();
  const verificationId = Array.isArray(params.verificationId)
    ? params.verificationId[0]
    : params.verificationId;

  if (!verificationId) {
    return (
      <Alert type="error" header="Error" dismissible={false}>
        DocumentId not specified
      </Alert>
    );
  }
  const detailsParams: DetailsProps<DocumentVerification> = {
    title: "Contract",
    primaryKey: verificationId,
    fetcher: (VerificationId: string) => fetchDocumentVerification(VerificationId),
    itemDetails: itemDetails,
  };

  return <Details {...detailsParams} />;
};

export default DocumentDetailsPageVerification;
