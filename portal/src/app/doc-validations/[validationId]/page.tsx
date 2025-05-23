"use client";

import { Details, DetailsProps } from "@/components/Details";
import KYCKeyWordsChecks, { KeyWordChecks } from "@/components/KYCKeyWordsChecks";
import KYCValidationResults, {
  ValidationResults,
} from "@/components/KYCValidationResults";
import { fetchDocumentValidation } from "@/services/DataService";
import { DocumentValidation } from "@/types/models";
import {
  Alert,
  Box,
  ColumnLayout,
  Header,
  SpaceBetween,
} from "@cloudscape-design/components";
import { useParams } from "next/navigation";
import React from "react";

const itemDetails = (documentValidation: DocumentValidation) => (
  <SpaceBetween size="l">
    <Header variant="h1" >{documentValidation.documentType} Document Validation</Header>

    <ColumnLayout columns={3} variant="text-grid">
      
        <div>
          <Box variant="awsui-key-label">{documentValidation.documentType} Identifier</Box>
          <div>{documentValidation.documentIdentifier}</div>
        </div>
        <div>
          <Box variant="awsui-key-label">Validation Id</Box>
          <div>{documentValidation.validationId}</div>
        </div>
        
        <div>
          <Box variant="awsui-key-label">S3 Path</Box>
          <div>{documentValidation.s3Path}</div>
        </div>
      
    </ColumnLayout>
    {documentValidation.keywords_checks && (
      <div>
        <KYCKeyWordsChecks
          results={
            typeof documentValidation.keywords_checks === "string"
              ? JSON.parse(documentValidation.keywords_checks)
              : (documentValidation.keywords_checks as KeyWordChecks)
          }
        />
      </div>
    )}

    {documentValidation.matchResults && (
      <KYCValidationResults
        results={
          typeof documentValidation.matchResults === "string"
            ? JSON.parse(documentValidation.matchResults)
            : (documentValidation.matchResults as ValidationResults)
        }
      />
    )}
  </SpaceBetween>
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
    title: "Validation",
    primaryKey: validationId,
    fetcher: (validationId: string) => fetchDocumentValidation(validationId),
    itemDetails: itemDetails,
  };

  return <Details {...detailsParams} />;
};

export default DocumentDetailsPageValidation;
