"use client";

import { documentStreamingApi } from "@/services/api";
import { Box, Spinner } from "@cloudscape-design/components";
import { useEffect, useState } from "react";

// Cache for storing signed URLs
const urlCache = new Map<string, { url: string; timestamp: number }>();
const CACHE_EXPIRY_MS = 3600000; // 1 hour cache expiry

interface CertificateViewerProps {
  objectKey: string;
  bucketType: string;
}

const DocumentViewer: React.FC<CertificateViewerProps> = ({ objectKey, bucketType }) => {
  const [certificateUrl, setCertificateUrl] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const cacheKey = `${bucketType}:${objectKey}`;

  useEffect(() => {
    const fetchCertificateUrl = async () => {
      if (!objectKey) {
        setIsLoading(false);
        return;
      }

      // Check if we have a valid cached URL
      const cachedData = urlCache.get(cacheKey);
      const now = Date.now();
      
      if (cachedData && (now - cachedData.timestamp) < CACHE_EXPIRY_MS) {
        setCertificateUrl(cachedData.url);
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      try {
        const url = await documentStreamingApi.getSignedUrl(bucketType, objectKey);
        setCertificateUrl(url);
        
        // Cache the URL with timestamp
        urlCache.set(cacheKey, { url, timestamp: now });
      } catch (err) {
        console.error('Failed to get certificate URL:', err);
        setError('Failed to load certificate');
      } finally {
        setIsLoading(false);
      }
    };

    fetchCertificateUrl();
  }, [objectKey, bucketType, cacheKey]);

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