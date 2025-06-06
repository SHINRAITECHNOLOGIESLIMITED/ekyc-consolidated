"use client";

import { useAuthenticator } from "@aws-amplify/ui-react";
import { FileUploader } from "@aws-amplify/ui-react-storage";
import {
  Alert,
  Box,
  Button,
  ColumnLayout,
  Container,
  DatePicker,
  Form,
  FormField,
  Header,
  Input,
  SpaceBetween,
} from "@cloudscape-design/components";
import { eKYCApi } from "@/services/api";
import { Document, Page, pdfjs } from "react-pdf";
import React, { useState, useEffect, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";
import { DocumentValidationResponse } from "@/types/liveness";


// Define the common props for all document validation forms
interface DocumentValidationFormProps {
  title: string;
  documentType: "nationalid" | "passport" | "krapincertificate" | "cr12";
  fields: Array<{
    id: string;
    label: string;
    type?: "text" | "date";
    required?: boolean;
    placeholder?: string;
  }>;
  onSuccess?: (data: DocumentValidationResponse) => void;
  onError?: (error: Error) => void;
}

const DocumentValidationForm: React.FC<DocumentValidationFormProps> = ({
  title,
  documentType,
  fields,
  onSuccess,
  onError
}) => {
  // State declarations first
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [uploadedDocumentUrl, setUploadedDocumentUrl] = useState<string>("");
  const [uploadedFileName, setUploadedFileName] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [success, setSuccess] = useState<boolean>(false);
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [isFormValid, setIsFormValid] = useState<boolean>(false);
  
  // Initialize PDF.js worker
  useEffect(() => {
    pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;
  }, []);
  
  // Define validateForm before it's used in useEffect
  const validateForm = useCallback((currentFormData: Record<string, string> = formData) => {
    // Check if all required fields have values
    const requiredFieldsFilled = fields
      .filter(field => field.required)
      .every(field => currentFormData[field.id] && currentFormData[field.id].trim() !== '');
      
    // Form is valid if all required fields are filled and a document is uploaded
    setIsFormValid(requiredFieldsFilled && uploadedDocumentUrl !== '');
  }, [fields, formData, uploadedDocumentUrl]);

  // Validate form whenever dependencies change
  useEffect(() => {
    validateForm();
  }, [validateForm]);
  
  const { user } = useAuthenticator((context) => [context.user]);

  const handleInputChange = (id: string, value: string) => {
    const updatedFormData = { ...formData, [id]: value };
    setFormData(updatedFormData);
    validateForm(updatedFormData);
  };

  const handleClearForm = () => {
    setFormData({});
    setFieldErrors({});
    setIsFormValid(false);
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

  const handleUploadSuccess = async (event: { key?: string; file?: File }) => {
    // Create the S3 URL format required by the API
    const s3Url = `s3://${process.env.NEXT_PUBLIC_S3_BUCKET_NAME}/${event.key}`;
    setUploadedDocumentUrl(s3Url);

    // Save the file name for display
    if (event.file) {
      setUploadedFileName(event.file.name);
    }
    
    // Revalidate the form after document upload
    validateForm();
  };

  const handleSubmit = async () => {
    if (!uploadedDocumentUrl) {
      setError("Please upload a document first");
      return;
    }

    // Validate required fields
    const newFieldErrors: Record<string, string> = {};
    let hasErrors = false;

    fields.forEach((field) => {
      if (field.required && !formData[field.id]) {
        newFieldErrors[field.id] = "This field is required";
        hasErrors = true;
      }
    });

    setFieldErrors(newFieldErrors);

    if (hasErrors) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const payload = {
        ...formData,
        uploadedDocumentUrl,
      };

      
      const data:DocumentValidationResponse = await eKYCApi.validateDocument(
        documentType, 
        JSON.stringify(payload)
      );
      if (data.error) {
        setError(data.error);
        return
      }
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
            <Button
              key="clear-button"
              variant="icon"
              onClick={handleClearForm}
              iconName="remove"
              ariaLabel="Clear form"
            />
            <Button key="cancel-button" variant="link" onClick={() => document.querySelector('[aria-label="Close modal"]')?.dispatchEvent(new MouseEvent('click', { bubbles: true }))}>
              Cancel
            </Button>
            <Button
              key="validate-button"
              variant="primary"
              onClick={handleSubmit}
              loading={isLoading}
              disabled={!isFormValid}
            >
              Validate Document
            </Button>
          </SpaceBetween>
        }
      >
        <SpaceBetween size="l">
          <ColumnLayout columns={2} variant="text-grid" borders="horizontal">
            {fields.map((field) => (
              <FormField
                key={field.id}
                label={field.required ? `${field.label} *` : field.label}
                errorText={fieldErrors[field.id]}
              >
                {field.type === "date" ? (
                  <DatePicker
                    value={formData[field.id] || ""}
                    onChange={({ detail }) =>
                      handleInputChange(field.id, detail.value)
                    }
                    placeholder="YYYY-MM-DD"
                    ariaLabel="Date picker"
                    i18nStrings={{
                      nextMonthAriaLabel: "Next month",
                      previousMonthAriaLabel: "Previous month",
                      todayAriaLabel: "Today"
                    }}
                  />
                ) : (
                  <Input
                    value={formData[field.id] || ""}
                    onChange={({ detail }) =>
                      handleInputChange(field.id, detail.value)
                    }
                    placeholder={field.placeholder || field.label}
                  />
                )}
              </FormField>
            ))}
          </ColumnLayout>

          <FormField
            label="Upload Document *"
            description="Upload the document for validation"
            constraintText="Supported formats: JPG, PNG, PDF"
          >
            <SpaceBetween size={"s"} direction="horizontal">
              <FileUploader
                acceptedFileTypes={[".pdf", ".jpg", ".jpeg", ".png", "image/*"]}
                maxFileCount={1}
                processFile={processFile}
                path={() => `uploaded_kyc_docs/${documentType}/${uuidv4()}/`}
                onUploadSuccess={handleUploadSuccess}
                onUploadError={(message: string) => {
                  setError(message);
                  onError?.(Error(message));
                }}
              />
              {uploadedDocumentUrl && (
                <Box textAlign="center" padding={{ bottom: "s" }}>
                  <Box variant="h4">Preview: {uploadedFileName}</Box>
                  <Box
                    padding="s"                  
                  >
                    <Document
                      file={`https://${process.env.NEXT_PUBLIC_S3_BUCKET_NAME}.s3.amazonaws.com/${uploadedDocumentUrl.replace("s3://", "")}`}
                      onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                      onLoadError={(error) =>
                        console.error("Error loading PDF:", error)
                      }
                      loading={<Box>Loading PDF...</Box>}
                      error={<Box>Failed to load PDF. {uploadedDocumentUrl}</Box>}
                    >
                      <Page
                        pageNumber={pageNumber}
                        width={300}
                        renderTextLayer={false}
                        renderAnnotationLayer={false}
                      />
                    </Document>
                  </Box>
                  {numPages && (
                    <Box padding="xs">
                      <SpaceBetween direction="horizontal" size="xs">
                        <Button
                          key="prev-button"
                          disabled={pageNumber <= 1}
                          onClick={() =>
                            setPageNumber((prev) => Math.max(prev - 1, 1))
                          }
                          iconName="angle-left"
                        />
                        <Box key="page-info">
                          Page {pageNumber} of {numPages}
                        </Box>
                        <Button
                          key="next-button"
                          disabled={pageNumber >= numPages}
                          onClick={() =>
                            setPageNumber((prev) =>
                              Math.min(prev + 1, numPages || 1)
                            )
                          }
                          iconName="angle-right"
                        />
                      </SpaceBetween>
                    </Box>
                  )}
                </Box>
              )}
            </SpaceBetween>
          </FormField>
        </SpaceBetween>
      </Form>
    </Container>
  );
};

export default DocumentValidationForm;
