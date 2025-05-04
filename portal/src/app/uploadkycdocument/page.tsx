"use client";


import UploadKYCDocument from "@/components/UploadKYCDocument";

const UploadKYCDocumentPage = () => {
    const handleUploadSuccess = (key: string, documentType: string) => {
        console.log('File uploaded successfully:', key);
        console.log('Document type:', documentType);
    };

    const handleUploadError = (error: Error) => {
        console.error('Upload failed:', error);
    };

    return (
        <UploadKYCDocument
            onSuccess={handleUploadSuccess}
            onError={handleUploadError}
        />
    );
};

export default UploadKYCDocumentPage;
