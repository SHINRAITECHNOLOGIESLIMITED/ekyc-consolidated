"use client";

import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Container,
  Header,
  SpaceBetween,
  StatusIndicator,
} from "@cloudscape-design/components";
import { FaceLivenessDetector } from "@aws-amplify/ui-react-liveness";
import Image from 'next/image';

import { livenessApi } from "@/services/api";
import { handleApiError } from "@/utils/error";
import { LivenessResponse } from "@/types/liveness";
import { API_CONFIG } from "@/constants/api";

const LivenessDetection = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [processing, setProcessing] = useState<boolean>(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [result, setResult] = useState<LivenessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showCamera, setShowCamera] = useState<boolean>(true);
  const [imageError, setImageError] = useState<boolean>(false);

  useEffect(() => {
    const createLivenessSession = async (): Promise<void> => {
      try {
        const data = await livenessApi.createSession();
        setSessionId(data.sessionId);
        setError(null);
      } catch (err) {
        setError(handleApiError(err));
        console.error("Error creating liveness session:", err);
      } finally {
        setLoading(false);
      }
    };

    createLivenessSession();
  }, []);

  const handleAnalysisComplete = async (): Promise<void> => {
    if (!sessionId) {
      setError("No session ID available");
      return;
    }

    setProcessing(true);
    setError(null);

    try {
      const result: LivenessResponse = await livenessApi.getResults(sessionId);
      setResult(result);
      // Hide camera when liveness check is completed
      setShowCamera(false);
    } catch (err) {
      setError(handleApiError(err));
      console.error("Error getting liveness results:", err);
    } finally {
      setProcessing(false);
    }
  };

  const handleError = (error: Error): void => {
    setError(error.message);
    console.error("Liveness detection error:", error);
    setProcessing(false);
  };

  // Generate streaming API URL for liveness images
  const getLivenessImageUrl = (sessionId: string): string => {
    return `${API_CONFIG.API_BASE_URL}/stream/liveness/${sessionId}/reference.jpg`;
  };

  const renderResult = () => {
    if (!result) return null;

    return (
      <Container>
        <SpaceBetween size="m">
          <StatusIndicator type={result.isLive ? "success" : "error"}>
            {result.isLive ? "Liveness check passed" : "Liveness check failed"}
          </StatusIndicator>

          {result.confidence && (
            <Box variant="p">Confidence: {result.confidence.toFixed(2)}%</Box>
          )}

          <Box variant="p">Status: {result.status}</Box>

          {result.message && <Box variant="p">{result.message}</Box>}

          {/* Display liveness image using the streaming API */}
          {result.sessionId && result.isLive && !imageError && (
            <Box>
              <Box variant="h4">Liveness Reference Image</Box>
              <div style={{ marginTop: '10px', marginBottom: '10px', position: 'relative', width: '300px', height: '300px' }}>
                <Image
                  src={getLivenessImageUrl(result.sessionId)}
                  alt="Liveness reference"
                  fill
                  style={{ 
                    objectFit: 'contain',
                    border: '1px solid #ccc',
                    borderRadius: '4px'
                  }}
                  onError={() => {
                    console.error("Error loading liveness image");
                    setImageError(true);
                  }}
                />
              </div>
            </Box>
          )}

          <Button onClick={() => window.location.reload()}>Close</Button>
        </SpaceBetween>
      </Container>
    );
  };

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description="Complete the liveness check to verify your identity"
      >
        Liveness Detection
      </Header>

      {error && (
        <Alert
          type="error"
          header="Error"
          dismissible
          onDismiss={() => setError(null)}
        >
          {error}
        </Alert>
      )}

      {loading ? (
        <LoadingSpinner message="Initializing liveness detection..." />
      ) : processing ? (
        <LoadingSpinner message="Processing liveness check..." />
      ) : (
        <SpaceBetween size="l">
          {showCamera && (
            <Container>
              <FaceLivenessDetector
                sessionId={sessionId ?? ""}
                region={API_CONFIG.REGION}
                onError={(error) => handleError(error.error)}
                onAnalysisComplete={handleAnalysisComplete}
              />
            </Container>
          )}

          {result?.isLive && !showCamera && (
            <Alert type="success" header="Liveness Check Successful">
              Your identity has been successfully verified.
            </Alert>
          )}

          {renderResult()}
        </SpaceBetween>
      )}
    </SpaceBetween>
  );
};

interface LoadingSpinnerProps {
  message: string;
}

function LoadingSpinner({ message }: LoadingSpinnerProps) {
  return (
    <Container>
      <SpaceBetween size="xs" alignItems="center">
        <StatusIndicator type="loading">{message}</StatusIndicator>
      </SpaceBetween>
    </Container>
  );
}

export default LivenessDetection;