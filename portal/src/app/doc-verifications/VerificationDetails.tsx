"use client";

import KYCValidationResults, {
  ValidationResults,
} from "@/components/KYCValidationResults";
import { DocumentVerification } from "@/types/models";
import { formatDateTime } from "@/utils/formatters";
import {
  Box,
  ColumnLayout,
  Header,
  SpaceBetween,
} from "@cloudscape-design/components";

const VerificationDetails = (documentVerification: DocumentVerification) => (
  <SpaceBetween size="l">
    <Header variant="h1">
      {documentVerification.documentType} Verification
    </Header>
    <ColumnLayout columns={4} variant="text-grid">
      <div>
        <Box variant="awsui-key-label">
          {documentVerification.documentType} Identifier
        </Box>
        <div>{documentVerification.documentIdentifier ?? ""}</div>
      </div>
      <div>
        <Box variant="awsui-key-label">
          Accuracy (%)
        </Box>
        <div>formatPercentage(documentVerification.overall_accuracy)</div>
      </div>
      <div>
        <Box variant="awsui-key-label">Updated</Box>
        <div>{formatDateTime(documentVerification.updatedAt)}</div>
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

export default VerificationDetails;
