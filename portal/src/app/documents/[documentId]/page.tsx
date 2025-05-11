"use client"

import {Details, DetailsProps} from "@/components/Details";
import {fetchDocument} from "@/services/DataService";
import {
    Alert, 
    Box, 
    ColumnLayout, 
    Container, 
    Header, 
    SpaceBetween, 
    Tabs
} from '@cloudscape-design/components';
import CodeView from "@cloudscape-design/code-view/code-view";
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

            {(documentId.extractedData || documentId.searchedData || documentId.verifiedData) && (
                <Container header={<Header variant="h2">Document Data</Header>}>
                    <Tabs
                        tabs={[
                            {
                                label: "Extracted Data",
                                id: "extractedData",
                                content: documentId.extractedData ? (
                                    <CodeView
                                        content={JSON.stringify(documentId.extractedData, null, 2)}
                                        language="json"
                                    />
                                ) : <Box>No extracted data available</Box>,
                                disabled: !documentId.extractedData
                            },
                            {
                                label: "Searched Data",
                                id: "searchedData",
                                content: documentId.searchedData ? (
                                    <CodeView
                                        content={JSON.stringify(documentId.searchedData, null, 2)}
                                        language="json"
                                    />
                                ) : <Box>No searched data available</Box>,
                                disabled: !documentId.searchedData
                            },
                            {
                                label: "Verified Data",
                                id: "verifiedData",
                                content: documentId.verifiedData ? (
                                    <CodeView
                                        content={JSON.stringify(documentId.verifiedData, null, 2)}
                                        language="json"
                                    />
                                ) : <Box>No verified data available</Box>,
                                disabled: !documentId.verifiedData
                            }
                        ]}
                    />
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