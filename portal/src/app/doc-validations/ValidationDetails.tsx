"use client";

import DocumentViewer from "@/components/DocumentViewer";
import CopyableValue from "@/components/CopyableValue";
import KYCKeyWordsChecks, {
  KeyWordChecks,
} from "@/components/KYCKeyWordsChecks";
import KYCValidationResults, {
  ValidationResults,
} from "@/components/KYCValidationResults";
import IPRSValidationResults, {
  IPRSValidationResult,
} from "@/components/IPRSValidationResults";
import { API_CONFIG } from "@/constants/api"; // or wherever it's defined
import { DocumentValidation } from "@/types/models";
import { formatDateTime, formatPercentage } from "@/utils/formatters";
import {
  Box,
  ColumnLayout,
  Container,
  Header,
  SpaceBetween,
  Tabs,
} from "@cloudscape-design/components";

const ValidationDetails = (documentValidation: DocumentValidation) => {
  // Parse matchResults to extract IPRS validation data
  const matchResults = typeof documentValidation.matchResults === "string"
    ? JSON.parse(documentValidation.matchResults)
    : (documentValidation.matchResults as ValidationResults & {
        serialNumberValidation?: IPRSValidationResult;
        genderValidation?: IPRSValidationResult;
      });

  // Extract IPRS validation results (v1.2 features)
  const serialNumberValidation = matchResults?.serialNumberValidation as IPRSValidationResult | undefined;
  const genderValidation = matchResults?.genderValidation as IPRSValidationResult | undefined;

  // Filter out IPRS validation fields from regular matchResults for the standard table
  const standardMatchResults = matchResults ? Object.fromEntries(
    Object.entries(matchResults).filter(
      ([key]) => key !== "serialNumberValidation" && key !== "genderValidation"
    )
  ) as ValidationResults : undefined;

  return (
    <SpaceBetween size="l">
      <Header variant="h1">
        {documentValidation.documentType} Document Validation
      </Header>

      <ColumnLayout columns={4} variant="text-grid">
        <div>
          <Box variant="awsui-key-label">
            {documentValidation.documentType} Identifier
          </Box>
          <div>{documentValidation.documentIdentifier}</div>
        </div>
        <div>
          <Box variant="awsui-key-label">Processing Accuracy (%)</Box>
          <div>{formatPercentage(documentValidation.processing_accuracy)}</div>
        </div>
        <div>
          <Box variant="awsui-key-label">Validation Accuracy (%)</Box>
          <div>{formatPercentage(documentValidation.validation_accuracy)}</div>
        </div>
        <div>
          <Box variant="awsui-key-label">Confidence (%)</Box>
          <div>{formatPercentage(documentValidation.overall_confidence)}</div>
        </div>
        <div>
          <Box variant="awsui-key-label">Updated</Box>
          <div>{formatDateTime(documentValidation.updatedAt)}</div>
        </div>
        <div>
          <Box variant="awsui-key-label">Validation Id</Box>
          <div>{documentValidation.validationId}</div>
        </div>
      </ColumnLayout>
      <Tabs
        tabs={[
          {
            id: "details",
            label: "Validation Details",
            content: (
              <SpaceBetween size="l">
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

                {standardMatchResults && Object.keys(standardMatchResults).length > 0 && (
                  <KYCValidationResults results={standardMatchResults} />
                )}

                {(serialNumberValidation || genderValidation) && (
                  <IPRSValidationResults
                    serialNumberValidation={serialNumberValidation}
                    genderValidation={genderValidation}
                  />
                )}
              </SpaceBetween>
            ),
          },
          {
            id: "documents",
            label: "Document",
            content: (
              <Container header={<Header variant="h2">KYC Certificate</Header>}>
                <DocumentViewer
                  objectKey={documentValidation.s3Path}
                  bucketType={"kyc"}
                />
              </Container>
            ),
          },
        ]}
      />
      <div>
        <Box variant="awsui-key-label">S3 Path</Box>
        <SpaceBetween direction="horizontal" size="xs" alignItems="center">
          <CopyableValue
            label={documentValidation.s3Path}
            value={`${API_CONFIG.VALIDATED_DOCS_BASE_S3_PATH}${documentValidation.s3Path}`}
          />
        </SpaceBetween>
      </div>
    </SpaceBetween>
  );
};

export default ValidationDetails;
