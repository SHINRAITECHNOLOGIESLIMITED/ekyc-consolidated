"use client";

import { documentStreamingApi } from "@/services/api";
import { Box, Spinner } from "@cloudscape-design/components";
import { useEffect, useState } from "react";

interface CertificateViewerProps {
  objectKey: string;
  bucketType: string;
}

const DocumentViewer: React.FC<CertificateViewerProps> = ({ objectKey: objectKey,bucketType: bucketType }) => {
  const [certificateUrl, setCertificateUrl] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCertificateUrl = async () => {
      if (!objectKey) {
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      try {
        const url = await documentStreamingApi.getSignedUrl(bucketType, objectKey);
        setCertificateUrl(url);
      } catch (err) {
        console.error('Failed to get certificate URL:', err);
        setError('Failed to load certificate');
      } finally {
        setIsLoading(false);
      }
    };

    fetchCertificateUrl();
  }, [objectKey]);

  if (isLoading) {
    return (
      <Box textAlign="center" padding="l">
        <Spinner size="large" />
      </Box>
    );
  }

  if (error) {
    return <Box color="text-status-error">{error}</Box>;
  }

  if (!certificateUrl) {
    return <Box>No certificate available</Box>;
  }

  return (
    <Box padding="s">
      <iframe
        src={certificateUrl}
        title="Certificate"
        width="100%"
        height="600px"
        style={{ border: "none" }}
      />
    </Box>
  );
};

export default DocumentViewer;