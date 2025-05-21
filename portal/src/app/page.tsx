"use client"

import React, {useEffect, useState} from 'react';
import {Box, Button, Cards, ColumnLayout, Header, SpaceBetween,} from '@cloudscape-design/components';
import {DashboardMetrics} from "@/types/interfaces";
import {fetchMetrics} from "@/services/DataService";


const Dashboard: React.FC = () => {
    const [metrics, setMetrics] = useState<DashboardMetrics>({
        documentValidations: 0,
        documentVerifications: 0,
        apiCalls: 0,
        faceLivenessCount: 0,
    });
    const [loading, setLoading] = useState(true);
    const handleRefresh = async () => {
        setLoading(true);
        try {
            const data = await fetchMetrics();
            setMetrics(data);
        } catch (error) {
            console.error('Failed to refresh metrics:', error);
        } finally {
            setLoading(false);
        }
    };
    useEffect(() => {
        const loadMetrics = async () => {
            try {
                const data = await fetchMetrics();
                setMetrics(data);
            } catch (error) {
                console.error('Error fetching metrics:', error);
            } finally {
                setLoading(false);
            }
        };

        loadMetrics();
    }, []);

    const metricCards = [
        {
            title: 'Document Validations',
            value: metrics.documentValidations,
            description: 'How many KYC documents have been check against uploaded copies',
        },
        {
            title: 'Document Verifications',
            value: metrics.documentVerifications,
            description: 'How many documents have been verified by the system (against Identity Services)',
        },
        {
            title: 'API Calls',
            value: metrics.apiCalls,
            description: 'Total number of API calls made to specified external services (Jubilee EBS and AWS), indicating system activity and integration usage',
        },
        {
            title: 'FaceLiveness Sessions',
            value: metrics.faceLivenessCount,
            description: 'Number of times a face liveness detection process has been initiated or completed',
        },
    ];

    return (
        <SpaceBetween size="l">
            <Header
                variant="h1"
                description="Overview of KYC system performance and usage"
                actions={
                    <Button
                        iconName="refresh"
                        loading={loading}
                        onClick={handleRefresh}
                    >
                        Refresh
                    </Button>
                }
            >
                eKYC Dashboard
            </Header>

            <Cards
                cardDefinition={{
                    header: item => (
                        <Header
                            variant="h2"
                        >
                            {item.title}
                        </Header>
                    ),
                    sections: [
                        {
                            id: "value",
                            header: "Count",
                            content: item => (
                                <Box variant="awsui-key-label" color="text-label">
                    <span style={{fontSize: '2rem', fontWeight: 'bold'}}>
                      {loading ? '—' : item.value.toLocaleString()}
                    </span>
                                </Box>
                            )
                        },
                        {
                            id: "description",
                            content: item => item.description
                        }
                    ]
                }}
                items={metricCards}
                loadingText="Loading metrics"
                loading={loading}
            />

            <ColumnLayout columns={2}>
                {/* You can add charts or other visualizations here */}
            </ColumnLayout>
        </SpaceBetween>
    );
};

export default Dashboard;

