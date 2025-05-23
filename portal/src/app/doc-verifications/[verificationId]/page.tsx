"use client";

import { Details, DetailsProps } from "@/components/Details";
import KYCValidationResults, {
  ValidationResults,
} from "@/components/KYCValidationResults";
import { fetchDocumentVerification } from "@/services/DataService";
import { DocumentVerification } from "@/types/models";
import {
  Alert,
  Box,
  ColumnLayout,
  Header,
  SpaceBetween,
} from "@cloudscape-design/components";
import { useParams } from "next/navigation";
import React from "react";

const itemDetails = (documentVerification: DocumentVerification) => (
  <SpaceBetween size="l">
    <Header variant="h1" >{documentVerification.documentType} Verification</Header>
    <ColumnLayout columns={3} variant="text-grid">
        <div>
          <Box variant="awsui-key-label">{documentVerification.documentType} Identifier</Box>
          <div>{documentVerification.documentIdentifier ?? ""}</div>
        </div>
        <div>
          <Box variant="awsui-key-label">Verification ID</Box>
          <div>{documentVerification.verificationId}</div>
        </div>
    </ColumnLayout>
    {documentVerification.matchResults && (
      <KYCValidationResults
        results={
          typeof documentVerification.matchResults === "string"
            ? JSON.parse(documentVerification.matchResults)
            : (documentVerification.matchResults as ValidationResults)
        }
      />
    )}
  </SpaceBetween>
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
    title: "Verification",
    primaryKey: verificationId,
    fetcher: (VerificationId: string) =>
      fetchDocumentVerification(VerificationId),
    itemDetails: itemDetails,
  };

  return <Details {...detailsParams} />;
};

export default DocumentDetailsPageVerification;
