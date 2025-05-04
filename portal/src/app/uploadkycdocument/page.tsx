"use client";


import UploadKYCDocument from "@/components/UploadKYCDocument";

const UploadKYCDocumentPage = () => {
    const handleUploadSuccess = (key: string, documentType: string) => {
        console.log('File uploaded successfully:', key);
        console.log('Document type:', documentType);
        // Handle success (e.g., show success message, update UI)
    };

    const handleUploadError = (error: Error) => {
        console.error('Upload failed:', error);
        // Handle error (e.g., show error message)
    };

    return (
        <UploadKYCDocument
            onSuccess={handleUploadSuccess}
            onError={handleUploadError}
        />
    );
};

export default UploadKYCDocumentPage;
