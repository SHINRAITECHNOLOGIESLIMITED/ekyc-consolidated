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
import Image from "next/image";

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
          </SpaceBetween>
          <SpaceBetween size="l">
            <div>
              <Box variant="awsui-key-label">Confidence</Box>
              <div>{formatPercentage(session.confidence)}</div>
            </div>
            
            <div>
              <Box variant="awsui-key-label">Status</Box>
              <StatusIndicator type={session.is_live ? "success" : "error"}>
                {session.is_live ? "Live" : "Not Live"}
              </StatusIndicator>
            </div>
          </SpaceBetween>
        </ColumnLayout>
        
        {session.reference_image && (
          <div>
            <Box variant="awsui-key-label">Reference Image</Box>
            <Box padding="s">
              <div style={{ position: "relative", width: "300px", height: "300px" }}>
                <Image 
                  src={session.reference_image} 
                  alt="Reference" 
                  fill
                  style={{ objectFit: "contain" }}
                />
              </div>
            </Box>
          </div>
        )}
        
        {auditImages.length > 0 && (
          <div>
            <Box variant="awsui-key-label">Audit Images</Box>
            <Box padding="s">
              <SpaceBetween size="s" direction="horizontal">
                {auditImages.map((imageUrl: string, index: number) => (
                  <div 
                    key={index} 
                    style={{ position: "relative", width: "150px", height: "150px", margin: "5px" }}
                  >
                    <Image 
                      src={imageUrl} 
                      alt={`Audit image ${index + 1}`} 
                      fill
                      style={{ objectFit: "contain" }}
                    />
                  </div>
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