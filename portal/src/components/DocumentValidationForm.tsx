"use client";

import { useAuthenticator } from "@aws-amplify/ui-react";
import { FileUploader } from "@aws-amplify/ui-react-storage";
import {
  Alert,
  Button,
  Container,
  Form,
  FormField,
  Header,
  SpaceBetween,
} from "@cloudscape-design/components";
import React, { useState } from "react";
import { v4 as uuidv4 } from "uuid";

// Define response data interface
interface ValidationResponse {
  results: {
    matchResults: Record<string, unknown>;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

// Define the common props for all document validation forms
interface DocumentValidationFormProps {
  title: string;
  documentType: "nationalid" | "passport" | "krapincertificate" | "cr12";
  apiEndpoint: string;
  fields: Array<{
    id: string;
    label: string;
    type?: "text" | "date";
    required?: boolean;
  }>;
  onSuccess?: (data: ValidationResponse) => void;
  onError?: (error: Error) => void;
}

const DocumentValidationForm: React.FC<DocumentValidationFormProps> = ({
  title,
  documentType,
  apiEndpoint,
  fields,
  onSuccess,
  onError,
}) => {
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [uploadedDocumentUrl, setUploadedDocumentUrl] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const { user } = useAuthenticator((context) => [context.user]);

  const handleInputChange = (id: string, value: string) => {
    setFormData((prev) => ({ ...prev, [id]: value }));
  };

  interface ProcessFileInput {
    file: File;
  }

  interface ProcessFileOutput {
    file: File;
    key: string;
  }

  const processFile = async ({
    file,
  }: ProcessFileInput): Promise<ProcessFileOutput> => {
    const fileExtension = file.name.split(".").pop() || "";
    return file
      .arrayBuffer()
      .then((filebuffer: ArrayBuffer) =>
        window.crypto.subtle.digest("SHA-1", filebuffer)
      )
      .then((hashBuffer: ArrayBuffer) => {
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray
          .map((a: number) => a.toString(16).padStart(2, "0"))
          .join("");
        return {
          file,
          key: `${user.userId}/${documentType}/${hashHex}.${fileExtension}`,
          metadata: {
            documentType: documentType,
            uploadDate: new Date().toISOString(),
          },
        };
      });
  };

  const handleUploadSuccess = async (event: { key?: string }) => {
    // Create the S3 URL format required by the API
    const s3Url = `s3://${process.env.NEXT_PUBLIC_S3_BUCKET_NAME}/${event.key}`;
    setUploadedDocumentUrl(s3Url);
  };

  const handleSubmit = async () => {
    if (!uploadedDocumentUrl) {
      setError("Please upload a document first");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const payload = {
        ...formData,
        uploadedDocumentUrl,
      };

      const response = await fetch(apiEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data = await response.json();
      setSuccess(true);
      if (onSuccess) onSuccess(data);
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : "An error occurred during validation";
      setError(errorMessage);
      if (onError)
        onError(err instanceof Error ? err : new Error(errorMessage));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container header={<Header variant="h2">{title}</Header>}>
      {error && <Alert type="error">{error}</Alert>}
      {success && (
        <Alert type="success">Document validated successfully!</Alert>
      )}

      <Form
        actions={
          <SpaceBetween direction="horizontal" size="xs">
            <Button variant="link">Cancel</Button>
            <Button
              variant="primary"
              onClick={handleSubmit}
              loading={isLoading}
              disabled={!uploadedDocumentUrl}
            >
              Validate Document
            </Button>
          </SpaceBetween>
        }
      >
        <SpaceBetween size="l">
          <FormField
            label="Upload Document"
            description="Upload the document for validation"
            constraintText="Supported formats: JPG, PNG, PDF"
          >
            <FileUploader
              acceptedFileTypes={[".pdf", ".jpg", ".jpeg", ".png", "image/*"]}
              maxFileCount={1}
              processFile={processFile}
              path={() => `${documentType}/${uuidv4()}/`}
              onUploadSuccess={handleUploadSuccess}
              onUploadError={(message: string) => {
                setError(message);
                onError?.(Error(message));
              }}
            />
          </FormField>

          {fields.map((field) => (
            <FormField
              key={field.id}
              label={field.label}
              constraintText={field.required ? "Required" : "Optional"}
            >
              {field.type === "date" ? (
                <input
                  type="date"
                  value={formData[field.id] || ""}
                  onChange={(e) => handleInputChange(field.id, e.target.value)}
                  required={field.required}
                  style={{ width: "100%", padding: "8px" }}
                />
              ) : (
                <input
                  type="text"
                  value={formData[field.id] || ""}
                  onChange={(e) => handleInputChange(field.id, e.target.value)}
                  required={field.required}
                  style={{ width: "100%", padding: "8px" }}
                />
              )}
            </FormField>
          ))}
        </SpaceBetween>
      </Form>
    </Container>
  );
};

export default DocumentValidationForm;
