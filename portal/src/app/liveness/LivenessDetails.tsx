"use client";

import { documentStreamingApi } from "@/services/api";
import { LivenessSession } from "@/types/models";
import { formatDateTime, formatPercentage } from "@/utils/formatters";
import Image from "next/image";
import {
  Box,
  ColumnLayout,
  Container,
  Header,
  SpaceBetween,
  StatusIndicator,
  Spinner,
} from "@cloudscape-design/components";
import { useEffect, useState } from "react";

const getSignedUrl = async (objectkey: string): Promise<string> => {
  try {
    return await documentStreamingApi.getSignedUrl("liveness", objectkey);
  } catch (error) {
    console.error('Failed to get signed URL:', error);
    return '';
  }
};

const LivenessSessionDetails = (session: LivenessSession) => {
  const [referenceImageUrl, setReferenceImageUrl] = useState<string>('');
  const [auditImageUrls, setAuditImageUrls] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  


  useEffect(() => {
    const fetchUrls = async () => {
      setIsLoading(true);
      if (session.reference_image) {
        const refUrl = await getSignedUrl(session.reference_image);
        setReferenceImageUrl(refUrl);
      }
      
      if (session.audit_images) {
        const auditImages = JSON.parse(session.audit_images as string);
        if (auditImages.length > 0) {
          const auditUrls = await Promise.all(auditImages.map(getSignedUrl));
          setAuditImageUrls(auditUrls);
        }
      }
      
      setIsLoading(false);
    };
    
    fetchUrls();
  }, [session.reference_image, session.audit_images]);

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

        {isLoading ? (
          <Box textAlign="center">
            <Spinner size="large" />
          </Box>
        ) : (
          <>
            {referenceImageUrl && (
              <div>
                <Box variant="awsui-key-label">Reference Image</Box>
                <Box padding="s">
                  <Image 
                    src={referenceImageUrl} 
                    alt="Reference" 
                    width={300}
                    height={200}
                    style={{ objectFit: "contain" }}
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                    unoptimized
                  />
                </Box>
              </div>
            )}
            
            {auditImageUrls.length > 0 && (
              <div>
                <Box variant="awsui-key-label">Audit Images</Box>
                <Box padding="s">
                  <SpaceBetween size="s" direction="horizontal">
                    {auditImageUrls.map((imageUrl: string, index: number) => (
                      <Image 
                        key={index}
                        src={imageUrl} 
                        alt={`Audit image ${index + 1}`} 
                        width={150}
                        height={100}
                        style={{ objectFit: "contain", margin: "5px" }}
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                        }}
                        unoptimized
                      />
                    ))}
                  </SpaceBetween>
                </Box>
              </div>
            )}
          </>
        )}
      </SpaceBetween>
    </Container>
  );
};

export default LivenessSessionDetails;
