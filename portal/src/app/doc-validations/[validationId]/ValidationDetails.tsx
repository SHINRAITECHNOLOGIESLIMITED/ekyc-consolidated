"use client";

import CopyableValue from "@/components/CopyableValue";
import KYCKeyWordsChecks, {
  KeyWordChecks,
} from "@/components/KYCKeyWordsChecks";
import KYCValidationResults, {
  ValidationResults,
} from "@/components/KYCValidationResults";
import { API_CONFIG } from "@/constants/api"; // or wherever it's defined
import { DocumentValidation } from "@/types/models";
import { formatDateTime } from "@/utils/formatters";
import {
  Box,
  ColumnLayout,
  Header,
  SpaceBetween,
} from "@cloudscape-design/components";

const ValidationDetails = (documentValidation: DocumentValidation) => (
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
        <Box variant="awsui-key-label">Updated</Box>
        <div>{formatDateTime(documentValidation.updatedAt)}</div>
      </div>
      <div>
        <Box variant="awsui-key-label">Validation Id</Box>
        <div>{documentValidation.validationId}</div>
      </div>
    </ColumnLayout>
    <div>
      <Box variant="awsui-key-label">S3 Path</Box>
      <SpaceBetween direction="horizontal" size="xs" alignItems="center">
        <CopyableValue
          label={documentValidation.s3Path}
          value={`${API_CONFIG.VALIDATED_DOCS_BASE_S3_PATH}${documentValidation.s3Path}`}
        />
      </SpaceBetween>
    </div>

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

export default ValidationDetails;