"use client";

import React, {useState} from 'react';
import {Alert, Container, FormField, Input, Select, SelectProps, SpaceBetween,} from '@cloudscape-design/components';
import {FileUploader} from '@aws-amplify/ui-react-storage';
import '@aws-amplify/ui-react/styles.css';
import {documentApi} from "@/services/api";
import {useAuthenticator} from "@aws-amplify/ui-react";

interface UploadKYCDocumentProps {
    onSuccess?: (key: string, documentType: string, customerId: string) => void;
    onError?: (error: Error) => void;
}

const DOCUMENT_TYPES = [
    {label: 'Kenyan National ID', value: 'KENYAN_NATIONAL_ID'},
    {label: 'Kenyan Passport', value: 'KENYAN_PASSPORT'},
    {label: 'KRA Pin Certificate', value: 'KRA_PIN_CERTIFICATE'},
    {label: 'Certificate of Incorporation', value: 'CERTIFICATE_OF_INCORPORATION'},
    {label: 'IRA Certificate', value: 'IRA_CERTIFICATE'},
    {label: 'Kenyan Alien ID', value: 'KENYAN_ALIEN_ID'},
    {label: 'Kenyan Diplomatic ID', value: 'KENYAN_DIPLOMATIC_ID'},
    {label: 'Kenyan Military ID', value: 'KENYAN_MILITARY_ID'},
    {label: 'Kenyan Refugee ID', value: 'KENYAN_REFUGEE_ID'},
    {label: 'Dependant Pass', value: 'DEPENDANT_PASS'},
    {label: 'Work Permit', value: 'WORK_PERMIT'},
    {label: 'Permanent Residence', value: 'PERMANENT_RESIDENCE'},
];

const UploadKYCDocument: React.FC<UploadKYCDocumentProps> = ({
                                                                 onSuccess,
                                                                 onError
                                                             }) => {
    const [documentType, setDocumentType] = useState<SelectProps.Option | null>(null);
    const [customerId, setCustomerId] = useState<string>('');
    const [customerIdError, setCustomerIdError] = useState<string>('');
    const [error, setError] = useState<string>('');
    const [success, setSuccess] = useState<string>('');
    const {user} = useAuthenticator((context) => [context.user]);

    const validateCustomerId = (value: string): boolean => {
        if (!value || value.length < 5) {
            setCustomerIdError('Customer identifier must be at least 5 digits');
            return false;
        }
        setCustomerIdError('');
        return true;
    };

    const handleUploadSuccess = async (event: { key?: string, bucket?: string, region?: string, url?: string }) => {
        if (!event.key) {
            throw new Error('Upload key is missing');
        }
        if (!customerId) {
            setError('Please specify the customer identifier');
            return;
        }
        if (!documentType) {
            setError('Please select a document type');
            return;
        }
        const customerIdValue: string = customerId ?? "";
        const documentTypeValue: string = documentType.value ?? "";
        try {
            await documentApi.uploadDocument({
                documentType: documentTypeValue,
                customerId: customerIdValue,
                url: event.url ?? "",
                s3Path: `protected/eu-west-1:${user.userId}/${event.key}`
            });
            console.log(`Document uploaded successfully: ${event.url}`);
            setSuccess(`Document(${documentTypeValue}) uploaded successfully for customer ${customerId}`);
            setDocumentType(null);
            setError('');
            setCustomerId('');
            onSuccess?.(event.key, documentTypeValue, customerId);
        } catch (err) {
            setError('');
            setSuccess('');
            if (err instanceof Error) {
                setError(err.message);
                onError?.(err);
            } else {
                setError('An unexpected error occurred');
                onError?.(Error('An unexpected error occurred'));
            }
        }
    };

    interface ProcessFileInput {
        file: File;
    }

    interface ProcessFileOutput {
        file: File;
        key: string;
    }

    const processFile = async ({file}: ProcessFileInput): Promise<ProcessFileOutput> => {
        const fileExtension = file.name.split('.').pop() || '';
        const documentTypeValue: string = documentType?.value ?? "";
        return file
            .arrayBuffer()
            .then((filebuffer: ArrayBuffer) => window.crypto.subtle.digest('SHA-1', filebuffer))
            .then((hashBuffer: ArrayBuffer) => {
                const hashArray = Array.from(new Uint8Array(hashBuffer));
                const hashHex = hashArray
                    .map((a: number) => a.toString(16).padStart(2, '0'))
                    .join('');
                return {
                    file,
                    key: `${documentTypeValue}-${hashHex}.${fileExtension}`,
                    metadata: {
                        documentType: documentTypeValue,
                        customerId: customerId,
                        uploadDate: new Date().toISOString()
                    }
                };
            });
    };


    const getUploadPath = () => {
        if (!documentType) return '';
        try {
            return `${customerId}/`;
        } catch (error) {
            console.error('Error getting user identity:', error);
            return '';
        }
    };


    return (
        <Container>
            <SpaceBetween size="l">
                {error && (
                    <Alert type="error" dismissible onDismiss={() => setError('')}>
                        {error}
                    </Alert>
                )}
                {success && (
                    <Alert type="info" dismissible onDismiss={() => setSuccess('')}>
                        success
                    </Alert>
                )}
                <FormField
                    label="Customer Identifier"
                    description="Specify the customer identifier (minimum 5 digits)"
                    errorText={customerIdError}
                    constraintText="Must be at least 5 digits"
                >
                    <Input
                        value={customerId}
                        onChange={({detail}) => {
                            const value = detail.value;
                            setCustomerId(value);
                            validateCustomerId(value);
                        }}
                        onBlur={() => validateCustomerId(customerId)}
                        placeholder="Enter customer identifier"
                        type="text"
                        inputMode="numeric"
                    />
                </FormField>
                <FormField
                    label="Document Type"
                    description="Select the type of KYC document you are uploading"
                    errorText={!documentType ? 'Please select a document type' : undefined}
                >
                    <Select
                        selectedOption={documentType}
                        onChange={({detail}) => setDocumentType(detail.selectedOption)}
                        options={DOCUMENT_TYPES}
                        placeholder="Choose document type"
                        selectedAriaLabel="Selected"
                    />
                </FormField>

                <FormField
                    label="Upload Document"
                    description="Select a document to upload. Supported formats: PDF, JPG, PNG"
                >
                    {documentType ? (
                        <FileUploader
                            acceptedFileTypes={['.pdf', '.jpg', '.jpeg', '.png', 'image/*']}
                            accessLevel="protected"
                            maxFileCount={1}
                            processFile={processFile}
                            path={getUploadPath()}
                            onUploadSuccess={handleUploadSuccess}
                            onUploadError={(message: string) => {
                                setError(message);
                                onError?.(Error(message));
                            }}

                        />
                    ) : (
                        <Alert type="info">
                            Please specify customer identifier and select a document type before uploading
                        </Alert>
                    )}
                </FormField>
            </SpaceBetween>
        </Container>
    );
};

export default UploadKYCDocument;
