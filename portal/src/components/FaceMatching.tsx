"use client";

import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Container,
  ColumnLayout,
  Form,
  FormField,
  Header,
  Input,
  Select,
  SpaceBetween,
  StatusIndicator,
} from "@cloudscape-design/components";
import { eKYCApi } from "@/services/api";
import { handleApiError } from "@/utils/error";

interface FaceMatchResult {
  overall_decision: string;
  comparisons: Record<string, { similarity: number; matched: boolean; error?: string }>;
  lowest_score: number | null;
  iprs_photo_available: boolean;
  document_type: string;
  requires_manual_review: boolean;
  thresholds: { auto_approve: number; manual_review: number };
  error?: string;
}

interface FaceMatchingProps {
  sessionId: string;
  onClose?: () => void;
}

const DOCUMENT_TYPE_OPTIONS = [
  { label: "National ID", value: "national_id" },
  { label: "Alien ID", value: "alien_id" },
  { label: "Passport", value: "passport" },
  { label: "Military ID", value: "military_id" },
];

const FaceMatching = ({ sessionId, onClose }: FaceMatchingProps) => {
  const [documentType, setDocumentType] = useState(DOCUMENT_TYPE_OPTIONS[0]);
  const [documentS3Path, setDocumentS3Path] = useState("");
  const [idNumber, setIdNumber] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FaceMatchResult | null>(null);

  const handleSubmit = async () => {
    if (!documentS3Path.trim() || !idNumber.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = {
        action: "face_match",
        data: {
          sessionId,
          documentType: documentType.value,
          documentS3Path: documentS3Path.trim(),
          idNumber: idNumber.trim(),
        },
      };

      const response = await eKYCApi.call("kyc", JSON.stringify(payload));
      const body = typeof response === "string" ? JSON.parse(response) : response;

      if (body.error) {
        setError(body.error);
        return;
      }

      // The face match result may be nested in body.data or directly in body
      const matchResult = body.data?.face_match || body.data || body;
      setResult(matchResult as FaceMatchResult);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const getDecisionIndicator = (decision: string) => {
    switch (decision) {
      case "AUTO_APPROVED":
        return <StatusIndicator type="success">Auto Approved</StatusIndicator>;
      case "MANUAL_REVIEW":
        return <StatusIndicator type="warning">Manual Review Required</StatusIndicator>;
      case "AUTO_REJECTED":
        return <StatusIndicator type="error">Auto Rejected</StatusIndicator>;
      case "PARTIAL_MATCH":
        return <StatusIndicator type="warning">Partial Match</StatusIndicator>;
      case "ERROR":
        return <StatusIndicator type="error">Error</StatusIndicator>;
      default:
        return <StatusIndicator type="info">{decision}</StatusIndicator>;
    }
  };

  const renderResult = () => {
    if (!result) return null;

    return (
      <Container header={<Header variant="h3">Face Match Result</Header>}>
        <SpaceBetween size="m">
          <ColumnLayout columns={2} variant="text-grid">
            <div>
              <Box variant="awsui-key-label">Decision</Box>
              {getDecisionIndicator(result.overall_decision)}
            </div>
            <div>
              <Box variant="awsui-key-label">Lowest Score</Box>
              <Box>{result.lowest_score != null ? `${result.lowest_score.toFixed(2)}%` : "N/A"}</Box>
            </div>
            <div>
              <Box variant="awsui-key-label">IPRS Photo Available</Box>
              <StatusIndicator type={result.iprs_photo_available ? "success" : "warning"}>
                {result.iprs_photo_available ? "Yes" : "No"}
              </StatusIndicator>
            </div>
            <div>
              <Box variant="awsui-key-label">Manual Review</Box>
              <StatusIndicator type={result.requires_manual_review ? "warning" : "success"}>
                {result.requires_manual_review ? "Required" : "Not Required"}
              </StatusIndicator>
            </div>
          </ColumnLayout>

          {result.comparisons && (
            <>
              <Header variant="h4">Comparisons</Header>
              <ColumnLayout columns={3} variant="text-grid">
                {Object.entries(result.comparisons).map(([pair, comp]) => (
                  <div key={pair}>
                    <Box variant="awsui-key-label">{pair.replace(/_/g, " ")}</Box>
                    <Box>
                      Similarity: {comp.similarity?.toFixed(2)}%
                      {" "}
                      <StatusIndicator type={comp.matched ? "success" : "error"}>
                        {comp.matched ? "Matched" : "Not Matched"}
                      </StatusIndicator>
                    </Box>
                    {comp.error && <Box color="text-status-error">{comp.error}</Box>}
                  </div>
                ))}
              </ColumnLayout>
            </>
          )}

          {result.error && (
            <Alert type="error">{result.error}</Alert>
          )}

          <Button onClick={onClose || (() => window.location.reload())}>Close</Button>
        </SpaceBetween>
      </Container>
    );
  };

  return (
    <SpaceBetween size="l">
      <Header variant="h2" description="Compare liveness selfie against document photo and IPRS photo">
        Face Matching
      </Header>

      {error && (
        <Alert type="error" dismissible onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}

      {!result ? (
        <Form
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              <Button variant="primary" onClick={handleSubmit} loading={loading}
                disabled={!documentS3Path.trim() || !idNumber.trim()}>
                Run Face Match
              </Button>
            </SpaceBetween>
          }
        >
          <Container>
            <SpaceBetween size="l">
              <FormField label="Session ID">
                <Input value={sessionId} disabled />
              </FormField>
              <ColumnLayout columns={2}>
                <FormField label="Document Type *">
                  <Select
                    selectedOption={documentType}
                    onChange={({ detail }) =>
                      setDocumentType(detail.selectedOption as typeof documentType)
                    }
                    options={DOCUMENT_TYPE_OPTIONS}
                  />
                </FormField>
                <FormField label="ID Number *">
                  <Input
                    value={idNumber}
                    onChange={({ detail }) => setIdNumber(detail.value)}
                    placeholder="23667272"
                  />
                </FormField>
              </ColumnLayout>
              <FormField label="Document S3 Path *"
                description="S3 key of the uploaded document (from document validation)">
                <Input
                  value={documentS3Path}
                  onChange={({ detail }) => setDocumentS3Path(detail.value)}
                  placeholder="uploaded_kyc_docs/user123/document/nationalid/abc123.pdf"
                />
              </FormField>
            </SpaceBetween>
          </Container>
        </Form>
      ) : (
        renderResult()
      )}
    </SpaceBetween>
  );
};

export default FaceMatching;
