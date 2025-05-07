"use client"

import {Details, DetailsProps} from "@/components/Details";
import {fetchDocument} from "@/services/DataService";
import {Alert, Box, ColumnLayout, Container, Header, SpaceBetween} from '@cloudscape-design/components';
import {useParams} from 'next/navigation';
import React from 'react';
import {KYCDocument} from "@/types/models";

const itemDetails = (documentId: KYCDocument) => (
    <Container>
        <SpaceBetween size="l">
            <Header variant="h1">
                Document Details
            </Header>

            <ColumnLayout columns={2} variant="text-grid">
                <SpaceBetween size="l">
                    <div>
                        <Box variant="awsui-key-label">Document ID</Box>
                        <div>{documentId.documentId}</div>
                    </div>

                    <div>
                        <Box variant="awsui-key-label">Customer ID</Box>
                        <div>{documentId.customerId}</div>
                    </div>

                    <div>
                        <Box variant="awsui-key-label">Document Type</Box>
                        <div>{documentId.documentType}</div>
                    </div>

                    <div>
                        <Box variant="awsui-key-label">Status</Box>
                        <div>{documentId.documentStatus}</div>
                    </div>

                    {documentId.identifier && (
                        <div>
                            <Box variant="awsui-key-label">Identifier</Box>
                            <div>{documentId.identifier}</div>
                        </div>
                    )}

                    <div>
                        <Box variant="awsui-key-label">S3 Path</Box>
                        <div>{documentId.s3Path}</div>
                    </div>
                </SpaceBetween>
            </ColumnLayout>

            {documentId.extractedData && (
                <Container header={<Header variant="h2">Extracted Data</Header>}>
                    <div>
                        {JSON.stringify(documentId.extractedData, null, 2)}
                    </div>
                </Container>
            )}

            {documentId.verifiedData && (
                <Container header={<Header variant="h2">Verified Data</Header>}>
                    <div>
                        {JSON.stringify(documentId.verifiedData, null, 2)}
                    </div>
                </Container>
            )}
        </SpaceBetween>
    </Container>
);


const KYCDocumentDetailsPage: React.FC = () => {
    const params = useParams();
    const documentId = Array.isArray(params.documentId) ? params.documentId[0] : params.documentId;

    if (!documentId) {
        return (
            <Alert
                type="error"
                header="Error"
                dismissible={false}
            >
                DocumentId not specified
            </Alert>
        );
    }
    const detailsParams: DetailsProps<KYCDocument> = {
        title: "Contract",
        primaryKey: documentId,
        fetcher: (documentId: string) => fetchDocument(documentId),
        itemDetails: itemDetails
    }

    return <Details {...detailsParams} />;
};

export default KYCDocumentDetailsPage;