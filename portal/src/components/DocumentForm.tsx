"use client";

import { useAuthenticator } from "@aws-amplify/ui-react";
import { FileUploader } from "@aws-amplify/ui-react-storage";
import {
  Modal,
  Box,
  Alert,
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
import React, { useState, useEffect, useCallback } from "react";
import { DocumentValidationResponse } from "@/types/liveness";
import { API_CONFIG } from "@/constants/api";
import CopyableValue from "./CopyableValue";

// Define field types
interface BaseField {
  id: string;
  label: string;
  required?: boolean;
}

interface TextField extends BaseField {
  type: "text";
  placeholder?: string;
}

interface DateField extends BaseField {
  type: "date";
  placeholder?: string;
}

interface DocumentField extends BaseField {
  type: "document";
  acceptedFileTypes?: string[];
  description?: string;
  constraintText?: string;
}

type FormField = TextField | DateField | DocumentField;

// Define the common props for all document validation forms
interface DocumentValidationFormProps {
  title: string;
  documentType: "nationalid" | "passport" | "krapincertificate" | "cr12";
  fields: FormField[];
  onSuccess?: (data: DocumentValidationResponse) => void;
  onError?: (error: Error) => void;
}

const DocumentForm: React.FC<DocumentValidationFormProps> = ({
  title,
  documentType,
  fields,
  onSuccess,
  onError,
}) => {
  // State declarations first
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [success, setSuccess] = useState<boolean>(false);
  const [isFormValid, setIsFormValid] = useState<boolean>(false);
  const [showSuccessDialog, setShowSuccessDialog] = useState<boolean>(false);
  const [proccesingDocumentId, setProccesingDocumentId] = useState<string>("");
  

  // Define validateForm before it's used in useEffect
  const validateForm = useCallback(
    (currentFormData: Record<string, string> = formData) => {
      // Check if all required fields have values
      const requiredFieldsFilled = fields
        .filter((field) => field.required)
        .every((field) => {
          // For all fields including document fields
          return (
            currentFormData[field.id] && currentFormData[field.id].trim() !== ""
          );
        });

      setIsFormValid(requiredFieldsFilled);
    },
    [fields, formData]
  );

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
    fieldId: string;
  }

  interface ProcessFileOutput {
    file: File;
    key: string;
    fieldId: string;
  }

  const processFile = async ({
    file,
    fieldId,
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
          fieldId,
          key: `${user.userId}/${documentType}/${fieldId}/${hashHex}.${fileExtension}`,
          metadata: {
            documentType: documentType,
            fieldId: fieldId,
            uploadDate: new Date().toISOString(),
          },
        };
      });
  };

  const handleUploadSuccess = async (event: {
    key?: string;
    fieldId: string;
  }) => {
    // Save the file URL in the form data as an array of URLs
    const s3Url = `${API_CONFIG.UPLOADED_DOCS_BASE_S3_PATH}/${event.key}`;

    // Update the form data with the new document URL
    setFormData((prevData) => {
      const fieldId = event.fieldId;
      return {
        ...prevData,
        [fieldId]: s3Url,
      };
    });

    // Revalidate the form after document upload
    validateForm();
  };

  const handleSubmit = async () => {
    // Validate required fields
    const newFieldErrors: Record<string, string> = {};
    let hasErrors = false;

    fields.forEach((field) => {
      if (field.required) {
        if (
          !formData[field.id] ||
          (formData[field.id] as string).trim() === ""
        ) {
          newFieldErrors[field.id] = "This field is required";
          hasErrors = true;
        }
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
      };

      const data: DocumentValidationResponse = await eKYCApi.validateDocument(
        documentType,
        JSON.stringify(payload)
      );
      if (data.error) {
        setError(data.error);
        return;
      }
      setSuccess(true);
      //Close the form as show a success dialoge asking user if they want to view the details
      setShowSuccessDialog(false);
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

  const renderField = (field: FormField) => {
    if (field.type === "date") {
      return (
        <DatePicker
          value={(formData[field.id] as string) || ""}
          onChange={({ detail }) => handleInputChange(field.id, detail.value)}
          placeholder={field.placeholder || "YYYY-MM-DD"}
          ariaLabel="Date picker"
          i18nStrings={{
            nextMonthAriaLabel: "Next month",
            previousMonthAriaLabel: "Previous month",
            todayAriaLabel: "Today",
          }}
        />
      );
    } else if (field.type === "document") {
      return (
        <FileUploader
          acceptedFileTypes={
            field.acceptedFileTypes || [
              ".pdf",
              ".jpg",
              ".jpeg",
              ".png",
              "image/*",
            ]
          }
          bucket={API_CONFIG.UPLOADED_DOCS_BASE_S3_PATH}
          maxFileCount={1}
          path="uploaded_kyc_docs/"
          processFile={(params) =>
            processFile({ ...params, fieldId: field.id })
          }
          onUploadSuccess={(event) =>
            handleUploadSuccess({ ...event, fieldId: field.id })
          }
          onUploadError={(message: string) => {
            setError(message);
            onError?.(Error(message));
          }}
        />
      );
    } else {
      // Default to text input
      return (
        <Input
          value={(formData[field.id] as string) || ""}
          onChange={({ detail }) => handleInputChange(field.id, detail.value)}
          placeholder={field.placeholder || field.label}
        />
      );
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
          <ColumnLayout columns={3} variant="text-grid" borders="horizontal">
            {fields
              .filter((field) => field.type !== "document")
              .map((field) => (
                <FormField
                  key={field.id}
                  label={field.required ? `${field.label} *` : field.label}
                  errorText={fieldErrors[field.id]}
                >
                  {renderField(field)}
                </FormField>
              ))}
          </ColumnLayout>

          {fields
            .filter((field) => field.type === "document")
            .map((field) => (
              <FormField
                key={field.id}
                label={field.required ? `${field.label} *` : field.label}
                description={
                  field.type === "document"
                    ? (field as DocumentField).description
                    : undefined
                }
                constraintText={
                  field.type === "document"
                    ? (field as DocumentField).constraintText
                    : undefined
                }
                errorText={fieldErrors[field.id]}
              >
                {renderField(field)}
              </FormField>
            ))}
        </SpaceBetween>
      </Form>
      <Modal
        onDismiss={() => setShowSuccessDialog(false)}
        visible={showSuccessDialog}
        header="Document Validation Successful!"
        closeAriaLabel="Close dialog"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button
                onClick={() => setShowSuccessDialog(false)}
                //TODO: Close parent modal
                variant="link"
              >
                Close
              </Button>
              {/* You might want a button to view details */}
              
            </SpaceBetween>
          </Box>
        }
      >
        <p>Processsing sucessfully.</p>
        <CopyableValue label={"id"} value={documentId}>

        </CopyableValue>
      </Modal>
    </Container>
  );
};

export default DocumentForm;
