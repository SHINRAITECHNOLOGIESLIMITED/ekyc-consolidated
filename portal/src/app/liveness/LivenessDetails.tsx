"use client";

import { LivenessSession } from "@/types/models";
import { formatDateTime, formatPercentage } from "@/utils/formatters";
import {
  Box,
  ColumnLayout,
  Container,
  Header,
  SpaceBetween,
  StatusIndicator,
} from "@cloudscape-design/components";
import { StorageImage } from "@aws-amplify/ui-react-storage";

const LivenessSessionDetails = ( session : LivenessSession) => {
  // Parse audit images from JSON string
  const auditImages = session.audit_images ? JSON.parse(session.audit_images as string) : [];

  return (
    <Container>
      <SpaceBetween size="l">
        <Header variant="h1">Liveness Session Details</Header>
        
        <ColumnLayout columns={2} variant="text-grid">
          <SpaceBetween size="l">
            <div>
              <Box variant="awsui-key-label">Session ID</Box>
              <div>{session.sessionId}</div>
            </div>
            <div>
              <Box variant="awsui-key-label">Time</Box>
              <div>{formatDateTime(session.updatedAt)}</div>
            </div>
            <div>
              <Box variant="awsui-key-label">Status</Box>
              <StatusIndicator type={session.is_live ? "success" : "error"}>
                {session.is_live ? "Live" : "Not Live"}
              </StatusIndicator>
            </div>
          </SpaceBetween>
          <SpaceBetween size="l">
            <div>
              <Box variant="awsui-key-label">Confidence</Box>
              <div>{formatPercentage(session.confidence)}</div>
            </div>
            <div>
              <Box variant="awsui-key-label">Confidence Threshold</Box>
              <div>{formatPercentage(session.threshold)}</div>
            </div>
            <div>
              <Box variant="awsui-key-label">Remarks</Box>
              <div>{session.status}</div>
            </div>
          </SpaceBetween>
        </ColumnLayout>
        
        {session.reference_image && (
          <div>
            <Box variant="awsui-key-label">Reference Image</Box>
            <Box padding="s">
              <StorageImage 
                path={session.reference_image}
                alt="Reference"
                style={{ width: "300px", height: "300px", objectFit: "contain" }}
              />
            </Box>
          </div>
        )}
        
        {auditImages.length > 0 && (
          <div>
            <Box variant="awsui-key-label">Audit Images</Box>
            <Box padding="s">
              <SpaceBetween size="s" direction="horizontal">
                {auditImages.map((imageUrl: string, index: number) => (
                  <StorageImage 
                    key={index}
                    path={imageUrl}
                    alt={`Audit image ${index + 1}`}
                    style={{ width: "150px", height: "150px", objectFit: "contain", margin: "5px" }}
                  />
                ))}
              </SpaceBetween>
            </Box>
          </div>
        )}
      </SpaceBetween>
    </Container>
  );
};

export default LivenessSessionDetails;